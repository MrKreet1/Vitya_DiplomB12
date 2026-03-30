"""Helpers for working with XYZ structures."""

from __future__ import annotations

from collections import Counter
from pathlib import Path


def read_xyz_frames(path: Path) -> list[list[str]]:
    lines = [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines()]
    frames: list[list[str]] = []
    cursor = 0
    while cursor < len(lines):
        if not lines[cursor].strip():
            cursor += 1
            continue
        atom_count = int(lines[cursor].strip())
        frame = lines[cursor : cursor + atom_count + 2]
        if len(frame) < atom_count + 2:
            raise ValueError(f"Incomplete XYZ frame in {path}")
        frames.append(frame)
        cursor += atom_count + 2
    return frames


def write_last_frame(source: Path, destination: Path) -> Path:
    frames = read_xyz_frames(source)
    destination.write_text("\n".join(frames[-1]).strip() + "\n", encoding="utf-8")
    return destination


def summarize_xyz(path: Path) -> dict[str, object]:
    frames = read_xyz_frames(path)
    if not frames:
        raise ValueError(f"No XYZ frames found in {path}")
    frame = frames[-1]
    atom_count = int(frame[0].strip())
    symbols = [line.split()[0] for line in frame[2:] if line.strip()]
    formula_counter = Counter(symbols)
    formula = "".join(
        f"{element}{formula_counter[element] if formula_counter[element] > 1 else ''}"
        for element in sorted(formula_counter)
    )
    return {
        "atom_count": atom_count,
        "formula": formula,
    }


def find_best_xyz_output(workdir: Path, basename: str) -> Path | None:
    preferred = [
        workdir / f"{basename}.xyz",
        workdir / f"{basename}_opt.xyz",
        workdir / f"{basename}_optimized.xyz",
        workdir / f"{basename}_trj.xyz",
    ]
    for candidate in preferred:
        if candidate.exists():
            return candidate
    xyz_files = sorted(workdir.glob("*.xyz"))
    return xyz_files[0] if xyz_files else None
