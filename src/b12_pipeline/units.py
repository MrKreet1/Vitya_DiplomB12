"""Unit conversion helpers."""

from __future__ import annotations

from .constants import HARTREE_TO_EV, HARTREE_TO_KJMOL


def hartree_to_kjmol(value: float) -> float:
    return value * HARTREE_TO_KJMOL


def hartree_to_ev(value: float) -> float:
    return value * HARTREE_TO_EV
