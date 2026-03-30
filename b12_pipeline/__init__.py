"""Repository-root package shim for the src-layout project."""

from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

ROOT = Path(__file__).resolve().parents[1]
SRC_PACKAGE = ROOT / "src" / "b12_pipeline"

if SRC_PACKAGE.is_dir():
    src_package_text = str(SRC_PACKAGE)
    if src_package_text not in __path__:
        __path__.append(src_package_text)
