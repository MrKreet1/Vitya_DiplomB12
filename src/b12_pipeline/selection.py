"""Candidate selection logic."""

from __future__ import annotations

from .reporting import safe_float


def select_low_energy_rows(
    rows: list[dict[str, object]],
    energy_key: str,
    top_n: int | None,
    energy_window_kj_mol: float | None,
) -> list[dict[str, object]]:
    valid = [row for row in rows if safe_float(row.get(energy_key)) is not None]
    valid.sort(key=lambda row: safe_float(row.get(energy_key)) or 0.0)
    if not valid:
        return []

    selected = valid
    reference = safe_float(valid[0].get(energy_key)) or 0.0
    if energy_window_kj_mol is not None:
        from .units import hartree_to_kjmol

        selected = [
            row
            for row in selected
            if hartree_to_kjmol((safe_float(row.get(energy_key)) or reference) - reference)
            <= energy_window_kj_mol
        ]
    if top_n is not None:
        selected = selected[:top_n]
    return selected
