"""Главное окно приложения."""

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from ..models import Game, GameStatus
from ..randomizer import EmptyPoolError
from ..service import GameLibraryService
from . import theme
from .components import GameRow, StatCard, StatusBadge

logger = logging.getLogger(__name__)

_FILTER_ALL = "Все"
_FILTERS: list[str] = [_FILTER_ALL] + [s.label for s in GameStatus]


class MainWindow(ctk.CTk):
    def __init__(self, service: GameLibraryService) -> None:
        super().__init__()
        self._service = service
        self._game_rows: dict[str, GameRow] = {}
        self._current_filter = _FILTER_ALL
        self._search_query = ""
        self._current_roll: Game | None = None

        self.title(theme.APP_TITLE)
        self.geometry(f"{theme.WINDOW_DEFAULT_SIZE[0]}x{theme.WINDOW_DEFAULT_SIZE[1]}")
        self.minsize(*theme.WINDOW_MIN_SIZE)

        self._build_layout()
        self._refresh_all()

    # ------------------------------------------------------------------ layout

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self._build_main_panel()
        self._build_side_panel()

    def _build_main_panel(self) -> None:
        panel = ctk.CTkFrame(self, fg_color="transparent")
        panel.grid(row=0, column=0, sticky="nsew", padx=(24, 12), pady=24)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)

        header = ctk.CTkLabel(panel, text="Что сыграть сегодня?", font=theme.FONT_TITLE)
        header.grid(row=0, column=0, sticky="w", pady=(0, 4))

        subtitle = ctk.CTkLabel(
            panel,
            text="Жми кнопку и пробуй что-то новое из пула must-play.",
            font=theme.FONT_SUBTITLE,
            text_color=theme.COLOR_MUTED,
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(0, 16))

        self._stats_row = ctk.CTkFrame(panel, fg_color="transparent")
        self._stats_row.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        for i in range(4):
            self._stats_row.grid_columnconfigure(i, weight=1, uniform="stat")

        self._stat_total = StatCard(self._stats_row, "Всего в пуле")
        self._stat_total.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self._stat_done = StatCard(self._stats_row, "Пройдено", color=theme.COLOR_SUCCESS)
        self._stat_done.grid(row=0, column=1, padx=8, sticky="ew")
        self._stat_progress = StatCard(self._stats_row, "В процессе", color=theme.COLOR_WARNING)
        self._stat_progress.grid(row=0, column=2, padx=8, sticky="ew")
        self._stat_available = StatCard(self._stats_row, "Доступно для ролла", color=theme.COLOR_ACCENT)
        self._stat_available.grid(row=0, column=3, padx=(8, 0), sticky="ew")

        self._roll_card = ctk.CTkFrame(
            panel,
            fg_color=theme.COLOR_CARD_BG,
            border_width=1,
            border_color=theme.COLOR_CARD_BORDER,
            corner_radius=14,
        )
        self._roll_card.grid(row=3, column=0, sticky="nsew")
        self._roll_card.grid_columnconfigure(0, weight=1)
        self._roll_card.grid_rowconfigure(1, weight=1)

        self._roll_title = ctk.CTkLabel(
            self._roll_card,
            text="Готов к броску?",
            font=("Segoe UI", 22, "bold"),
            anchor="w",
            justify="left",
            wraplength=600,
        )
        self._roll_title.grid(row=0, column=0, sticky="w", padx=24, pady=(20, 6))

        self._roll_meta = ctk.CTkLabel(
            self._roll_card,
            text="Нажми «Бросить кости», и я выберу игру из тех, что ты ещё не пробовал.",
            font=theme.FONT_SUBTITLE,
            text_color=theme.COLOR_MUTED,
            anchor="w",
            justify="left",
            wraplength=600,
        )
        self._roll_meta.grid(row=1, column=0, sticky="nw", padx=24, pady=(0, 6))

        self._roll_description = ctk.CTkLabel(
            self._roll_card,
            text="",
            font=theme.FONT_BODY,
            anchor="nw",
            justify="left",
            wraplength=600,
        )
        self._roll_description.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 12))

        self._roll_specs = ctk.CTkLabel(
            self._roll_card,
            text="",
            font=theme.FONT_SMALL,
            text_color=theme.COLOR_MUTED,
            anchor="w",
            justify="left",
            wraplength=600,
        )
        self._roll_specs.grid(row=3, column=0, sticky="w", padx=24, pady=(0, 14))

        self._roll_badge_container = ctk.CTkFrame(self._roll_card, fg_color="transparent")
        self._roll_badge_container.grid(row=4, column=0, sticky="w", padx=24, pady=(0, 14))
        self._roll_badge: StatusBadge | None = None

        actions = ctk.CTkFrame(self._roll_card, fg_color="transparent")
        actions.grid(row=5, column=0, sticky="ew", padx=24, pady=(0, 24))
        for i in range(5):
            actions.grid_columnconfigure(i, weight=1, uniform="act")

        self._roll_button = ctk.CTkButton(
            actions,
            text="Бросить кости",
            font=theme.FONT_BUTTON,
            fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_HOVER,
            height=48,
            command=self._roll,
        )
        self._roll_button.grid(row=0, column=0, columnspan=5, sticky="ew", pady=(0, 12))

        self._btn_already_played = ctk.CTkButton(
            actions,
            text="Уже играл",
            command=lambda: self._mark_current(GameStatus.PLAYED_BEFORE, reroll=True),
            fg_color="#3F4452",
            hover_color="#4C5263",
            state="disabled",
        )
        self._btn_already_played.grid(row=1, column=0, padx=(0, 6), sticky="ew")

        self._btn_in_progress = ctk.CTkButton(
            actions,
            text="Начал играть",
            command=lambda: self._mark_current(GameStatus.IN_PROGRESS),
            fg_color=theme.COLOR_WARNING,
            hover_color="#F0B83A",
            state="disabled",
        )
        self._btn_in_progress.grid(row=1, column=1, padx=6, sticky="ew")

        self._btn_completed = ctk.CTkButton(
            actions,
            text="Прошёл",
            command=lambda: self._mark_current(GameStatus.COMPLETED),
            fg_color=theme.COLOR_SUCCESS,
            hover_color="#4DC383",
            state="disabled",
        )
        self._btn_completed.grid(row=1, column=2, padx=6, sticky="ew")

        self._btn_dropped = ctk.CTkButton(
            actions,
            text="Дропнуть",
            command=lambda: self._mark_current(GameStatus.DROPPED, reroll=True),
            fg_color=theme.COLOR_DANGER,
            hover_color="#E26464",
            state="disabled",
        )
        self._btn_dropped.grid(row=1, column=3, padx=6, sticky="ew")

        self._btn_reroll = ctk.CTkButton(
            actions,
            text="Перебросить",
            command=self._roll,
            fg_color="#3F4452",
            hover_color="#4C5263",
            state="disabled",
        )
        self._btn_reroll.grid(row=1, column=4, padx=(6, 0), sticky="ew")

    def _build_side_panel(self) -> None:
        panel = ctk.CTkFrame(self, fg_color="transparent")
        panel.grid(row=0, column=1, sticky="nsew", padx=(12, 24), pady=24)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)

        header = ctk.CTkLabel(panel, text="Пул игр", font=("Segoe UI", 20, "bold"))
        header.grid(row=0, column=0, sticky="w", pady=(0, 8))

        controls = ctk.CTkFrame(panel, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        controls.grid_columnconfigure(0, weight=1)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search_changed)
        search = ctk.CTkEntry(
            controls,
            placeholder_text="Поиск по названию или жанру…",
            textvariable=self._search_var,
        )
        search.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self._filter_menu = ctk.CTkOptionMenu(
            controls,
            values=_FILTERS,
            command=self._on_filter_change,
            width=160,
        )
        self._filter_menu.grid(row=0, column=1)

        self._count_label = ctk.CTkLabel(
            panel,
            text="",
            font=theme.FONT_SMALL,
            text_color=theme.COLOR_MUTED,
            anchor="w",
        )
        self._count_label.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        self._scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self._scroll.grid(row=3, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

        footer = ctk.CTkFrame(panel, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        reset = ctk.CTkButton(
            footer,
            text="Сбросить прогресс",
            command=self._confirm_reset,
            fg_color="transparent",
            hover_color="#2A2A33",
            text_color=theme.COLOR_DANGER,
            border_width=1,
            border_color=theme.COLOR_DANGER,
        )
        reset.pack(side="right")

    # ----------------------------------------------------------------- actions

    def _roll(self) -> None:
        try:
            result = self._service.roll()
        except EmptyPoolError as exc:
            self._show_empty_pool(str(exc))
            return
        self._render_roll(result.game)

    def _mark_current(self, status: GameStatus, *, reroll: bool = False) -> None:
        if self._current_roll is None:
            return
        game_id = self._current_roll.id
        self._service.set_status(game_id, status)
        self._refresh_all(preserve_roll=not reroll)
        if reroll:
            self._roll()

    def _confirm_reset(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Сброс прогресса")
        dialog.geometry("380x160")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        ctk.CTkLabel(
            dialog,
            text="Сбросить статусы всех игр?\nЭто действие нельзя отменить.",
            font=theme.FONT_BODY,
            justify="center",
        ).pack(pady=(24, 16), padx=20)

        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(pady=(0, 20))

        def confirm() -> None:
            self._service.reset_progress()
            self._current_roll = None
            self._refresh_all()
            dialog.destroy()

        ctk.CTkButton(buttons, text="Отмена", command=dialog.destroy, fg_color="#3F4452").pack(
            side="left", padx=8
        )
        ctk.CTkButton(
            buttons,
            text="Сбросить",
            command=confirm,
            fg_color=theme.COLOR_DANGER,
            hover_color="#E26464",
        ).pack(side="left", padx=8)

    def _on_filter_change(self, value: str) -> None:
        self._current_filter = value
        self._render_game_list()

    def _on_search_changed(self, *_: object) -> None:
        self._search_query = self._search_var.get().strip().lower()
        self._render_game_list()

    def _handle_row_status_change(self, game_id: str, status: GameStatus) -> None:
        self._service.set_status(game_id, status)
        self._refresh_all(preserve_roll=True)

    # ----------------------------------------------------------------- render

    def _refresh_all(self, *, preserve_roll: bool = False) -> None:
        self._render_stats()
        self._render_game_list()
        if preserve_roll and self._current_roll is not None:
            fresh = self._service.get(self._current_roll.id)
            if fresh is not None:
                self._render_roll(fresh, animate=False)

    def _render_stats(self) -> None:
        stats = self._service.stats()
        self._stat_total.set_value(stats.total)
        self._stat_done.set_value(f"{stats.completed}  ({stats.percent_done}%)")
        self._stat_progress.set_value(stats.in_progress)
        self._stat_available.set_value(stats.available_for_roll)

    def _render_game_list(self) -> None:
        for row in self._game_rows.values():
            row.destroy()
        self._game_rows.clear()

        filtered = self._filtered_games()
        self._count_label.configure(text=f"Показано: {len(filtered)} из {len(self._service.games)}")

        for index, game in enumerate(filtered):
            row = GameRow(self._scroll, game, on_status_change=self._handle_row_status_change)
            row.grid(row=index, column=0, sticky="ew", pady=4)
            self._game_rows[game.id] = row

    def _filtered_games(self) -> list[Game]:
        result: list[Game] = []
        for game in self._service.games:
            if self._current_filter != _FILTER_ALL and game.status.label != self._current_filter:
                continue
            if self._search_query:
                haystack = f"{game.title} {game.genre}".lower()
                if self._search_query not in haystack:
                    continue
            result.append(game)
        result.sort(key=lambda g: g.title.lower())
        return result

    def _render_roll(self, game: Game, *, animate: bool = True) -> None:
        self._current_roll = game
        self._roll_title.configure(text=game.title)
        meta_bits = [str(game.year), game.genre, f"~{game.estimated_hours} ч", game.difficulty]
        platforms = ", ".join(game.platforms) if game.platforms else ""
        meta_text = " • ".join([b for b in meta_bits if b])
        if platforms:
            meta_text += f"\n{platforms}"
        self._roll_meta.configure(text=meta_text)
        self._roll_description.configure(text=game.description or "")
        self._roll_specs.configure(text=game.min_specs_note or "")

        if self._roll_badge is not None:
            self._roll_badge.destroy()
        self._roll_badge = StatusBadge(self._roll_badge_container, game.status)
        self._roll_badge.pack(side="left")

        for button in (
            self._btn_already_played,
            self._btn_in_progress,
            self._btn_completed,
            self._btn_dropped,
            self._btn_reroll,
        ):
            button.configure(state="normal")

        if animate:
            self._flash(self._roll_card)

    def _show_empty_pool(self, message: str) -> None:
        self._current_roll = None
        self._roll_title.configure(text="Пул пуст")
        self._roll_meta.configure(text=message)
        self._roll_description.configure(text="")
        self._roll_specs.configure(text="")
        if self._roll_badge is not None:
            self._roll_badge.destroy()
            self._roll_badge = None
        for button in (
            self._btn_already_played,
            self._btn_in_progress,
            self._btn_completed,
            self._btn_dropped,
            self._btn_reroll,
        ):
            button.configure(state="disabled")

    def _flash(self, widget: ctk.CTkFrame) -> None:
        """Лёгкая визуальная индикация смены содержимого карточки."""
        original = widget.cget("border_color")
        widget.configure(border_color=theme.COLOR_ACCENT)
        self.after(280, lambda: widget.configure(border_color=original))


def run_app(service_factory: Callable[[], GameLibraryService]) -> None:
    theme.setup_appearance()
    service = service_factory()
    service.load()
    window = MainWindow(service)
    window.mainloop()
