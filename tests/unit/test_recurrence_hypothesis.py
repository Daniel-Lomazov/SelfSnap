from __future__ import annotations

from datetime import UTC, date, datetime, time

from hypothesis import given, settings
from hypothesis import strategies as st

from selfsnap.models import IntervalUnit, Schedule
from selfsnap.recurrence import iter_occurrences_between, next_occurrence

# ── Strategies ─────────────────────────────────────────────────────────────

_VALID_UNITS = [u.value for u in IntervalUnit]
_VALID_UNITS_NO_HIGH_FREQ = ["hour", "day", "week", "month", "year"]  # skip second/minute for speed


def _schedule_strategy(units: list[str] | None = None) -> st.SearchStrategy[Schedule]:
    chosen_units = units or _VALID_UNITS
    return st.builds(
        lambda iv, iu, sd, st_: Schedule(
            schedule_id="test",
            label="Test",
            interval_value=iv,
            interval_unit=iu,
            start_date_local=sd.isoformat(),
            start_time_local=st_.strftime("%H:%M:%S"),
            enabled=True,
        ),
        iv=st.integers(min_value=1, max_value=52),
        iu=st.sampled_from(chosen_units),
        sd=st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)),
        st_=st.times(min_value=time(0, 0, 0), max_value=time(23, 59, 59)).map(
            lambda t: t.replace(microsecond=0)
        ),
    )


def _reference_dt_strategy() -> st.SearchStrategy[datetime]:
    return st.datetimes(
        min_value=datetime(2023, 1, 1),
        max_value=datetime(2029, 12, 31),
        timezones=st.just(UTC),
    )


# ── Tests ───────────────────────────────────────────────────────────────────


@given(schedule=_schedule_strategy(), ref=_reference_dt_strategy())
@settings(max_examples=200, deadline=2000)
def test_next_occurrence_is_strictly_after_reference(schedule: Schedule, ref: datetime) -> None:
    result = next_occurrence(schedule, ref, include_reference=False)
    if result is not None:
        assert result > ref, f"next_occurrence {result} is not after reference {ref}"


@given(schedule=_schedule_strategy(), ref=_reference_dt_strategy())
@settings(max_examples=200, deadline=2000)
def test_next_occurrence_include_reference_is_gte_reference(
    schedule: Schedule, ref: datetime
) -> None:
    result = next_occurrence(schedule, ref, include_reference=True)
    if result is not None:
        assert result >= ref


@given(
    schedule=_schedule_strategy(units=_VALID_UNITS_NO_HIGH_FREQ),
    ref=_reference_dt_strategy(),
)
@settings(max_examples=100, deadline=5000)
def test_iter_occurrences_between_is_monotonically_increasing(
    schedule: Schedule, ref: datetime
) -> None:
    from datetime import timedelta

    # Use timedelta instead of replace(year=...) to avoid leap-day ValueError
    # (Feb 29 + 2 years would land on a non-leap year)
    end = ref + timedelta(days=min(365 * 2, (2030 - ref.year) * 365))
    occurrences = list(iter_occurrences_between(schedule, ref, end))
    for a, b in zip(occurrences, occurrences[1:], strict=False):
        assert a < b, f"occurrences not monotone: {a} >= {b}"


@given(schedule=_schedule_strategy(), ref=_reference_dt_strategy())
@settings(max_examples=200, deadline=2000)
def test_next_occurrence_never_returns_naive_datetime(schedule: Schedule, ref: datetime) -> None:
    result = next_occurrence(schedule, ref, include_reference=False)
    if result is not None:
        assert result.tzinfo is not None, "next_occurrence returned a naive datetime"
