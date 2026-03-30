"""DLPNO-CCSD(T) control calculations."""

from __future__ import annotations

from pathlib import Path

from opi.input.blocks import BlockMdci, BlockOutput
from opi.input.simple_keywords import AuxBasisSet, BasisSet, Dlpno, Scf, Task, Wft

from ..config import ProjectConfig
from ..constants import DLPNO_LEVEL
from ..opi_runner import OrcaJobSpec, run_job
from ..reporting import write_stage_summary
from ..resources import parallel_lines
from ..selection import select_low_energy_rows
from .common import append_log, bool_text, candidate_metadata, load_summary, mark_stage_end, mark_stage_start


def run_dlpno_check(config: ProjectConfig, dry_run: bool = False) -> Path:
    mark_stage_start(config, "dlpno_check")
    highlevel_summary = config.paths.highlevel_sp / "summary.csv"
    candidates = select_low_energy_rows(
        load_summary(highlevel_summary),
        energy_key="final_energy_eh",
        top_n=config.selection.dlpno_candidate_count,
        energy_window_kj_mol=None,
    )
    rows: list[dict[str, object]] = []
    summary_path = config.paths.dlpno_check / "summary.csv"

    for candidate in candidates:
        structure_name = candidate["structure_name"]
        multiplicity = int(candidate["multiplicity"])
        geometry = Path(candidate["geometry"])
        meta = candidate_metadata(geometry)
        workdir = config.paths.dlpno_check / structure_name / f"mult_{multiplicity}"
        basename = f"{structure_name}_m{multiplicity}_dlpno"
        spec = OrcaJobSpec(
            stage_name="dlpno_check",
            basename=basename,
            workdir=workdir,
            xyz_path=geometry,
            charge=config.charge,
            multiplicity=multiplicity,
            simple_keywords=[
                Wft.DLPNO_CCSD_T,
                BasisSet.DEF2_TZVPP,
                AuxBasisSet.DEF2_J,
                AuxBasisSet.DEF2_TZVPP_C,
                Dlpno.TIGHTPNO,
                Task.SP,
                Scf.TIGHTSCF,
            ],
            blocks=[BlockOutput(jsonpropfile=True), BlockMdci(maxiter=200, printlevel=3)],
            raw_input_lines=parallel_lines(config, "dlpno_check"),
        )
        result = run_job(config, spec, dry_run=dry_run)
        parsed = result.parsed
        rows.append(
            {
                "structure_name": structure_name,
                "multiplicity": multiplicity,
                "charge": config.charge,
                "level_of_theory": DLPNO_LEVEL,
                "task": "SP",
                "geometry": str(geometry),
                "normal_termination": bool_text(parsed.get("normal_termination")),
                "final_energy_eh": parsed.get("final_energy_eh", ""),
                "t1_diagnostic": parsed.get("t1_diagnostic", ""),
                "s2": parsed.get("s2", ""),
                "input_file": str(result.input_path),
                "output_file": str(result.output_path),
                "job_dir": str(workdir),
                "mode": result.mode,
                "atom_count": meta.get("atom_count", ""),
                "formula": meta.get("formula", ""),
            }
        )
        append_log(config, "dlpno", f"{structure_name} mult={multiplicity} DLPNO finished")

    write_stage_summary(summary_path, rows, energy_key="final_energy_eh")
    write_stage_summary(
        config.paths.summaries / "07_dlpno_summary.csv",
        rows,
        energy_key="final_energy_eh",
    )
    mark_stage_end(config, "dlpno_check", details=f"jobs={len(rows)} summary={summary_path.name}")
    return summary_path
