"""Helpers for per-stage ORCA resource configuration."""

from __future__ import annotations

from .config import ProjectConfig


def parallel_lines(config: ProjectConfig, stage_name: str) -> list[str]:
    preset = config.resources.resolve(stage_name)
    return [
        f"%maxcore {preset.maxcore_mb}",
        "%pal",
        f"  nprocs {preset.nprocs}",
        "end",
    ]
