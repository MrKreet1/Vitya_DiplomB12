"""Frequency analysis for refined candidates."""

from __future__ import annotations

from pathlib import Path

from opi.input.blocks import BlockFreq, BlockOutput
from opi.input.simple_keywords import Dft, Scf, Task

from ..config import ProjectConfig
from ..constants import SCREENING_LEVEL
from ..opi_runner import OrcaJobSpec, run_job
from ..reporting import write_stage_summary
from ..resources import parallel_lines
from .common import append_log, bool_text, candidate_metadata, load_summary, mark_stage_end, mark_stage_start


def run_frequencies(config: ProjectConfig, dry_run: bool = False) -> Path:
    mark_stage_start(config, "frequencies")
    refinement_summary = config.paths.refinement / "summary.csv"
    candidates = load_summary(refinement_summary)
    rows: list[dict[str, object]] = []
    summary_path = config.paths.frequencies / "summary.csv"

    for candidate in candidates:
        structure_name = candidate["structure_name"]
        multiplicity = int(candidate["multiplicity"])
        geometry = Path(candidate.get("refined_xyz") or candidate["source_geometry"])
        meta = candidate_metadata(geometry)
        workdir = config.paths.frequencies / structure_name / f"mult_{multiplicity}"
        basename = f"{structure_name}_m{multiplicity}_freq"
        spec = OrcaJobSpec(
            stage_name="frequencies",
            basename=basename,
            workdir=workdir,
            xyz_path=geometry,
            charge=config.charge,
            multiplicity=multiplicity,
            simple_keywords=[Dft.R2SCAN_3C, Task.FREQ, Scf.TIGHTSCF],
            blocks=[BlockOutput(jsonpropfile=True), BlockFreq(temp=298.15, pressure=1.0)],
            raw_input_lines=parallel_lines(config, "frequencies"),
        )
        result = run_job(config, spec, dry_run=dry_run)
        parsed = result.parsed
        rows.append(
            {
                "structure_name": structure_name,
                "multiplicity": multiplicity,
                "charge": config.charge,
                "level_of_theory": SCREENING_LEVEL,
                "task": "FREQ",
                "source_geometry": str(geometry),
                "normal_termination": bool_text(parsed.get("normal_termination")),
                "final_energy_eh": parsed.get("final_energy_eh", ""),
                "nimag": parsed.get("nimag", ""),
                "minimum_confirmed": bool_text(parsed.get("nimag") == 0 if parsed else False),
                "min_frequency_cm-1": parsed.get("min_frequency_cm-1", ""),
                "max_frequency_cm-1": parsed.get("max_frequency_cm-1", ""),
                "zero_point_energy_eh": parsed.get("zero_point_energy_eh", ""),
                "thermal_correction_eh": parsed.get("thermal_correction_eh", ""),
                "gibbs_free_energy_eh": parsed.get("gibbs_free_energy_eh", ""),
                "input_file": str(result.input_path),
                "output_file": str(result.output_path),
                "job_dir": str(workdir),
                "mode": result.mode,
                "atom_count": meta.get("atom_count", ""),
                "formula": meta.get("formula", ""),
            }
        )
        append_log(
            config,
            "frequencies",
            f"{structure_name} mult={multiplicity} nimag={parsed.get('nimag', '')}",
        )

    write_stage_summary(summary_path, rows, energy_key="final_energy_eh")
    write_stage_summary(
        config.paths.summaries / "04_frequencies_summary.csv",
        rows,
        energy_key="final_energy_eh",
    )
    mark_stage_end(config, "frequencies", details=f"jobs={len(rows)} summary={summary_path.name}")
    return summary_path
