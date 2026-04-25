from __future__ import annotations

from datetime import UTC, datetime

import pytest

from selfsnap.models import Schedule
from selfsnap.recurrence import (
    is_coarse_schedule,
    is_high_frequency_schedule,
    iter_occurrences_between,
    next_occurrence,
)


def _schedule(
    *,
    schedule_id: str,
    interval_value: int,
    interval_unit: str,
    start_date_local: str = "2026-01-31",
    start_time_local: str = "09:00:00",
) -> Schedule:
    return Schedule(
        schedule_id=schedule_id,
        label=schedule_id.replace("_", " ").title(),
        interval_value=interval_value,
        interval_unit=interval_unit,
        start_date_local=start_date_local,
        start_time_local=start_time_local,
    )


@pytest.mark.parametrize(
    ("interval_unit", "interval_value", "reference", "expected"),
    [
        (
            "second",
            15,
            datetime(2026, 1, 31, 9, 0, 10, tzinfo=UTC),
            datetime(2026, 1, 31, 9, 0, 15, tzinfo=UTC),
        ),
        (
            "minute",
            5,
            datetime(2026, 1, 31, 9, 3, 0, tzinfo=UTC),
            datetime(2026, 1, 31, 9, 5, 0, tzinfo=UTC),
        ),
        (
            "hour",
            2,
            datetime(2026, 1, 31, 10, 0, 0, tzinfo=UTC),
            datetime(2026, 1, 31, 11, 0, 0, tzinfo=UTC),
        ),
        (
            "day",
            1,
            datetime(2026, 2, 1, 10, 0, 0, tzinfo=UTC),
            datetime(2026, 2, 2, 9, 0, 0, tzinfo=UTC),
        ),
        (
            "week",
            2,
            datetime(2026, 2, 7, 9, 0, 0, tzinfo=UTC),
            datetime(2026, 2, 14, 9, 0, 0, tzinfo=UTC),
        ),
    ],
)
def test_fixed_unit_next_occurrence(
    interval_unit: str,
    interval_value: int,
    reference: datetime,
    expected: datetime,
) -> None:
    schedule = _schedule(
        schedule_id=f"{interval_unit}_schedule",
        interval_value=interval_value,
        interval_unit=interval_unit,
    )

    assert next_occurrence(schedule, reference) == expected


def test_calendar_units_skip_invalid_dates() -> None:
    month_schedule = _schedule(
        schedule_id="monthly",
        interval_value=1,
        interval_unit="month",
        start_date_local="2026-01-31",
    )
    year_schedule = _schedule(
        schedule_id="yearly",
        interval_value=1,
        interval_unit="year",
        start_date_local="2024-02-29",
    )

    assert (
        next_occurrence(
            month_schedule,
            datetime(2026, 2, 15, 9, 0, 0, tzinfo=UTC),
        )
        .date()
        .isoformat()
        == "2026-03-31"
    )
    assert (
        next_occurrence(
            year_schedule,
            datetime(2025, 3, 1, 9, 0, 0, tzinfo=UTC),
        )
        .date()
        .isoformat()
        == "2028-02-29"
    )


def test_iter_occurrences_between_returns_expected_points() -> None:
    schedule = _schedule(
        schedule_id="every_two_days",
        interval_value=2,
        interval_unit="day",
        start_date_local="2026-03-20",
        start_time_local="20:00:00",
    )
    start = datetime(2026, 3, 20, 19, 0, 0, tzinfo=UTC)
    end = datetime(2026, 3, 25, 21, 0, 0, tzinfo=UTC)

    slots = iter_occurrences_between(schedule, start, end)

    assert [slot.date().isoformat() for slot in slots] == [
        "2026-03-20",
        "2026-03-22",
        "2026-03-24",
    ]
    assert [slot.time().strftime("%H:%M:%S") for slot in slots] == [
        "20:00:00",
        "20:00:00",
        "20:00:00",
    ]


def test_schedule_classification_helpers() -> None:
    assert is_high_frequency_schedule(
        _schedule(schedule_id="fast", interval_value=1, interval_unit="second")
    )
    assert is_high_frequency_schedule(
        _schedule(schedule_id="fast2", interval_value=1, interval_unit="minute")
    )
    assert not is_high_frequency_schedule(
        _schedule(schedule_id="slow", interval_value=1, interval_unit="day")
    )
    assert is_coarse_schedule(_schedule(schedule_id="slow", interval_value=1, interval_unit="day"))
