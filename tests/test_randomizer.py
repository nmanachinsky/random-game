"""Тесты рандомайзера."""

from __future__ import annotations

import random

import pytest

from random_game.models import GameStatus
from random_game.randomizer import EmptyPoolError, GameRandomizer


@pytest.mark.unit
class TestGameRandomizer:
    def test_выбирает_только_активные_игры(self, sample_games) -> None:
        # Arrange: только Alpha (not_started) и Beta (in_progress) активны
        randomizer = GameRandomizer(rng=random.Random(42))
        active_ids = {"a", "b"}

        # Act: 100 итераций должны попадать только в активные
        chosen_ids = {randomizer.pick(sample_games).id for _ in range(100)}

        # Assert
        assert chosen_ids.issubset(active_ids)

    def test_исключает_указанные_id(self, sample_games) -> None:
        # Arrange
        randomizer = GameRandomizer(rng=random.Random(1))

        # Act: с exclude_ids=['a'] должен выбирать только Beta
        ids = {randomizer.pick(sample_games, exclude_ids=["a"]).id for _ in range(20)}

        # Assert
        assert ids == {"b"}

    def test_fallback_когда_все_активные_в_exclude(self, sample_games) -> None:
        # Arrange: в exclude обе активные — рандомайзер должен fallback'нуться на них
        randomizer = GameRandomizer(rng=random.Random(0))

        # Act
        chosen = randomizer.pick(sample_games, exclude_ids=["a", "b"])

        # Assert
        assert chosen.id in {"a", "b"}

    def test_бросает_EmptyPoolError_когда_нет_активных_игр(self, make_game) -> None:
        # Arrange: все игры пройдены
        games = [
            make_game("1", "X", status=GameStatus.COMPLETED),
            make_game("2", "Y", status=GameStatus.DROPPED),
            make_game("3", "Z", status=GameStatus.PLAYED_BEFORE),
        ]
        randomizer = GameRandomizer(rng=random.Random(0))

        # Act / Assert
        with pytest.raises(EmptyPoolError):
            randomizer.pick(games)

    def test_детерминированный_выбор_с_фиксированным_seed(self, sample_games) -> None:
        # Arrange
        first = GameRandomizer(rng=random.Random(123)).pick(sample_games)
        second = GameRandomizer(rng=random.Random(123)).pick(sample_games)

        # Assert
        assert first.id == second.id
