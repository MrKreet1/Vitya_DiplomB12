"""Summary and text-report helpers."""

from __future__ import annotations

from pathlib import Path

from .filesystem import write_csv_rows, write_text
from .units import hartree_to_ev, hartree_to_kjmol


def safe_float(value: object) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def annotate_relative_energies(
    rows: list[dict[str, object]],
    energy_key: str,
    target_key: str = "relative_energy_kj_mol",
) -> None:
    energies = [safe_float(row.get(energy_key)) for row in rows]
    valid = [value for value in energies if value is not None]
    if not valid:
        return
    reference = min(valid)
    for row in rows:
        energy = safe_float(row.get(energy_key))
        if energy is None:
            row[target_key] = ""
        else:
            row[target_key] = f"{hartree_to_kjmol(energy - reference):.4f}"


def write_stage_summary(summary_path: Path, rows: list[dict[str, object]], energy_key: str) -> None:
    annotate_relative_energies(rows, energy_key=energy_key)
    rows.sort(key=lambda row: (safe_float(row.get(energy_key)) is None, safe_float(row.get(energy_key)) or 0.0))
    write_csv_rows(summary_path, rows)


def render_comparison_text(
    structure_name: str,
    rows: list[dict[str, object]],
    energy_key: str,
    label: str,
) -> str:
    ranked = [
        row for row in rows
        if safe_float(row.get(energy_key)) is not None
    ]
    ranked.sort(key=lambda row: safe_float(row.get(energy_key)) or 0.0)
    lines = [f"{label}: {structure_name}", ""]
    if not ranked:
        lines.append("No converged energies were available.")
        return "\n".join(lines) + "\n"

    ref_energy = safe_float(ranked[0][energy_key]) or 0.0
    ref_mult = ranked[0].get("multiplicity", "?")
    lines.append(f"Lowest state: multiplicity {ref_mult}")
    lines.append("")
    for row in ranked:
        energy = safe_float(row.get(energy_key)) or 0.0
        delta = energy - ref_energy
        lines.append(
            "mult={mult}  E={energy:.10f} Eh  dE={delta_eh:.10f} Eh  "
            "dE={delta_kj:.4f} kJ/mol  dE={delta_ev:.6f} eV".format(
                mult=row.get("multiplicity", "?"),
                energy=energy,
                delta_eh=delta,
                delta_kj=hartree_to_kjmol(delta),
                delta_ev=hartree_to_ev(delta),
            )
        )
    return "\n".join(lines) + "\n"


def write_comparison_text(
    path: Path,
    structure_name: str,
    rows: list[dict[str, object]],
    energy_key: str,
    label: str,
) -> None:
    write_text(path, render_comparison_text(structure_name, rows, energy_key, label))
