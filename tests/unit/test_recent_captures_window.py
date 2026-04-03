from __future__ import annotations

from selfsnap.tray.recent_captures_window import _format_local_timestamp


def test_recent_captures_timestamp_treats_naive_as_utc() -> None:
    naive = "2026-04-03T14:03:00"
    explicit_utc = "2026-04-03T14:03:00+00:00"

    assert _format_local_timestamp(naive) == _format_local_timestamp(explicit_utc)
