"""Тесты JSON-хранилища."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from random_game.models import GameStatus
from random_game.storage import JsonStorage, StorageConfig


@pytest.mark.unit
class TestJsonStorage:
    def test_загрузка_seed_возвращает_все_игры_из_пула(self, storage: JsonStorage) -> None:
        games = storage.load_games()
        assert len(games) == 5
        assert {g.id for g in games} == {"a", "b", "c", "d", "e"}

    def test_сохранение_и_повторная_загрузка_сохраняет_статусы(
        self, storage: JsonStorage
    ) -> None:
        # Arrange
        games = storage.load_games()
        games[0] = games[0].with_status(GameStatus.COMPLETED, note="Топ")

        # Act
        storage.save_games(games)
        reloaded = storage.load_games()

        # Assert
        first = next(g for g in reloaded if g.id == games[0].id)
        assert first.status is GameStatus.COMPLETED
        assert first.note == "Топ"

    def test_seed_метаданные_сохраняются_при_слиянии_с_пользовательским_state(
        self, storage: JsonStorage
    ) -> None:
        # Arrange: пользователь меняет статус, но title должен прийти из seed
        games = storage.load_games()
        target = games[0]
        storage.save_games([target.with_status(GameStatus.IN_PROGRESS)])

        # Act
        reloaded = storage.load_games()

        # Assert
        same = next(g for g in reloaded if g.id == target.id)
        assert same.title == target.title
        assert same.description == target.description
        assert same.status is GameStatus.IN_PROGRESS

    def test_отсутствующий_seed_файл_возвращает_пустой_список(self, tmp_path: Path) -> None:
        config = StorageConfig(
            state_path=tmp_path / "state.json", seed_path=tmp_path / "missing.json"
        )
        storage = JsonStorage(config)
        assert storage.load_games() == []

    def test_повреждённый_state_не_ломает_загрузку(self, storage: JsonStorage) -> None:
        storage._config.state_path.write_text("{ not valid json", encoding="utf-8")
        games = storage.load_games()
        assert len(games) == 5

    def test_атомарная_запись_через_tmp_файл(
        self, storage: JsonStorage, tmp_path: Path
    ) -> None:
        games = storage.load_games()
        storage.save_games(games)
        assert storage._config.state_path.exists()
        # tmp файл не должен оставаться после успешного rename
        assert not storage._config.state_path.with_suffix(".json.tmp").exists()

    def test_state_использует_utf8_для_кириллицы(self, storage: JsonStorage) -> None:
        games = storage.load_games()
        games[0] = games[0].with_status(GameStatus.COMPLETED, note="Заметка на русском")
        storage.save_games(games)

        raw = storage._config.state_path.read_text(encoding="utf-8")
        payload = json.loads(raw)
        assert payload["games"][0]["note"] == "Заметка на русском"
