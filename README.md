# Random Game

Десктопное приложение для ПК-геймера, которое выбирает случайную игру из пула must-play и помогает отслеживать прогресс прохождения.

## Что внутри

- 136 игр в стартовом пуле (RPG, шутеры, стратегии, инди, хорроры, метроидвании, soulslike и т.д.)
- Все игры подобраны под среднее железо — ориентир Cyberpunk 2077 и Witcher 3 на средне-низких
- Фильтрация по статусу, поиск, статистика прохождения
- Корректная обработка случая «уже играл» — такие игры исключаются из рандома
- Чистый UI на CustomTkinter с тёмной темой

### Статусы игр

| Статус | Поведение в рандомайзере |
|--------|--------------------------|
| Не начата | участвует в выдаче |
| В процессе | участвует в выдаче |
| Пройдена | исключена |
| Уже играл | исключена |
| Дропнул | исключена |

## Требования

- Windows 10/11
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) для управления зависимостями

## Установка и запуск

```powershell
# Установить зависимости
uv sync

# Запустить приложение
uv run python -m random_game
```

Состояние сохраняется в `%APPDATA%\random-game\state.json` — переустановка приложения не сбрасывает прогресс.

## Сборка exe

```powershell
uv run python build.py
```

Результат: `dist/RandomGame.exe` — single-file, без консоли, ~30–60 МБ.

## Тесты

```powershell
uv run pytest --cov=src/random_game --cov-report=term-missing
```

Текущее покрытие: ~89%, 30 тестов.

## Структура проекта

```
random-game/
  build.py                  скрипт сборки exe
  random_game.spec          PyInstaller spec
  pyproject.toml
  src/random_game/
    __main__.py             entry point
    models.py               Game, GameStatus, ProgressStats
    storage.py              JsonStorage с миграцией seed → state
    randomizer.py           GameRandomizer
    service.py              GameLibraryService (фасад для UI)
    paths.py                пути к ресурсам и %APPDATA%
    data/games_seed.json    стартовый пул из 136 игр
    ui/
      main_window.py        главное окно
      components.py         StatusBadge, StatCard, GameRow
      theme.py              цвета, шрифты, размеры
  tests/                    pytest, 30 тестов, покрытие 89%
```

## Как пополнить пул

Просто добавь запись в `src/random_game/data/games_seed.json` — после следующего запуска она появится в списке. Пользовательский прогресс не потеряется: он хранится отдельно по `id` игры.

Минимальный формат записи:

```json
{
  "id": "stable-slug",
  "title": "Название",
  "year": 2024,
  "genre": "Action RPG",
  "description": "Краткое описание на русском",
  "estimated_hours": 30,
  "difficulty": "Medium",
  "platforms": ["Steam"],
  "min_specs_note": "GTX 1060 / 8 GB RAM"
}
```
