from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from selfsnap.models import CaptureBackendError
from selfsnap.runtime_probe import probe_runtime_dependencies


@dataclass(slots=True)
class CaptureImage:
    image: Any
    monitor_count: int
    composite_width: int
    composite_height: int


def capture_virtual_desktop() -> CaptureImage:
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
                image=image,
                monitor_count=monitor_count,
                composite_width=shot.width,
                composite_height=shot.height,
            )
    except Exception as exc:  # pragma: no cover - backend-specific error translation
        raise CaptureBackendError(str(exc)) from exc
