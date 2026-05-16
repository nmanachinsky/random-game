"""Тесты сервисного слоя."""

from __future__ import annotations

import random

import pytest

from random_game.models import GameStatus
from random_game.randomizer import EmptyPoolError, GameRandomizer
from random_game.service import GameLibraryService


@pytest.fixture
def service(storage) -> GameLibraryService:
    svc = GameLibraryService(storage, GameRandomizer(rng=random.Random(42)))
    svc.load()
    return svc


@pytest.mark.unit
class TestGameLibraryService:
    def test_load_возвращает_игры_из_хранилища(self, service: GameLibraryService) -> None:
        assert len(service.games) == 5

    def test_set_status_обновляет_игру_и_сохраняет(
        self, service: GameLibraryService, storage
    ) -> None:
        # Act
        updated = service.set_status("a", GameStatus.COMPLETED, note="Прошёл")

        # Assert
        assert updated.status is GameStatus.COMPLETED
        reloaded = storage.load_games()
        same = next(g for g in reloaded if g.id == "a")
        assert same.status is GameStatus.COMPLETED
        assert same.note == "Прошёл"

    def test_set_status_неизвестной_игры_бросает_KeyError(
        self, service: GameLibraryService
    ) -> None:
        with pytest.raises(KeyError):
            service.set_status("missing", GameStatus.COMPLETED)

    def test_roll_возвращает_активную_игру(self, service: GameLibraryService) -> None:
        result = service.roll()
        assert result.game.status.is_active_for_randomizer
        assert result.pool_size == 2

    def test_roll_не_повторяет_последний_результат_если_есть_альтернатива(
        self, service: GameLibraryService
    ) -> None:
        first = service.roll()
        second = service.roll()
        # 2 активные игры -> второй ролл должен отличаться
        assert first.game.id != second.game.id

    def test_roll_бросает_EmptyPoolError_когда_все_недоступны(
        self, service: GameLibraryService
    ) -> None:
        # Arrange
        service.set_status("a", GameStatus.COMPLETED)
        service.set_status("b", GameStatus.COMPLETED)

        # Act / Assert
        with pytest.raises(EmptyPoolError):
            service.roll()

    def test_stats_отражает_текущие_статусы(self, service: GameLibraryService) -> None:
        stats = service.stats()
        assert stats.total == 5
        assert stats.available_for_roll == 2

    def test_reset_progress_сбрасывает_все_статусы(
        self, service: GameLibraryService
    ) -> None:
        # Act
        service.reset_progress()

        # Assert
        assert all(g.status is GameStatus.NOT_STARTED for g in service.games)
        stats = service.stats()
        assert stats.not_started == 5
