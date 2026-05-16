"""Пути к ресурсам и пользовательским данным."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def app_data_dir() -> Path:
    """Каталог для пользовательских данных (state.json).

    Why: при сборке в exe рабочий каталог может быть read-only (Program Files),
    поэтому состояние пишем в %APPDATA%\\random-game (Windows) или
    ~/.local/share/random-game на других ОС.
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        path = Path(base) / "random-game"
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        path = Path(base) / "random-game"
    path.mkdir(parents=True, exist_ok=True)
    return path


def state_file() -> Path:
    """Файл с пользовательским состоянием (статусы игр)."""
    return app_data_dir() / "state.json"


def resource_path(relative: str) -> Path:
    """Путь к встроенному ресурсу.

    Why: PyInstaller распаковывает ресурсы во временную папку sys._MEIPASS;
    для dev-режима используем относительный путь от пакета.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass) / relative
    return Path(__file__).resolve().parent / relative


def seed_file() -> Path:
    """Встроенный начальный пул игр."""
    return resource_path("data/games_seed.json")
