"""Refinement of low-energy candidates."""

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
from .common import append_log, bool_text, candidate_metadata, load_summary, mark_stage_end, mark_stage_start


def run_refinement(config: ProjectConfig, dry_run: bool = False) -> Path:
    mark_stage_start(config, "refinement")
    selection_path = config.paths.refinement / "selected_candidates.csv"
    candidates = load_summary(selection_path)
    rows: list[dict[str, object]] = []
    summary_path = config.paths.refinement / "summary.csv"

    for candidate in candidates:
        structure_name = candidate["structure_name"]
        multiplicity = int(candidate["multiplicity"])
        source_geometry = Path(candidate.get("optimized_xyz") or candidate["source_xyz"])
        meta = candidate_metadata(source_geometry)
        workdir = config.paths.refinement / structure_name / f"mult_{multiplicity}"
        basename = f"{structure_name}_m{multiplicity}_refine"
        spec = OrcaJobSpec(
            stage_name="refinement",
            basename=basename,
            workdir=workdir,
            xyz_path=source_geometry,
            charge=config.charge,
            multiplicity=multiplicity,
            simple_keywords=[Dft.R2SCAN_3C, Opt.TIGHTOPT, Scf.TIGHTSCF],
            blocks=[BlockOutput(jsonpropfile=True)],
            raw_input_lines=parallel_lines(config, "refinement"),
        )
        result = run_job(config, spec, dry_run=dry_run)
        refined_copy = (
            copy_if_exists(result.final_xyz_path, workdir / f"{basename}_saved.xyz")
            if result.final_xyz_path is not None
            else None
        )
        rows.append(
            {
                "structure_name": structure_name,
                "source_geometry": str(source_geometry),
                "multiplicity": multiplicity,
                "charge": config.charge,
                "level_of_theory": SCREENING_LEVEL,
                "task": "OPT",
                "normal_termination": bool_text(result.parsed.get("normal_termination")),
                "optimization_converged": bool_text(result.parsed.get("optimization_converged")),
                "final_energy_eh": result.parsed.get("final_energy_eh", ""),
                "refined_xyz": str(refined_copy) if refined_copy else "",
                "input_file": str(result.input_path),
                "output_file": str(result.output_path),
                "job_dir": str(workdir),
                "mode": result.mode,
                "atom_count": meta.get("atom_count", ""),
                "formula": meta.get("formula", ""),
            }
        )
        append_log(config, "refinement", f"{structure_name} mult={multiplicity} refined")

    write_stage_summary(summary_path, rows, energy_key="final_energy_eh")
    write_stage_summary(
        config.paths.summaries / "03_refinement_summary.csv",
        rows,
        energy_key="final_energy_eh",
    )
    mark_stage_end(config, "refinement", details=f"jobs={len(rows)} summary={summary_path.name}")
    return summary_path
