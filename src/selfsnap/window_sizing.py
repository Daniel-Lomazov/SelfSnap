from __future__ import annotations

LEGACY_SETTINGS_WINDOW_WIDTH = 960
LEGACY_SETTINGS_WINDOW_HEIGHT = 760

DEFAULT_SETTINGS_WINDOW_WIDTH = 640
DEFAULT_SETTINGS_WINDOW_HEIGHT = 480

MIGRATED_SETTINGS_WINDOW_SIZES = frozenset(
    {
        (LEGACY_SETTINGS_WINDOW_WIDTH, LEGACY_SETTINGS_WINDOW_HEIGHT),
        (864, 684),
        (816, 646),
        (792, 627),
        (768, 608),
        (744, 580),
    }
)

SETTINGS_WINDOW_MIN_WIDTH = 640
SETTINGS_WINDOW_MIN_HEIGHT = 480


def clamp_settings_window_size(width: int, height: int) -> tuple[int, int]:
    return max(width, SETTINGS_WINDOW_MIN_WIDTH), max(height, SETTINGS_WINDOW_MIN_HEIGHT)


def resolve_initial_settings_window_size(width: int, height: int) -> tuple[int, int]:
    if (width, height) in MIGRATED_SETTINGS_WINDOW_SIZES:
        return DEFAULT_SETTINGS_WINDOW_WIDTH, DEFAULT_SETTINGS_WINDOW_HEIGHT
    return clamp_settings_window_size(width, height)


def build_centered_window_geometry(
    screen_width: int,
    screen_height: int,
    window_width: int,
    window_height: int,
) -> str:
    x = max((screen_width - window_width) // 2, 0)
    y = max((screen_height - window_height) // 2, 0)
    return f"{window_width}x{window_height}+{x}+{y}"