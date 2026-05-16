"""Хранилище состояния игр в JSON."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from .models import Game
from .paths import seed_file, state_file

logger = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    """Конфигурация хранилища. Позволяет переопределять пути в тестах."""

    state_path: Path
    seed_path: Path

    @classmethod
    def default(cls) -> StorageConfig:
        return cls(state_path=state_file(), seed_path=seed_file())


class JsonStorage:
    """Загрузка и сохранение пула игр в JSON.

    Стратегия слияния: seed-файл — источник истины по метаданным игр (название,
    описание, год и т.д.). Пользовательское состояние (статус, заметки) хранится
    в state.json и накладывается поверх seed. Это позволяет обновлять пул в
    новых релизах без потери прогресса.
    """

    def __init__(self, config: StorageConfig | None = None) -> None:
        self._config = config or StorageConfig.default()

    def load_games(self) -> list[Game]:
        seed_games = self._load_seed()
        user_state = self._load_user_state()
        return self._merge(seed_games, user_state)

    def save_games(self, games: list[Game]) -> None:
        payload = {
            "version": 1,
            "games": [
                {
                    "id": game.id,
                    "status": game.status.value,
                    "note": game.note,
                    "updated_at": game.updated_at,
                }
                for game in games
            ],
        }
        self._config.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._config.state_path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self._config.state_path)
        logger.debug("Состояние сохранено в %s", self._config.state_path)

    def _load_seed(self) -> list[Game]:
        if not self._config.seed_path.exists():
            logger.warning("Seed-файл не найден: %s", self._config.seed_path)
            return []
        raw = json.loads(self._config.seed_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "games" in raw:
            items = raw["games"]
        elif isinstance(raw, list):
            items = raw
        else:
            logger.error("Неподдерживаемый формат seed: %s", type(raw))
            return []
        games: list[Game] = []
        seen_ids: set[str] = set()
        for item in items:
            try:
                game = Game.from_dict(item)
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning("Пропущена некорректная запись seed: %s (%s)", item, exc)
                continue
            if game.id in seen_ids:
                logger.warning("Дубликат id в seed: %s", game.id)
                continue
            seen_ids.add(game.id)
            games.append(game)
        return games

    def _load_user_state(self) -> dict[str, dict]:
        if not self._config.state_path.exists():
            return {}
        try:
            raw = json.loads(self._config.state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            logger.error("Повреждённый state.json: %s", exc)
            return {}
        items = raw.get("games", []) if isinstance(raw, dict) else []
        return {entry["id"]: entry for entry in items if isinstance(entry, dict) and "id" in entry}

    @staticmethod
    def _merge(seed_games: list[Game], user_state: dict[str, dict]) -> list[Game]:
        result: list[Game] = []
        for game in seed_games:
            override = user_state.get(game.id)
            if override is None:
                result.append(game)
                continue
            merged = Game.from_dict({**game.to_dict(), **override, "title": game.title})
            result.append(merged)
        return result
