"""Primary r2SCAN-3c screening stage."""

from __future__ import annotations

from pathlib import Path

from opi.input.blocks import BlockOutput
from opi.input.simple_keywords import Dft, Opt, Scf

from ..config import ProjectConfig
from ..constants import SCREENING_LEVEL
from ..filesystem import copy_if_exists
from ..opi_runner import OrcaJobSpec, run_job
from ..reporting import write_stage_summary
from ..resources import parallel_lines
from .common import append_log, bool_text, candidate_metadata, mark_stage_end, mark_stage_start


def run_screening(config: ProjectConfig, dry_run: bool = False) -> Path:
    config.ensure_directories()
    stage_name = "screening"
    mark_stage_start(config, stage_name)
    rows: list[dict[str, object]] = []
    xyz_files = sorted(config.paths.initial_structures.glob("*.xyz"))
    summary_path = config.paths.screening / "summary.csv"

    for xyz_path in xyz_files:
        meta = candidate_metadata(xyz_path)
        for multiplicity in config.screening_multiplicities:
            workdir = config.paths.screening / xyz_path.stem / f"mult_{multiplicity}"
            basename = f"{xyz_path.stem}_m{multiplicity}_screen"
            spec = OrcaJobSpec(
                stage_name=stage_name,
                basename=basename,
                workdir=workdir,
                xyz_path=xyz_path,
                charge=config.charge,
                multiplicity=multiplicity,
                simple_keywords=[Dft.R2SCAN_3C, Opt.OPT, Scf.TIGHTSCF],
                blocks=[BlockOutput(jsonpropfile=True)],
                raw_input_lines=parallel_lines(config, "screening"),
            )
            result = run_job(config, spec, dry_run=dry_run)
            optimized_copy = (
                copy_if_exists(result.final_xyz_path, workdir / f"{basename}_saved.xyz")
                if result.final_xyz_path is not None
                else None
            )
            row = {
                "structure_name": xyz_path.stem,
                "source_xyz": str(xyz_path),
                "multiplicity": multiplicity,
                "charge": config.charge,
                "level_of_theory": SCREENING_LEVEL,
                "task": "OPT",
                "normal_termination": bool_text(result.parsed.get("normal_termination")),
                "optimization_converged": bool_text(result.parsed.get("optimization_converged")),
                "final_energy_eh": result.parsed.get("final_energy_eh", ""),
                "optimized_xyz": str(optimized_copy) if optimized_copy else "",
                "input_file": str(result.input_path),
                "output_file": str(result.output_path),
                "job_dir": str(workdir),
                "mode": result.mode,
                "atom_count": meta.get("atom_count", ""),
                "formula": meta.get("formula", ""),
            }
            rows.append(row)
            append_log(
                config,
                stage_name,
                f"{xyz_path.name} mult={multiplicity} mode={result.mode} energy={row['final_energy_eh']}",
            )

    write_stage_summary(summary_path, rows, energy_key="final_energy_eh")
    write_stage_summary(
        config.paths.summaries / "02_screening_summary.csv",
        rows,
        energy_key="final_energy_eh",
    )
    mark_stage_end(config, stage_name, details=f"jobs={len(rows)} summary={summary_path.name}")
    return summary_path
