"""Aggregation of final reports for the diploma workflow."""

from __future__ import annotations

from pathlib import Path

from ..config import ProjectConfig
from ..filesystem import write_csv_rows, write_text
from ..reporting import safe_float
from .common import load_summary, mark_stage_end, mark_stage_start


def build_final_reports(config: ProjectConfig) -> tuple[Path, Path]:
    mark_stage_start(config, "finalize")
    methods = [
        ("screening", config.paths.screening / "summary.csv", "final_energy_eh"),
        ("refinement", config.paths.refinement / "summary.csv", "final_energy_eh"),
        ("frequencies", config.paths.frequencies / "summary.csv", "final_energy_eh"),
        ("spin_comparison", config.paths.spin_comparison / "summary.csv", "sp_energy_eh"),
        ("highlevel_sp", config.paths.highlevel_sp / "summary.csv", "final_energy_eh"),
        ("dlpno_check", config.paths.dlpno_check / "summary.csv", "final_energy_eh"),
        ("casscf_nevpt2", config.paths.casscf_nevpt2 / "summary.csv", "nevpt2_energy_eh"),
    ]

    table_rows: list[dict[str, object]] = []
    text_lines = [config.project_name, ""]

    for method_name, summary_path, energy_key in methods:
        rows = load_summary(summary_path)
        if not rows:
            text_lines.append(f"{method_name}: no data")
            continue
        ranked = sorted(
            [row for row in rows if safe_float(row.get(energy_key)) is not None],
            key=lambda row: safe_float(row.get(energy_key)) or 0.0,
        )
        if not ranked:
            text_lines.append(f"{method_name}: no converged energies")
            continue
        best = ranked[0]
        table_rows.append(
            {
                "method": method_name,
                "structure_name": best.get("structure_name", ""),
                "multiplicity": best.get("multiplicity", ""),
                "energy_key": energy_key,
                "energy_eh": best.get(energy_key, ""),
                "summary_file": str(summary_path),
            }
        )
        text_lines.append(
            f"{method_name}: {best.get('structure_name', '')} mult={best.get('multiplicity', '')} energy={best.get(energy_key, '')} Eh"
        )

    final_table = config.paths.summaries / "final_method_comparison.csv"
    final_text = config.paths.summaries / "final_conclusion.txt"
    write_csv_rows(final_table, table_rows)
    write_text(final_text, "\n".join(text_lines).strip() + "\n")
    mark_stage_end(config, "finalize", details=f"table={final_table.name} text={final_text.name}")
    return final_table, final_text
