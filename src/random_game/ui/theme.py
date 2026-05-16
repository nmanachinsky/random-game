"""Темизация и константы UI."""

from __future__ import annotations

from typing import Final

import customtkinter as ctk

APP_TITLE: Final[str] = "Random Game — что сыграть сегодня"
WINDOW_MIN_SIZE: Final[tuple[int, int]] = (1100, 720)
WINDOW_DEFAULT_SIZE: Final[tuple[int, int]] = (1200, 780)

COLOR_ACCENT: Final[str] = "#7C5CFF"
COLOR_ACCENT_HOVER: Final[str] = "#9277FF"
COLOR_SUCCESS: Final[str] = "#3DB371"
COLOR_WARNING: Final[str] = "#E0A52B"
COLOR_DANGER: Final[str] = "#D94F4F"
COLOR_MUTED: Final[str] = "#7A7A85"
COLOR_CARD_BG: Final[str] = "#1F1F26"
COLOR_CARD_BORDER: Final[str] = "#2A2A33"

FONT_TITLE: Final[tuple[str, int, str]] = ("Segoe UI", 28, "bold")
FONT_SUBTITLE: Final[tuple[str, int, str]] = ("Segoe UI", 16, "normal")
FONT_BODY: Final[tuple[str, int, str]] = ("Segoe UI", 13, "normal")
FONT_SMALL: Final[tuple[str, int, str]] = ("Segoe UI", 11, "normal")
FONT_BUTTON: Final[tuple[str, int, str]] = ("Segoe UI", 14, "bold")


def setup_appearance() -> None:
    """Глобальные настройки темы. Вызывается один раз при старте."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
