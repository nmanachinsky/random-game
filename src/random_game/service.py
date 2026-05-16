"""Сервисный слой, объединяющий хранилище и рандомайзер."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .models import Game, GameStatus, ProgressStats
from .randomizer import EmptyPoolError, GameRandomizer
from .storage import JsonStorage

logger = logging.getLogger(__name__)


@dataclass
class RollResult:
    """Результат броска рандомайзера."""

    game: Game
    pool_size: int
    fallback_used: bool


class GameLibraryService:
    """Фасад для UI-слоя.

    Загружает игры при старте, хранит их в памяти, делегирует сохранение
    при изменениях и выдаёт случайную игру.
    """

    def __init__(self, storage: JsonStorage, randomizer: GameRandomizer) -> None:
        self._storage = storage
        self._randomizer = randomizer
        self._games: list[Game] = []
        self._last_rolled_id: str | None = None

    def load(self) -> list[Game]:
        self._games = self._storage.load_games()
        logger.info("Загружено игр: %d", len(self._games))
        return list(self._games)

    @property
    def games(self) -> list[Game]:
        return list(self._games)

    def get(self, game_id: str) -> Game | None:
        return next((g for g in self._games if g.id == game_id), None)

    def stats(self) -> ProgressStats:
        return ProgressStats.from_games(self._games)

    def set_status(self, game_id: str, status: GameStatus, note: str | None = None) -> Game:
        index = next((i for i, g in enumerate(self._games) if g.id == game_id), None)
        if index is None:
            raise KeyError(f"Игра не найдена: {game_id}")
        updated = self._games[index].with_status(status, note)
        self._games[index] = updated
        self._storage.save_games(self._games)
        return updated

    def roll(self, *, avoid_repeat: bool = True) -> RollResult:
        exclude = [self._last_rolled_id] if avoid_repeat and self._last_rolled_id else []
        pool = [g for g in self._games if g.status.is_active_for_randomizer]
        if not pool:
            raise EmptyPoolError("Пул пустой: отметьте часть игр как 'Не начата' или 'В процессе'.")
        try:
            chosen = self._randomizer.pick(self._games, exclude_ids=exclude)
            fallback = chosen.id in exclude
        except EmptyPoolError:
            raise
        self._last_rolled_id = chosen.id
        return RollResult(game=chosen, pool_size=len(pool), fallback_used=fallback)

    def reset_progress(self) -> None:
        """Сбрасывает статусы всех игр на NOT_STARTED."""
        self._games = [g.with_status(GameStatus.NOT_STARTED, note="") for g in self._games]
        self._storage.save_games(self._games)
        self._last_rolled_id = None
