"""Общие фикстуры pytest."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import pytest

from random_game.models import Game, GameStatus
from random_game.storage import JsonStorage, StorageConfig


def _make_game(
    game_id: str,
    title: str,
    status: GameStatus = GameStatus.NOT_STARTED,
) -> Game:
    return Game(
        id=game_id,
        title=title,
        year=2020,
        genre="Action",
        description=f"Описание {title}",
        estimated_hours=20,
        difficulty="Medium",
        platforms=["Steam"],
        min_specs_note="GTX 1060",
        status=status,
    )


@pytest.fixture
def make_game():
    return _make_game


@pytest.fixture
def sample_games() -> list[Game]:
    return [
        _make_game("a", "Alpha"),
        _make_game("b", "Beta", status=GameStatus.IN_PROGRESS),
        _make_game("c", "Gamma", status=GameStatus.COMPLETED),
        _make_game("d", "Delta", status=GameStatus.PLAYED_BEFORE),
        _make_game("e", "Epsilon", status=GameStatus.DROPPED),
    ]


@pytest.fixture
def storage(tmp_path: Path, sample_games: Iterable[Game]) -> JsonStorage:
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(
        json.dumps(
            {"games": [g.to_dict() for g in sample_games]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    config = StorageConfig(state_path=tmp_path / "state.json", seed_path=seed_path)
    return JsonStorage(config)
