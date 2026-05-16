"""Точка входа для PyInstaller.

Why: при сборке exe PyInstaller использует указанный скрипт как top-level,
и относительные импорты в random_game/__main__.py перестают работать.
Этот враппер вызывает main() через абсолютный импорт пакета.
"""

from __future__ import annotations

from random_game.__main__ import main


if __name__ == "__main__":
    main()
