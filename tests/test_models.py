"""Тесты доменных моделей."""

from __future__ import annotations

import pytest

from random_game.models import Game, GameStatus, ProgressStats


@pytest.mark.unit
class TestGameStatus:
    def test_все_статусы_имеют_русский_label(self) -> None:
        for status in GameStatus:
            assert status.label
            assert isinstance(status.label, str)

    def test_только_not_started_и_in_progress_активны_для_рандомайзера(self) -> None:
        # Arrange
        active = {GameStatus.NOT_STARTED, GameStatus.IN_PROGRESS}
        inactive = set(GameStatus) - active

        # Act / Assert
        for status in active:
            assert status.is_active_for_randomizer is True
        for status in inactive:
            assert status.is_active_for_randomizer is False


@pytest.mark.unit
class TestGame:
    def test_with_status_возвращает_новый_объект(self, make_game) -> None:
        # Arrange
        game = make_game("g1", "Test")

        # Act
        updated = game.with_status(GameStatus.COMPLETED, note="Прошёл за 30 часов")

        # Assert
        assert updated is not game
        assert game.status is GameStatus.NOT_STARTED  # оригинал не изменился
        assert updated.status is GameStatus.COMPLETED
        assert updated.note == "Прошёл за 30 часов"
        assert updated.updated_at is not None

    def test_to_dict_и_from_dict_симметричны(self, make_game) -> None:
        # Arrange
        original = make_game("g1", "Test", status=GameStatus.IN_PROGRESS)

        # Act
        restored = Game.from_dict(original.to_dict())

        # Assert
        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.status is original.status

    def test_from_dict_обрабатывает_невалидный_статус_как_not_started(self) -> None:
        # Arrange
        data = {"title": "X", "status": "invalid_status"}

        # Act
        game = Game.from_dict(data)

        # Assert
        assert game.status is GameStatus.NOT_STARTED

    def test_from_dict_генерирует_id_из_названия_если_отсутствует(self) -> None:
        # Arrange
        data = {"title": "Half-Life 2"}

        # Act
        game = Game.from_dict(data)

        # Assert
        assert game.id == "half-life-2"


@pytest.mark.unit
class TestProgressStats:
    def test_подсчёт_статусов_из_списка_игр(self, sample_games) -> None:
        # Act
        stats = ProgressStats.from_games(sample_games)

        # Assert
        assert stats.total == 5
        assert stats.not_started == 1
        assert stats.in_progress == 1
        assert stats.completed == 1
        assert stats.played_before == 1
        assert stats.dropped == 1

    def test_available_for_roll_суммирует_активные_статусы(self, sample_games) -> None:
        stats = ProgressStats.from_games(sample_games)
        assert stats.available_for_roll == 2  # not_started + in_progress

    def test_percent_done_возвращает_ноль_для_пустого_списка(self) -> None:
        stats = ProgressStats.from_games([])
        assert stats.percent_done == 0.0

    def test_percent_done_корректно_рассчитывается(self, make_game) -> None:
        # Arrange
        games = [
            make_game("1", "A", status=GameStatus.COMPLETED),
            make_game("2", "B", status=GameStatus.COMPLETED),
            make_game("3", "C", status=GameStatus.NOT_STARTED),
            make_game("4", "D", status=GameStatus.NOT_STARTED),
        ]

        # Act
        stats = ProgressStats.from_games(games)

        # Assert
        assert stats.percent_done == 50.0
