from __future__ import annotations

from datetime import datetime

from selfsnap.scheduler.reconcile import iter_planned_slots


def test_iter_planned_slots_returns_expected_points() -> None:
    start = datetime(2026, 3, 20, 20, 0, 0).astimezone()
    end = datetime(2026, 3, 21, 22, 0, 0).astimezone()
    slots = iter_planned_slots("21:00", start, end)
    assert len(slots) == 2
    assert slots[0].hour == 21
    assert slots[1].day == 21

