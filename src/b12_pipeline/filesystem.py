"""Filesystem helpers."""

from __future__ import annotations

import csv
from pathlib import Path
import shutil


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    ensure_dir(path.parent)
    if fieldnames is None:
        collected: list[str] = []
        for row in rows:
            for key in row:
                if key not in collected:
                    collected.append(key)
        fieldnames = collected
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def copy_if_exists(source: Path | None, destination: Path) -> Path | None:
    if source is None or not source.exists():
        return None
    ensure_dir(destination.parent)
    shutil.copy2(source, destination)
    return destination
