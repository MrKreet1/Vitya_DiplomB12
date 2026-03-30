"""Project configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(slots=True)
class ResourcePreset:
    nprocs: int | None = None
    maxcore_mb: int | None = None


@dataclass(slots=True)
class ResourcesConfig:
    nprocs: int = 8
    maxcore_mb: int = 4000
    orca_path: Path | None = None
    mpi_path: Path | None = None
    version_check: bool = False
    stage_resources: dict[str, ResourcePreset] | None = None

    def resolve(self, stage_name: str) -> ResourcePreset:
        preset = (self.stage_resources or {}).get(stage_name)
        return ResourcePreset(
            nprocs=preset.nprocs if preset and preset.nprocs is not None else self.nprocs,
            maxcore_mb=preset.maxcore_mb if preset and preset.maxcore_mb is not None else self.maxcore_mb,
        )


@dataclass(slots=True)
class SelectionConfig:
    top_n: int | None = 5
    energy_window_kj_mol: float | None = 15.0
    dlpno_candidate_count: int = 2
    multiref_candidate_count: int = 2


@dataclass(slots=True)
class MultireferenceCriteria:
    spin_gap_threshold_kj_mol: float = 10.0
    t1_threshold: float = 0.02
    spin_contamination_tolerance: float = 0.30


@dataclass(slots=True)
class CasscfConfig:
    nel: int = 12
    norb: int = 12
    nroots: int = 1
    weights: float | None = None
    maxiter: int = 200
    print_level: int = 3
    mults: list[int] | None = None
    nevpt2: bool = True


@dataclass(slots=True)
class PathsConfig:
    project_root: Path
    initial_structures: Path
    screening: Path
    refinement: Path
    frequencies: Path
    spin_comparison: Path
    highlevel_sp: Path
    dlpno_check: Path
    casscf_nevpt2: Path
    logs: Path
    summaries: Path

    def ensure(self) -> None:
        for path in (
            self.initial_structures,
            self.screening,
            self.refinement,
            self.frequencies,
            self.spin_comparison,
            self.highlevel_sp,
            self.dlpno_check,
            self.casscf_nevpt2,
            self.logs,
            self.summaries,
        ):
            path.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class ProjectConfig:
    project_root: Path
    project_name: str
    charge: int
    screening_multiplicities: list[int]
    spin_comparison_multiplicities: list[int]
    resources: ResourcesConfig
    selection: SelectionConfig
    multireference: MultireferenceCriteria
    casscf: CasscfConfig
    paths: PathsConfig

    def ensure_directories(self) -> None:
        self.paths.ensure()


def _resolve_path(project_root: Path, raw: str | None, default_name: str) -> Path:
    if raw is None:
        return project_root / default_name
    path = Path(raw)
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def _coerce_path(raw: str | None, project_root: Path) -> Path | None:
    if raw in (None, ""):
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def load_config(config_path: str | Path) -> ProjectConfig:
    path = Path(config_path).resolve()
    project_root = path.parent.parent if path.parent.name == "config" else path.parent
    payload = json.loads(path.read_text(encoding="utf-8"))

    resources_payload = payload.get("resources", {})
    selection_payload = payload.get("selection", {})
    multiref_payload = payload.get("multireference", {})
    casscf_payload = payload.get("casscf", {})
    paths_payload = payload.get("paths", {})

    resources = ResourcesConfig(
        nprocs=int(resources_payload.get("nprocs", 8)),
        maxcore_mb=int(resources_payload.get("maxcore_mb", 4000)),
        orca_path=_coerce_path(resources_payload.get("orca_path"), project_root),
        mpi_path=_coerce_path(resources_payload.get("mpi_path"), project_root),
        version_check=bool(resources_payload.get("version_check", False)),
        stage_resources={
            stage_name: ResourcePreset(
                nprocs=int(stage_payload["nprocs"]) if "nprocs" in stage_payload else None,
                maxcore_mb=int(stage_payload["maxcore_mb"]) if "maxcore_mb" in stage_payload else None,
            )
            for stage_name, stage_payload in resources_payload.get("stage_resources", {}).items()
        }
        or None,
    )

    selection = SelectionConfig(
        top_n=selection_payload.get("top_n"),
        energy_window_kj_mol=selection_payload.get("energy_window_kj_mol"),
        dlpno_candidate_count=int(selection_payload.get("dlpno_candidate_count", 2)),
        multiref_candidate_count=int(selection_payload.get("multiref_candidate_count", 2)),
    )

    multireference = MultireferenceCriteria(
        spin_gap_threshold_kj_mol=float(multiref_payload.get("spin_gap_threshold_kj_mol", 10.0)),
        t1_threshold=float(multiref_payload.get("t1_threshold", 0.02)),
        spin_contamination_tolerance=float(
            multiref_payload.get("spin_contamination_tolerance", 0.30)
        ),
    )

    casscf = CasscfConfig(
        nel=int(casscf_payload.get("nel", 12)),
        norb=int(casscf_payload.get("norb", 12)),
        nroots=int(casscf_payload.get("nroots", 1)),
        weights=casscf_payload.get("weights"),
        maxiter=int(casscf_payload.get("maxiter", 200)),
        print_level=int(casscf_payload.get("print_level", 3)),
        mults=list(casscf_payload.get("mults", [])) or None,
        nevpt2=bool(casscf_payload.get("nevpt2", True)),
    )

    paths = PathsConfig(
        project_root=project_root,
        initial_structures=_resolve_path(project_root, paths_payload.get("initial_structures"), "01_initial_structures"),
        screening=_resolve_path(project_root, paths_payload.get("screening"), "02_screening_r2scan3c"),
        refinement=_resolve_path(project_root, paths_payload.get("refinement"), "03_refined_candidates"),
        frequencies=_resolve_path(project_root, paths_payload.get("frequencies"), "04_frequencies"),
        spin_comparison=_resolve_path(project_root, paths_payload.get("spin_comparison"), "05_spin_comparison"),
        highlevel_sp=_resolve_path(project_root, paths_payload.get("highlevel_sp"), "06_highlevel_sp"),
        dlpno_check=_resolve_path(project_root, paths_payload.get("dlpno_check"), "07_dlpno_check"),
        casscf_nevpt2=_resolve_path(project_root, paths_payload.get("casscf_nevpt2"), "08_casscf_nevpt2"),
        logs=_resolve_path(project_root, paths_payload.get("logs"), "logs"),
        summaries=_resolve_path(project_root, paths_payload.get("summaries"), "summaries"),
    )

    return ProjectConfig(
        project_root=project_root,
        project_name=str(payload.get("project_name", "B12 ORCA pipeline")),
        charge=int(payload.get("charge", 0)),
        screening_multiplicities=list(payload.get("screening_multiplicities", [1, 3, 5])),
        spin_comparison_multiplicities=list(
            payload.get("spin_comparison_multiplicities", [1, 3, 5])
        ),
        resources=resources,
        selection=selection,
        multireference=multireference,
        casscf=casscf,
        paths=paths,
    )
