"""Combined OPT + FREQ + SP spin-comparison workflow."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from opi.input.blocks import BlockFreq, BlockOutput
from opi.input.simple_keywords import (
    Approximation,
    AuxBasisSet,
    BasisSet,
    Dft,
    DispersionCorrection,
    Opt,
    Scf,
    Task,
)

from ..config import ProjectConfig
from ..constants import HIGHLEVEL_LEVEL, SCREENING_LEVEL
from ..filesystem import copy_if_exists
from ..opi_runner import OrcaJobSpec, run_job
from ..reporting import write_comparison_text, write_stage_summary
from ..resources import parallel_lines
from ..selection import select_low_energy_rows
from .common import append_log, bool_text, candidate_metadata, load_summary, mark_stage_end, mark_stage_start


def run_spin_comparison(config: ProjectConfig, dry_run: bool = False) -> Path:
    mark_stage_start(config, "spin_comparison")
    freq_summary = config.paths.frequencies / "summary.csv"
    minima = [row for row in load_summary(freq_summary) if row.get("minimum_confirmed") == "True"]
    seeds = select_low_energy_rows(
        minima,
        energy_key="final_energy_eh",
        top_n=config.selection.top_n,
        energy_window_kj_mol=config.selection.energy_window_kj_mol,
    )

    rows: list[dict[str, object]] = []
    by_structure: dict[str, list[dict[str, object]]] = defaultdict(list)
    summary_path = config.paths.spin_comparison / "summary.csv"

    for seed in seeds:
        structure_name = seed["structure_name"]
        seed_geometry = Path(seed["source_geometry"])
        for multiplicity in config.spin_comparison_multiplicities:
            root_dir = config.paths.spin_comparison / structure_name / f"mult_{multiplicity}"
            opt_dir = root_dir / "opt"
            freq_dir = root_dir / "freq"
            sp_dir = root_dir / "sp"

            opt_spec = OrcaJobSpec(
                stage_name="spin_opt",
                basename=f"{structure_name}_m{multiplicity}_spinopt",
                workdir=opt_dir,
                xyz_path=seed_geometry,
                charge=config.charge,
                multiplicity=multiplicity,
                simple_keywords=[Dft.R2SCAN_3C, Opt.TIGHTOPT, Scf.TIGHTSCF],
                blocks=[BlockOutput(jsonpropfile=True)],
                raw_input_lines=parallel_lines(config, "spin_opt"),
            )
            opt_result = run_job(config, opt_spec, dry_run=dry_run)
            opt_geometry = opt_result.final_xyz_path or seed_geometry
            saved_opt = (
                copy_if_exists(opt_result.final_xyz_path, opt_dir / f"{opt_spec.basename}_saved.xyz")
                if opt_result.final_xyz_path
                else None
            )

            freq_spec = OrcaJobSpec(
                stage_name="spin_freq",
                basename=f"{structure_name}_m{multiplicity}_spinfreq",
                workdir=freq_dir,
                xyz_path=opt_geometry,
                charge=config.charge,
                multiplicity=multiplicity,
                simple_keywords=[Dft.R2SCAN_3C, Task.FREQ, Scf.TIGHTSCF],
                blocks=[BlockOutput(jsonpropfile=True), BlockFreq(temp=298.15, pressure=1.0)],
                raw_input_lines=parallel_lines(config, "spin_freq"),
            )
            freq_result = run_job(config, freq_spec, dry_run=dry_run)

            sp_spec = OrcaJobSpec(
                stage_name="spin_sp",
                basename=f"{structure_name}_m{multiplicity}_spinsp",
                workdir=sp_dir,
                xyz_path=opt_geometry,
                charge=config.charge,
                multiplicity=multiplicity,
                simple_keywords=[
                    Dft.PBE0,
                    DispersionCorrection.D4,
                    BasisSet.DEF2_TZVPP,
                    AuxBasisSet.DEF2_J,
                    Approximation.RIJCOSX,
                    Task.SP,
                    Scf.TIGHTSCF,
                ],
                blocks=[BlockOutput(jsonpropfile=True)],
                raw_input_lines=parallel_lines(config, "spin_sp"),
            )
            sp_result = run_job(config, sp_spec, dry_run=dry_run)
            meta = candidate_metadata(opt_geometry)
            row = {
                "structure_name": structure_name,
                "multiplicity": multiplicity,
                "charge": config.charge,
                "seed_geometry": str(seed_geometry),
                "optimized_xyz": str(saved_opt or opt_geometry),
                "opt_level": SCREENING_LEVEL,
                "freq_level": SCREENING_LEVEL,
                "sp_level": HIGHLEVEL_LEVEL,
                "opt_normal_termination": bool_text(opt_result.parsed.get("normal_termination")),
                "opt_energy_eh": opt_result.parsed.get("final_energy_eh", ""),
                "freq_normal_termination": bool_text(freq_result.parsed.get("normal_termination")),
                "freq_energy_eh": freq_result.parsed.get("final_energy_eh", ""),
                "nimag": freq_result.parsed.get("nimag", ""),
                "minimum_confirmed": bool_text(freq_result.parsed.get("nimag") == 0 if freq_result.parsed else False),
                "sp_normal_termination": bool_text(sp_result.parsed.get("normal_termination")),
                "sp_energy_eh": sp_result.parsed.get("final_energy_eh", ""),
                "s2": sp_result.parsed.get("s2", ""),
                "opt_output_file": str(opt_result.output_path),
                "freq_output_file": str(freq_result.output_path),
                "sp_output_file": str(sp_result.output_path),
                "job_dir": str(root_dir),
                "mode": sp_result.mode,
                "atom_count": meta.get("atom_count", ""),
                "formula": meta.get("formula", ""),
            }
            rows.append(row)
            by_structure[structure_name].append(row)
            append_log(config, "spin_comparison", f"{structure_name} mult={multiplicity} spin route finished")

    write_stage_summary(summary_path, rows, energy_key="sp_energy_eh")
    write_stage_summary(
        config.paths.summaries / "05_spin_comparison_summary.csv",
        rows,
        energy_key="sp_energy_eh",
    )
    for structure_name, structure_rows in by_structure.items():
        write_comparison_text(
            config.paths.spin_comparison / structure_name / "comparison_summary.txt",
            structure_name=structure_name,
            rows=structure_rows,
            energy_key="sp_energy_eh",
            label="Spin comparison",
        )
    mark_stage_end(config, "spin_comparison", details=f"jobs={len(rows)} summary={summary_path.name}")
    return summary_path
