"""Точка входа приложения."""

from __future__ import annotations

import logging
import random
import sys

from .randomizer import GameRandomizer
from .service import GameLibraryService
from .storage import JsonStorage
from .ui.main_window import run_app


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        stream=sys.stderr,
    )


def _build_service() -> GameLibraryService:
    storage = JsonStorage()
    randomizer = GameRandomizer(rng=random.Random())
    return GameLibraryService(storage, randomizer)


def main() -> None:
    _configure_logging()
    run_app(_build_service)


if __name__ == "__main__":
    main()
