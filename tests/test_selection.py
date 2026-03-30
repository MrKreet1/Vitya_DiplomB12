from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from b12_pipeline.selection import select_low_energy_rows


class SelectionTests(unittest.TestCase):
    def test_selects_rows_within_window_then_applies_top_n(self) -> None:
        rows = [
            {"name": "a", "energy": "-10.000000"},
            {"name": "b", "energy": "-9.999000"},
            {"name": "c", "energy": "-9.990000"}
        ]

        selected = select_low_energy_rows(
            rows,
            energy_key="energy",
            top_n=2,
            energy_window_kj_mol=5.0,
        )

        self.assertEqual([row["name"] for row in selected], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
