from __future__ import annotations

import importlib
import platform
import sys
from dataclasses import asdict, dataclass


@dataclass(slots=True)
class DependencyProbeResult:
    ok: bool
    summary: str
    details: str
    classification: str
    python_executable: str
    python_version: str
    python_architecture: str
    pillow_version: str | None = None
    pillow_path: str | None = None

    def to_dict(self) -> dict[str, str | bool | None]:
        return asdict(self)


def probe_runtime_dependencies() -> DependencyProbeResult:
    python_architecture = platform.architecture()[0]
    python_version = sys.version
    python_executable = sys.executable

    try:
        importlib.import_module("pystray")
        pillow_module = importlib.import_module("PIL")
        pillow_image = importlib.import_module("PIL.Image")
        pillow_binary = importlib.import_module("PIL._imaging")
        importlib.import_module("mss")
    except ModuleNotFoundError as exc:
        return DependencyProbeResult(
            ok=False,
            summary="Runtime dependency is missing",
            details=_format_error_details(
                exc, python_executable, python_version, python_architecture
            ),
            classification="missing_dependency",
            python_executable=python_executable,
            python_version=python_version,
            python_architecture=python_architecture,
        )
    except ImportError as exc:
        return DependencyProbeResult(
            ok=False,
            summary="Runtime dependency failed to load",
            details=_format_error_details(
                exc, python_executable, python_version, python_architecture
            ),
            classification="broken_native_dependency",
            python_executable=python_executable,
            python_version=python_version,
            python_architecture=python_architecture,
        )

    return DependencyProbeResult(
        ok=True,
        summary="Runtime dependencies are healthy",
        details="Imported pystray, PIL.Image, PIL._imaging, and mss successfully.",
        classification="ok",
        python_executable=python_executable,
        python_version=python_version,
        python_architecture=python_architecture,
        pillow_version=getattr(pillow_module, "__version__", None),
        pillow_path=getattr(pillow_image, "__file__", None)
        or getattr(pillow_binary, "__file__", None),
    )


def _format_error_details(
    exc: BaseException,
    python_executable: str,
    python_version: str,
    python_architecture: str,
) -> str:
    return (
        f"{exc.__class__.__name__}: {exc}\n"
        f"python_executable={python_executable}\n"
        f"python_version={python_version}\n"
        f"python_architecture={python_architecture}"
    )
