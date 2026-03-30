from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from b12_pipeline.orca_parser import parse_orca_output


SAMPLE_OUTPUT = """\
VIBRATIONAL FREQUENCIES
  1:   -25.1234 cm**-1
  2:   100.0000 cm**-1
  3:   250.0000 cm**-1
NORMAL MODES
FINAL SINGLE POINT ENERGY      -294.123456789
<S**2>           2.015
T1 diagnostic    0.021
Zero point energy      0.123456
Total thermal correction      0.234567
Final Gibbs free energy      -293.987654
ORCA TERMINATED NORMALLY
"""


class OrcaParserTests(unittest.TestCase):
    def test_extracts_core_quantities(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sample.out"
            output_path.write_text(SAMPLE_OUTPUT, encoding="utf-8")
            parsed = parse_orca_output(output_path)

        self.assertTrue(parsed["normal_termination"])
        self.assertEqual(parsed["nimag"], 1)
        self.assertAlmostEqual(parsed["final_energy_eh"], -294.123456789)
        self.assertAlmostEqual(parsed["s2"], 2.015)
        self.assertAlmostEqual(parsed["t1_diagnostic"], 0.021)


if __name__ == "__main__":
    unittest.main()
