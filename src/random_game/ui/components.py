"""Переиспользуемые UI-компоненты."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from ..models import Game, GameStatus
from . import theme


STATUS_COLORS: dict[GameStatus, str] = {
    GameStatus.NOT_STARTED: theme.COLOR_MUTED,
    GameStatus.IN_PROGRESS: theme.COLOR_WARNING,
    GameStatus.COMPLETED: theme.COLOR_SUCCESS,
    GameStatus.PLAYED_BEFORE: "#5587E8",
    GameStatus.DROPPED: theme.COLOR_DANGER,
}


class StatusBadge(ctk.CTkLabel):
    """Цветной бейдж со статусом игры."""

    def __init__(self, master, status: GameStatus, **kwargs) -> None:
        super().__init__(
            master,
            text=f"  {status.label}  ",
            fg_color=STATUS_COLORS[status],
            corner_radius=10,
            text_color="white",
            font=theme.FONT_SMALL,
            **kwargs,
        )
        self._status = status

    def update_status(self, status: GameStatus) -> None:
        self._status = status
        self.configure(text=f"  {status.label}  ", fg_color=STATUS_COLORS[status])


class StatCard(ctk.CTkFrame):
    """Карточка одной метрики (число + подпись)."""

    def __init__(self, master, label: str, color: str = theme.COLOR_ACCENT, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=theme.COLOR_CARD_BG,
            border_width=1,
            border_color=theme.COLOR_CARD_BORDER,
            corner_radius=12,
            **kwargs,
        )
        self._value_label = ctk.CTkLabel(
            self,
            text="0",
            font=("Segoe UI", 24, "bold"),
            text_color=color,
        )
        self._value_label.pack(padx=16, pady=(12, 0))

        self._caption = ctk.CTkLabel(
            self,
            text=label,
            font=theme.FONT_SMALL,
            text_color=theme.COLOR_MUTED,
        )
        self._caption.pack(padx=16, pady=(2, 12))

    def set_value(self, value: int | str) -> None:
        self._value_label.configure(text=str(value))


class GameRow(ctk.CTkFrame):
    """Строка в списке игр с быстрой сменой статуса."""

    def __init__(
        self,
        master,
        game: Game,
        on_status_change: Callable[[str, GameStatus], None],
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=theme.COLOR_CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=theme.COLOR_CARD_BORDER,
            **kwargs,
        )
        self._game = game
        self._on_status_change = on_status_change

        title = ctk.CTkLabel(
            self,
            text=game.title,
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="w", padx=(14, 8), pady=(10, 0))

        meta_text = f"{game.year} • {game.genre} • ~{game.estimated_hours} ч"
        meta = ctk.CTkLabel(
            self,
            text=meta_text,
            font=theme.FONT_SMALL,
            text_color=theme.COLOR_MUTED,
            anchor="w",
        )
        meta.grid(row=1, column=0, sticky="w", padx=(14, 8), pady=(0, 10))

        self._badge = StatusBadge(self, game.status)
        self._badge.grid(row=0, column=1, rowspan=2, padx=8, pady=10)

        labels = [s.label for s in GameStatus]
        self._status_var = ctk.StringVar(value=game.status.label)
        selector = ctk.CTkOptionMenu(
            self,
            values=labels,
            variable=self._status_var,
            width=160,
            command=self._handle_change,
        )
        selector.grid(row=0, column=2, rowspan=2, padx=(8, 14), pady=10)

        self.grid_columnconfigure(0, weight=1)

    def _handle_change(self, label: str) -> None:
        status = next((s for s in GameStatus if s.label == label), None)
        if status is None:
            return
        self._badge.update_status(status)
        self._on_status_change(self._game.id, status)

    def update_game(self, game: Game) -> None:
        self._game = game
        self._status_var.set(game.status.label)
        self._badge.update_status(game.status)
