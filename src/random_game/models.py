"""Доменные модели приложения."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class GameStatus(str, Enum):
    """Статус прохождения игры пользователем."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PLAYED_BEFORE = "played_before"
    DROPPED = "dropped"

    @property
    def label(self) -> str:
        """Человекочитаемое название статуса на русском."""
        return _STATUS_LABELS[self]

    @property
    def is_active_for_randomizer(self) -> bool:
        """Может ли игра быть выбрана рандомайзером.

        Why: уже пройденные/брошенные/ранее игранные игры исключаются из выдачи,
        чтобы каждый ролл предлагал что-то новое.
        """
        return self in {GameStatus.NOT_STARTED, GameStatus.IN_PROGRESS}


_STATUS_LABELS: dict[GameStatus, str] = {
    GameStatus.NOT_STARTED: "Не начата",
    GameStatus.IN_PROGRESS: "В процессе",
    GameStatus.COMPLETED: "Пройдена",
    GameStatus.PLAYED_BEFORE: "Уже играл",
    GameStatus.DROPPED: "Дропнул",
}


@dataclass
class Game:
    """Игра из пула.

    Хранит метаданные и пользовательский статус. id стабильный — это позволяет
    дополнять seed-пул новыми играми без потери прогресса.
    """

    id: str
    title: str
    year: int
    genre: str
    description: str
    estimated_hours: int
    difficulty: str = "Medium"
    platforms: list[str] = field(default_factory=list)
    min_specs_note: str = ""
    status: GameStatus = GameStatus.NOT_STARTED
    note: str = ""
    updated_at: str | None = None

    def with_status(self, status: GameStatus, note: str | None = None) -> Game:
        """Иммутабельное обновление статуса. Возвращает новый объект."""
        return Game(
            id=self.id,
            title=self.title,
            year=self.year,
            genre=self.genre,
            description=self.description,
            estimated_hours=self.estimated_hours,
            difficulty=self.difficulty,
            platforms=list(self.platforms),
            min_specs_note=self.min_specs_note,
            status=status,
            note=note if note is not None else self.note,
            updated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "year": self.year,
            "genre": self.genre,
            "description": self.description,
            "estimated_hours": self.estimated_hours,
            "difficulty": self.difficulty,
            "platforms": list(self.platforms),
            "min_specs_note": self.min_specs_note,
            "status": self.status.value,
            "note": self.note,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Game:
        raw_status = data.get("status", GameStatus.NOT_STARTED.value)
        try:
            status = GameStatus(raw_status)
        except ValueError:
            status = GameStatus.NOT_STARTED

        return cls(
            id=str(data.get("id") or _slugify(data["title"])),
            title=str(data["title"]),
            year=int(data.get("year", 0) or 0),
            genre=str(data.get("genre", "")),
            description=str(data.get("description", "")),
            estimated_hours=int(data.get("estimated_hours", 0) or 0),
            difficulty=str(data.get("difficulty", "Medium")),
            platforms=list(data.get("platforms") or []),
            min_specs_note=str(data.get("min_specs_note", "")),
            status=status,
            note=str(data.get("note", "")),
            updated_at=data.get("updated_at"),
        )


def _slugify(title: str) -> str:
    """Генерирует стабильный id из названия.

    Why: если seed-файл не содержит id, нужно сгенерировать предсказуемый
    идентификатор, чтобы при следующем обновлении пула пользовательский
    прогресс не потерялся.
    """
    base = "".join(c.lower() if c.isalnum() else "-" for c in title).strip("-")
    while "--" in base:
        base = base.replace("--", "-")
    return base or uuid.uuid4().hex[:8]


@dataclass(frozen=True)
class ProgressStats:
    """Статистика прохождения пула."""

    total: int
    completed: int
    in_progress: int
    played_before: int
    dropped: int
    not_started: int

    @property
    def available_for_roll(self) -> int:
        return self.not_started + self.in_progress

    @property
    def percent_done(self) -> float:
        """Процент пройденных игр от общего числа."""
        if self.total == 0:
            return 0.0
        return round(self.completed / self.total * 100, 1)

    @classmethod
    def from_games(cls, games: list[Game]) -> ProgressStats:
        counters: dict[GameStatus, int] = dict.fromkeys(GameStatus, 0)
        for game in games:
            counters[game.status] += 1
        return cls(
            total=len(games),
            completed=counters[GameStatus.COMPLETED],
            in_progress=counters[GameStatus.IN_PROGRESS],
            played_before=counters[GameStatus.PLAYED_BEFORE],
            dropped=counters[GameStatus.DROPPED],
            not_started=counters[GameStatus.NOT_STARTED],
        )
