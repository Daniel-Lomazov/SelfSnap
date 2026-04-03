from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from selfsnap.models import CaptureBackendError
from selfsnap.runtime_probe import probe_runtime_dependencies

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(slots=True)
class CaptureImage:
    images: list[Any]  # one entry per-monitor in per_monitor mode; one entry in composite mode
    monitor_count: int
    composite_width: int
    composite_height: int


def capture_composite() -> CaptureImage:
    probe = probe_runtime_dependencies()
    if not probe.ok:
        raise CaptureBackendError(f"{probe.summary}: {probe.details}")

    import mss
    from PIL import Image

    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            monitor_count = 1 if len(monitors) <= 1 else len(monitors) - 1
            virtual_monitor = monitors[0]
            shot = sct.grab(virtual_monitor)
            image = Image.frombytes("RGB", shot.size, shot.rgb)
            return CaptureImage(
                images=[image],
                monitor_count=monitor_count,
                composite_width=shot.width,
                composite_height=shot.height,
            )
    except Exception as exc:  # pragma: no cover - backend-specific error translation
        raise CaptureBackendError(str(exc)) from exc


def capture_per_monitor() -> CaptureImage:
    probe = probe_runtime_dependencies()
    if not probe.ok:
        raise CaptureBackendError(f"{probe.summary}: {probe.details}")

    import mss
    from PIL import Image

    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            individual = monitors[1:] if len(monitors) > 1 else monitors[:1]
            images = []
            for monitor in individual:
                shot = sct.grab(monitor)
                images.append(Image.frombytes("RGB", shot.size, shot.rgb))
            composite_width = sum(m["width"] for m in individual)
            composite_height = max(m["height"] for m in individual)
            return CaptureImage(
                images=images,
                monitor_count=len(individual),
                composite_width=composite_width,
                composite_height=composite_height,
            )
    except Exception as exc:  # pragma: no cover - backend-specific error translation
        raise CaptureBackendError(str(exc)) from exc


# Backward-compatible alias
capture_virtual_desktop = capture_composite


def save_capture_images(
    capture: CaptureImage,
    base_path: Path,
    image_format: str = "png",
    image_quality: int = 85,
    per_monitor: bool = False,
) -> list[Path]:
    """Save capture images to disk. Returns list of written paths."""
    from pathlib import Path as _Path

    paths_written: list[_Path] = []
    fmt = image_format.upper()
    ext = f".{image_format.lower()}"
    save_kwargs: dict[str, Any] = {}
    if fmt in ("JPEG", "WEBP"):
        save_kwargs["quality"] = image_quality

    if not per_monitor or len(capture.images) == 1:
        out_path = base_path.with_suffix(ext)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        capture.images[0].save(out_path, format=fmt, **save_kwargs)
        paths_written.append(out_path)
    else:
        stem = base_path.stem
        parent = base_path.parent
        parent.mkdir(parents=True, exist_ok=True)
        for idx, image in enumerate(capture.images, start=1):
            out_path = parent / f"{stem}_m{idx}{ext}"
            image.save(out_path, format=fmt, **save_kwargs)
            paths_written.append(out_path)

    return paths_written
