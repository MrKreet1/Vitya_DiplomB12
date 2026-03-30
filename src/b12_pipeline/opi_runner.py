"""Thin wrapper around OPI job construction and execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import os
from pathlib import Path

from .config import ProjectConfig
from .filesystem import ensure_dir
from .orca_parser import parse_orca_output
from .xyz import find_best_xyz_output, write_last_frame


@dataclass(slots=True)
class OrcaJobSpec:
    stage_name: str
    basename: str
    workdir: Path
    xyz_path: Path
    charge: int
    multiplicity: int
    simple_keywords: list[object] = field(default_factory=list)
    blocks: list[object] = field(default_factory=list)
    raw_input_lines: list[str] = field(default_factory=list)


@dataclass(slots=True)
class OrcaJobResult:
    spec: OrcaJobSpec
    input_path: Path
    output_path: Path
    final_xyz_path: Path | None
    parsed: dict[str, object]
    mode: str


def run_job(config: ProjectConfig, spec: OrcaJobSpec, dry_run: bool = False) -> OrcaJobResult:
    from opi.core import Calculator
    from opi.input.structures.structure import Structure

    _configure_environment(config)
    ensure_dir(spec.workdir)
    _append_job_event(
        config,
        spec,
        status="START",
        details=f"mode={'dry-run' if dry_run else 'run'} xyz={spec.xyz_path.name} mult={spec.multiplicity}",
    )

    calc = Calculator(
        spec.basename,
        working_dir=spec.workdir,
        version_check=config.resources.version_check,
    )
    calc.structure = Structure.from_xyz(spec.xyz_path, charge=spec.charge, multiplicity=spec.multiplicity)
    if spec.simple_keywords:
        calc.input.add_simple_keywords(*spec.simple_keywords)
    for block in spec.blocks:
        calc.input.add_blocks(block)
    if spec.raw_input_lines:
        calc.input.add_arbitrary_string("\n".join(spec.raw_input_lines))

    calc.write_input()
    input_path = spec.workdir / f"{spec.basename}.inp"
    output_path = spec.workdir / f"{spec.basename}.out"

    if dry_run:
        result = OrcaJobResult(
            spec=spec,
            input_path=input_path,
            output_path=output_path,
            final_xyz_path=None,
            parsed={},
            mode="write_input",
        )
        _append_job_event(config, spec, status="END", details="result=write_input")
        return result

    try:
        calc.run()
        final_xyz = _resolve_final_xyz(spec.workdir, spec.basename)
        parsed = parse_orca_output(output_path) if output_path.exists() else {}
        result = OrcaJobResult(
            spec=spec,
            input_path=input_path,
            output_path=output_path,
            final_xyz_path=final_xyz,
            parsed=parsed,
            mode="run",
        )
        _append_job_event(
            config,
            spec,
            status="END",
            details=f"normal_termination={parsed.get('normal_termination')} energy={parsed.get('final_energy_eh')}",
        )
        return result
    except Exception as exc:
        _append_job_event(config, spec, status="ERROR", details=f"{exc.__class__.__name__}: {exc}")
        raise


def _configure_environment(config: ProjectConfig) -> None:
    if config.resources.orca_path is not None:
        os.environ["OPI_ORCA"] = str(config.resources.orca_path)
    if config.resources.mpi_path is not None:
        os.environ["OPI_MPI"] = str(config.resources.mpi_path)


def _resolve_final_xyz(workdir: Path, basename: str) -> Path | None:
    xyz_path = find_best_xyz_output(workdir, basename)
    if xyz_path is None:
        return None
    if xyz_path.name.endswith("_trj.xyz"):
        final_path = workdir / f"{basename}_final.xyz"
        write_last_frame(xyz_path, final_path)
        return final_path
    return xyz_path


def _append_job_event(config: ProjectConfig, spec: OrcaJobSpec, status: str, details: str = "") -> None:
    log_path = config.paths.logs / "pipeline_events.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = f" {details}" if details else ""
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{status} stage={spec.stage_name} job={spec.basename}{suffix}\n"
        )
