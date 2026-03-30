"""Command-line entry points for pipeline stages."""

from __future__ import annotations

import argparse

from .config import load_config
from .stages import (
    build_final_reports,
    run_casscf_nevpt2,
    run_dlpno_check,
    run_frequencies,
    run_highlevel_sp,
    run_refinement,
    run_screening,
    run_selection,
    run_spin_comparison,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="B12 ORCA/OPI pipeline")
    parser.add_argument(
        "stage",
        choices=[
            "screening",
            "selection",
            "refinement",
            "frequencies",
            "spin_comparison",
            "highlevel_sp",
            "dlpno_check",
            "casscf_nevpt2",
            "finalize",
            "full",
        ],
    )
    parser.add_argument(
        "--config",
        default="config/b12_config.example.json",
        help="Path to JSON configuration file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write ORCA inputs but do not execute ORCA.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config)

    if args.stage == "screening":
        run_screening(config, dry_run=args.dry_run)
    elif args.stage == "selection":
        run_selection(config)
    elif args.stage == "refinement":
        run_refinement(config, dry_run=args.dry_run)
    elif args.stage == "frequencies":
        run_frequencies(config, dry_run=args.dry_run)
    elif args.stage == "spin_comparison":
        run_spin_comparison(config, dry_run=args.dry_run)
    elif args.stage == "highlevel_sp":
        run_highlevel_sp(config, dry_run=args.dry_run)
    elif args.stage == "dlpno_check":
        run_dlpno_check(config, dry_run=args.dry_run)
    elif args.stage == "casscf_nevpt2":
        run_casscf_nevpt2(config, dry_run=args.dry_run)
    elif args.stage == "finalize":
        build_final_reports(config)
    elif args.stage == "full":
        run_screening(config, dry_run=args.dry_run)
        run_selection(config)
        run_refinement(config, dry_run=args.dry_run)
        run_frequencies(config, dry_run=args.dry_run)
        run_spin_comparison(config, dry_run=args.dry_run)
        run_highlevel_sp(config, dry_run=args.dry_run)
        run_dlpno_check(config, dry_run=args.dry_run)
        run_casscf_nevpt2(config, dry_run=args.dry_run)
        build_final_reports(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
