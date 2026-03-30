"""Regex-based parsing of ORCA outputs."""

from __future__ import annotations

from pathlib import Path
import re


FINAL_SINGLE_POINT_RE = re.compile(r"FINAL SINGLE POINT ENERGY\s+(-?\d+\.\d+)")
S2_RE = re.compile(r"<S\*\*2>\s*[:=]?\s*(-?\d+\.\d+)|<S\^2>\s*[:=]?\s*(-?\d+\.\d+)")
T1_RE = re.compile(r"T1 diagnostic\s*[:=]?\s*(-?\d+\.\d+)", re.IGNORECASE)
ZERO_POINT_RE = re.compile(r"Zero point energy\s*\.*\s*(-?\d+\.\d+)", re.IGNORECASE)
THERMAL_CORR_RE = re.compile(r"Total thermal correction\s*\.*\s*(-?\d+\.\d+)", re.IGNORECASE)
GIBBS_RE = re.compile(r"Final Gibbs free energy\s*\.*\s*(-?\d+\.\d+)", re.IGNORECASE)
FREQ_LINE_RE = re.compile(r"^\s*\d+\s*:\s*(-?\d+\.\d+)\s*cm", re.IGNORECASE)
OCC_RE = re.compile(r"(-?\d+\.\d+)")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_orca_output(path: Path) -> dict[str, object]:
    text = _read_text(path)
    energies = [float(match) for match in FINAL_SINGLE_POINT_RE.findall(text)]
    s2_match = S2_RE.search(text)
    t1_match = T1_RE.search(text)
    zero_point_match = ZERO_POINT_RE.search(text)
    thermal_match = THERMAL_CORR_RE.search(text)
    gibbs_match = GIBBS_RE.search(text)
    frequencies = _parse_frequencies(text)
    occ_numbers = _parse_occupation_numbers(text)

    return {
        "normal_termination": "ORCA TERMINATED NORMALLY" in text,
        "optimization_converged": "THE OPTIMIZATION HAS CONVERGED" in text,
        "final_energy_eh": energies[-1] if energies else None,
        "s2": _first_group_float(s2_match),
        "t1_diagnostic": float(t1_match.group(1)) if t1_match else None,
        "zero_point_energy_eh": float(zero_point_match.group(1)) if zero_point_match else None,
        "thermal_correction_eh": float(thermal_match.group(1)) if thermal_match else None,
        "gibbs_free_energy_eh": float(gibbs_match.group(1)) if gibbs_match else None,
        "nimag": len([freq for freq in frequencies if freq < 0.0]),
        "min_frequency_cm-1": min(frequencies) if frequencies else None,
        "max_frequency_cm-1": max(frequencies) if frequencies else None,
        "occupation_numbers": occ_numbers,
    }


def _first_group_float(match: re.Match[str] | None) -> float | None:
    if not match:
        return None
    groups = [group for group in match.groups() if group is not None]
    return float(groups[0]) if groups else None


def _parse_frequencies(text: str) -> list[float]:
    frequencies: list[float] = []
    in_block = False
    for line in text.splitlines():
        if "VIBRATIONAL FREQUENCIES" in line.upper():
            in_block = True
            continue
        if in_block and "NORMAL MODES" in line.upper():
            break
        if not in_block:
            continue
        match = FREQ_LINE_RE.match(line)
        if match:
            frequencies.append(float(match.group(1)))
    return frequencies


def _parse_occupation_numbers(text: str) -> str:
    marker_indices = [
        idx for idx, line in enumerate(text.splitlines())
        if "OCCUPATION" in line.upper() and "NUMBER" in line.upper()
    ]
    if not marker_indices:
        return ""
    lines = text.splitlines()
    start = marker_indices[-1] + 1
    collected: list[str] = []
    for line in lines[start : start + 20]:
        numbers = OCC_RE.findall(line)
        if numbers:
            collected.extend(numbers)
    return " ".join(collected)
