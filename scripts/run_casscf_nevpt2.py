from __future__ import annotations

import sys

import _bootstrap  # noqa: F401
from b12_pipeline.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["casscf_nevpt2", *sys.argv[1:]]))
