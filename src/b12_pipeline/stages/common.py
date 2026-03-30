"""Shared stage utilities."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..config import ProjectConfig
from ..filesystem import read_csv_rows
from ..reporting import safe_float
from ..xyz import summarize_xyz


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def pipeline_event_log_path(config: ProjectConfig) -> Path:
    return config.paths.logs / "pipeline_events.log"


def append_pipeline_event(config: ProjectConfig, message: str) -> None:
    log_path = pipeline_event_log_path(config)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{_timestamp()}] {message.rstrip()}\n")


def stage_log_path(config: ProjectConfig, stage_name: str) -> Path:
    return config.paths.logs / f"{stage_name}.log"


def append_log(config: ProjectConfig, stage_name: str, message: str) -> None:
    log_path = stage_log_path(config, stage_name)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{_timestamp()}] {message.rstrip()}\n")


def bool_text(value: object) -> str:
    if value in (True, "True", "true", "1"):
        return "True"
    if value in (False, "False", "false", "0"):
        return "False"
    return ""


def sort_rows_by_energy(rows: list[dict[str, object]], energy_key: str) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda row: (safe_float(row.get(energy_key)) is None, safe_float(row.get(energy_key)) or 0.0),
    )


def load_summary(path: Path) -> list[dict[str, str]]:
    return read_csv_rows(path)


def candidate_metadata(xyz_path: Path) -> dict[str, object]:
    try:
        return summarize_xyz(xyz_path)
    except Exception:
        return {"atom_count": "", "formula": ""}


def mark_stage_start(config: ProjectConfig, stage_name: str) -> None:
    append_log(config, stage_name, f"START stage={stage_name}")
    append_pipeline_event(config, f"START stage={stage_name}")


def mark_stage_end(config: ProjectConfig, stage_name: str, details: str = "") -> None:
    suffix = f" {details}" if details else ""
    append_log(config, stage_name, f"END stage={stage_name}{suffix}")
    append_pipeline_event(config, f"END stage={stage_name}{suffix}")
