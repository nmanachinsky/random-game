"""Скрипт сборки exe через PyInstaller.

Запуск:
    uv run python build.py

Результат: dist/RandomGame.exe (single-file, без консоли).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC_PATH = ROOT / "random_game.spec"
DIST_PATH = ROOT / "dist"
BUILD_PATH = ROOT / "build"


def _purge(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def main() -> int:
    _purge(DIST_PATH)
    _purge(BUILD_PATH)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(SPEC_PATH),
        "--noconfirm",
        "--clean",
    ]
    print("$", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT, env=os.environ.copy())
    if result.returncode != 0:
        print("Build failed.", file=sys.stderr)
        return result.returncode

    exe = DIST_PATH / "RandomGame.exe"
    if exe.exists():
        print(f"\nDone: {exe} ({exe.stat().st_size / (1024 * 1024):.1f} MB)")
    else:
        print("Build succeeded but dist/RandomGame.exe not found.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
