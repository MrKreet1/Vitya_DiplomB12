"""CASSCF / SC-NEVPT2 control workflow."""

from __future__ import annotations

from pathlib import Path

from opi.input.blocks import BlockCasscf, BlockOutput, BlockScf
from opi.input.simple_keywords import BasisSet, Scf, Task, Wft

from ..config import ProjectConfig
from ..constants import CASSCF_LEVEL, NEVPT2_LEVEL
from ..opi_runner import OrcaJobSpec, run_job
from ..reporting import safe_float, write_stage_summary
from ..resources import parallel_lines
from ..selection import select_low_energy_rows
from .common import append_log, bool_text, candidate_metadata, load_summary, mark_stage_end, mark_stage_start


def run_casscf_nevpt2(config: ProjectConfig, dry_run: bool = False) -> Path:
    mark_stage_start(config, "casscf_nevpt2")
    highlevel_rows = load_summary(config.paths.highlevel_sp / "summary.csv")
    spin_rows = load_summary(config.paths.spin_comparison / "summary.csv")
    dlpno_rows = load_summary(config.paths.dlpno_check / "summary.csv")

    selected = _select_multireference_candidates(config, highlevel_rows, spin_rows, dlpno_rows)
    rows: list[dict[str, object]] = []
    summary_path = config.paths.casscf_nevpt2 / "summary.csv"

    for candidate in selected:
        structure_name = candidate["structure_name"]
        multiplicity = int(candidate["multiplicity"])
        geometry = Path(candidate["geometry"])
        meta = candidate_metadata(geometry)
        root_dir = config.paths.casscf_nevpt2 / structure_name / f"mult_{multiplicity}"

        casscf_spec = OrcaJobSpec(
            stage_name="casscf",
            basename=f"{structure_name}_m{multiplicity}_casscf",
            workdir=root_dir / "casscf",
            xyz_path=geometry,
            charge=config.charge,
            multiplicity=multiplicity,
            simple_keywords=[BasisSet.DEF2_TZVPP, Task.SP, Scf.TIGHTSCF],
            blocks=[
                BlockOutput(jsonpropfile=True),
                BlockCasscf(
                    nel=config.casscf.nel,
                    norb=config.casscf.norb,
                    mult=multiplicity,
                    nroots=config.casscf.nroots,
                    weights=config.casscf.weights,
                    printlevel=config.casscf.print_level,
                    maxiter=config.casscf.maxiter,
                ),
            ],
            raw_input_lines=parallel_lines(config, "casscf"),
        )
        casscf_result = run_job(config, casscf_spec, dry_run=dry_run)

        nevpt2_gbw = casscf_result.spec.workdir / f"{casscf_spec.basename}.gbw"
        nevpt2_blocks = [
            BlockOutput(jsonpropfile=True),
            BlockCasscf(
                nel=config.casscf.nel,
                norb=config.casscf.norb,
                mult=multiplicity,
                nroots=config.casscf.nroots,
                weights=config.casscf.weights,
                printlevel=config.casscf.print_level,
                maxiter=config.casscf.maxiter,
                nevpt2=1,
                ptmethod="sc_nevpt2",
            ),
        ]
        if nevpt2_gbw.exists():
            nevpt2_blocks.append(BlockScf(moinp=nevpt2_gbw))

        nevpt2_spec = OrcaJobSpec(
            stage_name="nevpt2",
            basename=f"{structure_name}_m{multiplicity}_nevpt2",
            workdir=root_dir / "nevpt2",
            xyz_path=geometry,
            charge=config.charge,
            multiplicity=multiplicity,
            simple_keywords=[Wft.SC_NEVPT2, BasisSet.DEF2_TZVPP, Task.SP, Scf.TIGHTSCF],
            blocks=nevpt2_blocks,
            raw_input_lines=parallel_lines(config, "nevpt2"),
        )
        nevpt2_result = run_job(config, nevpt2_spec, dry_run=dry_run)

        rows.append(
            {
                "structure_name": structure_name,
                "multiplicity": multiplicity,
                "charge": config.charge,
                "geometry": str(geometry),
                "casscf_level": CASSCF_LEVEL,
                "casscf_energy_eh": casscf_result.parsed.get("final_energy_eh", ""),
                "casscf_normal_termination": bool_text(casscf_result.parsed.get("normal_termination")),
                "occupation_numbers": casscf_result.parsed.get("occupation_numbers", ""),
                "nevpt2_level": NEVPT2_LEVEL,
                "nevpt2_energy_eh": nevpt2_result.parsed.get("final_energy_eh", ""),
                "nevpt2_normal_termination": bool_text(nevpt2_result.parsed.get("normal_termination")),
                "casscf_output_file": str(casscf_result.output_path),
                "nevpt2_output_file": str(nevpt2_result.output_path),
                "job_dir": str(root_dir),
                "mode": nevpt2_result.mode,
                "atom_count": meta.get("atom_count", ""),
                "formula": meta.get("formula", ""),
            }
        )
        append_log(config, "casscf_nevpt2", f"{structure_name} mult={multiplicity} CASSCF/NEVPT2 finished")

    write_stage_summary(summary_path, rows, energy_key="nevpt2_energy_eh")
    write_stage_summary(
        config.paths.summaries / "08_casscf_nevpt2_summary.csv",
        rows,
        energy_key="nevpt2_energy_eh",
    )
    mark_stage_end(config, "casscf_nevpt2", details=f"jobs={len(rows)} summary={summary_path.name}")
    return summary_path


def _select_multireference_candidates(
    config: ProjectConfig,
    highlevel_rows: list[dict[str, str]],
    spin_rows: list[dict[str, str]],
    dlpno_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []

    ranked_highlevel = select_low_energy_rows(
        highlevel_rows,
        energy_key="final_energy_eh",
        top_n=config.selection.multiref_candidate_count,
        energy_window_kj_mol=config.multireference.spin_gap_threshold_kj_mol,
    )
    for row in ranked_highlevel:
        selected.append(
            {
                "structure_name": row["structure_name"],
                "multiplicity": int(row["multiplicity"]),
                "geometry": row["geometry"],
                "reason": "close_in_highlevel_window",
            }
        )

    for row in dlpno_rows:
        t1 = safe_float(row.get("t1_diagnostic"))
        if t1 is not None and t1 >= config.multireference.t1_threshold:
            selected.append(
                {
                    "structure_name": row["structure_name"],
                    "multiplicity": int(row["multiplicity"]),
                    "geometry": row["geometry"],
                    "reason": "t1_threshold",
                }
            )

    for row in spin_rows:
        s2 = safe_float(row.get("s2"))
        multiplicity = int(row["multiplicity"])
        spin = (multiplicity - 1) / 2
        expected_s2 = spin * (spin + 1)
        if s2 is not None and abs(s2 - expected_s2) >= config.multireference.spin_contamination_tolerance:
            selected.append(
                {
                    "structure_name": row["structure_name"],
                    "multiplicity": multiplicity,
                    "geometry": row["optimized_xyz"],
                    "reason": "spin_contamination",
                }
            )

    deduplicated: dict[tuple[str, int, str], dict[str, object]] = {}
    for row in selected:
        if config.casscf.mults and int(row["multiplicity"]) not in config.casscf.mults:
            continue
        key = (str(row["structure_name"]), int(row["multiplicity"]), str(row["geometry"]))
        deduplicated[key] = row
    return list(deduplicated.values())[: config.selection.multiref_candidate_count]
