from __future__ import annotations

from selfsnap.window_sizing import (
    DEFAULT_SETTINGS_WINDOW_HEIGHT,
    DEFAULT_SETTINGS_WINDOW_WIDTH,
    SETTINGS_WINDOW_MIN_HEIGHT,
    SETTINGS_WINDOW_MIN_WIDTH,
    build_centered_window_geometry,
    clamp_settings_window_size,
    resolve_initial_settings_window_size,
)


def test_clamp_settings_window_size_applies_floor() -> None:
    assert clamp_settings_window_size(200, 300) == (
        SETTINGS_WINDOW_MIN_WIDTH,
        SETTINGS_WINDOW_MIN_HEIGHT,
    )


def test_resolve_initial_settings_window_size_replaces_legacy_default() -> None:
    assert resolve_initial_settings_window_size(960, 760) == (
        DEFAULT_SETTINGS_WINDOW_WIDTH,
        DEFAULT_SETTINGS_WINDOW_HEIGHT,
    )


def test_resolve_initial_settings_window_size_replaces_previous_default() -> None:
    assert resolve_initial_settings_window_size(864, 684) == (
        DEFAULT_SETTINGS_WINDOW_WIDTH,
        DEFAULT_SETTINGS_WINDOW_HEIGHT,
    )


def test_resolve_initial_settings_window_size_replaces_most_recent_default() -> None:
    assert resolve_initial_settings_window_size(816, 646) == (
        DEFAULT_SETTINGS_WINDOW_WIDTH,
        DEFAULT_SETTINGS_WINDOW_HEIGHT,
    )


def test_resolve_initial_settings_window_size_replaces_current_previous_default() -> None:
    assert resolve_initial_settings_window_size(792, 627) == (
        DEFAULT_SETTINGS_WINDOW_WIDTH,
        DEFAULT_SETTINGS_WINDOW_HEIGHT,
    )


def test_resolve_initial_settings_window_size_replaces_latest_previous_default() -> None:
    assert resolve_initial_settings_window_size(768, 608) == (
        DEFAULT_SETTINGS_WINDOW_WIDTH,
        DEFAULT_SETTINGS_WINDOW_HEIGHT,
    )


def test_resolve_initial_settings_window_size_replaces_last_compact_default() -> None:
    assert resolve_initial_settings_window_size(744, 580) == (
        DEFAULT_SETTINGS_WINDOW_WIDTH,
        DEFAULT_SETTINGS_WINDOW_HEIGHT,
    )


def test_build_centered_window_geometry_returns_centered_coordinates() -> None:
    assert build_centered_window_geometry(1920, 1080, 640, 480) == "640x480+640+300"