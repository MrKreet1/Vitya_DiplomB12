"""High-level single-point calculations."""

from __future__ import annotations

from pathlib import Path

from opi.input.blocks import BlockOutput
from opi.input.simple_keywords import (
    Approximation,
    AuxBasisSet,
    BasisSet,
    Dft,
    DispersionCorrection,
    Scf,
    Task,
)

from ..config import ProjectConfig
from ..constants import HIGHLEVEL_LEVEL
from ..opi_runner import OrcaJobSpec, run_job
from ..reporting import write_stage_summary
from ..resources import parallel_lines
from .common import append_log, bool_text, candidate_metadata, load_summary, mark_stage_end, mark_stage_start


def run_highlevel_sp(config: ProjectConfig, dry_run: bool = False) -> Path:
    mark_stage_start(config, "highlevel_sp")
    freq_summary = config.paths.frequencies / "summary.csv"
    candidates = [
        row for row in load_summary(freq_summary) if row.get("minimum_confirmed") == "True"
    ]
    rows: list[dict[str, object]] = []
    summary_path = config.paths.highlevel_sp / "summary.csv"

    for candidate in candidates:
        structure_name = candidate["structure_name"]
        multiplicity = int(candidate["multiplicity"])
        geometry = Path(candidate["source_geometry"])
        meta = candidate_metadata(geometry)
        workdir = config.paths.highlevel_sp / structure_name / f"mult_{multiplicity}"
        basename = f"{structure_name}_m{multiplicity}_highlevel"
        spec = OrcaJobSpec(
            stage_name="highlevel_sp",
            basename=basename,
            workdir=workdir,
            xyz_path=geometry,
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
            raw_input_lines=parallel_lines(config, "highlevel_sp"),
        )
        result = run_job(config, spec, dry_run=dry_run)
        parsed = result.parsed
        rows.append(
            {
                "structure_name": structure_name,
                "multiplicity": multiplicity,
                "charge": config.charge,
                "level_of_theory": HIGHLEVEL_LEVEL,
                "task": "SP",
                "geometry": str(geometry),
                "normal_termination": bool_text(parsed.get("normal_termination")),
                "final_energy_eh": parsed.get("final_energy_eh", ""),
                "s2": parsed.get("s2", ""),
                "input_file": str(result.input_path),
                "output_file": str(result.output_path),
                "job_dir": str(workdir),
                "mode": result.mode,
                "atom_count": meta.get("atom_count", ""),
                "formula": meta.get("formula", ""),
            }
        )
        append_log(config, "highlevel", f"{structure_name} mult={multiplicity} high-level SP finished")

    write_stage_summary(summary_path, rows, energy_key="final_energy_eh")
    write_stage_summary(
        config.paths.summaries / "06_highlevel_summary.csv",
        rows,
        energy_key="final_energy_eh",
    )
    mark_stage_end(config, "highlevel_sp", details=f"jobs={len(rows)} summary={summary_path.name}")
    return summary_path
