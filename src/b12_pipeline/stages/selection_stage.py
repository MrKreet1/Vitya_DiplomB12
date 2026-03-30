"""Candidate selection after screening."""

from __future__ import annotations

from pathlib import Path

from ..config import ProjectConfig
from ..filesystem import write_csv_rows
from ..selection import select_low_energy_rows
from .common import append_log, load_summary, mark_stage_end, mark_stage_start


def run_selection(config: ProjectConfig) -> Path:
    mark_stage_start(config, "selection")
    screening_summary = config.paths.screening / "summary.csv"
    rows = [
        row for row in load_summary(screening_summary)
        if row.get("normal_termination") == "True"
    ]
    selected = select_low_energy_rows(
        rows,
        energy_key="final_energy_eh",
        top_n=config.selection.top_n,
        energy_window_kj_mol=config.selection.energy_window_kj_mol,
    )

    output_rows: list[dict[str, object]] = []
    for row in selected:
        out_row = dict(row)
        out_row["selection_reason"] = (
            f"top_n={config.selection.top_n}, energy_window_kj_mol={config.selection.energy_window_kj_mol}"
        )
        output_rows.append(out_row)

    selection_path = config.paths.refinement / "selected_candidates.csv"
    write_csv_rows(selection_path, output_rows)
    write_csv_rows(config.paths.summaries / "03_selected_candidates.csv", output_rows)
    append_log(config, "selection", f"Selected {len(output_rows)} candidates from {screening_summary}")
    mark_stage_end(config, "selection", details=f"selected={len(output_rows)}")
    return selection_path
