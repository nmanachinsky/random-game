"""Логика выбора случайной игры из пула."""

from __future__ import annotations

import random
from collections.abc import Iterable

from .models import Game


class EmptyPoolError(RuntimeError):
    """Нет игр, доступных для выбора."""


class GameRandomizer:
    """Возвращает случайную игру из пула с учётом фильтров.

    Игры со статусом completed/played_before/dropped автоматически исключаются.
    Опциональный exclude_ids позволяет реролл-логике не повторять последний результат.
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    def pick(
        self,
        games: Iterable[Game],
        *,
        exclude_ids: Iterable[str] = (),
    ) -> Game:
        excluded = set(exclude_ids)
        candidates = [
            game
            for game in games
            if game.status.is_active_for_randomizer and game.id not in excluded
        ]
        if not candidates:
            fallback = [game for game in games if game.status.is_active_for_randomizer]
            if not fallback:
                raise EmptyPoolError("Все игры из пула отмечены как пройденные или пропущенные.")
            candidates = fallback
        return self._rng.choice(candidates)
