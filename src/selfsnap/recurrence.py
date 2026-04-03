from __future__ import annotations

from datetime import date, datetime, time, timedelta
from math import floor

from selfsnap.models import IntervalUnit, Schedule

HIGH_FREQUENCY_UNITS = {IntervalUnit.SECOND.value, IntervalUnit.MINUTE.value}
COARSE_UNITS = {
    IntervalUnit.HOUR.value,
    IntervalUnit.DAY.value,
    IntervalUnit.WEEK.value,
    IntervalUnit.MONTH.value,
    IntervalUnit.YEAR.value,
}


def parse_schedule_anchor(schedule: Schedule, tzinfo) -> datetime:
    anchor_date = date.fromisoformat(schedule.start_date_local)
    anchor_time = time.fromisoformat(schedule.normalized_start_time_local)
    return datetime.combine(anchor_date, anchor_time, tzinfo=tzinfo)


def is_high_frequency_schedule(schedule: Schedule) -> bool:
    return schedule.interval_unit in HIGH_FREQUENCY_UNITS


def is_coarse_schedule(schedule: Schedule) -> bool:
    return schedule.interval_unit in COARSE_UNITS


def next_occurrence(
    schedule: Schedule,
    reference_local: datetime,
    *,
    include_reference: bool = False,
) -> datetime | None:
    if reference_local.tzinfo is None:
        raise ValueError("reference_local must be timezone-aware")

    anchor = parse_schedule_anchor(schedule, reference_local.tzinfo)
    if include_reference:
        if reference_local <= anchor:
            return anchor
    elif reference_local < anchor:
        return anchor

    if schedule.interval_unit in {
        IntervalUnit.SECOND.value,
        IntervalUnit.MINUTE.value,
        IntervalUnit.HOUR.value,
        IntervalUnit.DAY.value,
        IntervalUnit.WEEK.value,
    }:
        return _next_fixed_occurrence(schedule, anchor, reference_local, include_reference)

    return _next_calendar_occurrence(schedule, anchor, reference_local, include_reference)


def previous_occurrence(
    schedule: Schedule,
    reference_local: datetime,
    *,
    include_reference: bool = False,
) -> datetime | None:
    if reference_local.tzinfo is None:
        raise ValueError("reference_local must be timezone-aware")

    anchor = parse_schedule_anchor(schedule, reference_local.tzinfo)
    if include_reference:
        if reference_local < anchor:
            return None
    elif reference_local <= anchor:
        return anchor if reference_local == anchor and include_reference else None

    if schedule.interval_unit in {
        IntervalUnit.SECOND.value,
        IntervalUnit.MINUTE.value,
        IntervalUnit.HOUR.value,
        IntervalUnit.DAY.value,
        IntervalUnit.WEEK.value,
    }:
        return _previous_fixed_occurrence(schedule, anchor, reference_local, include_reference)

    return _previous_calendar_occurrence(schedule, anchor, reference_local, include_reference)


def iter_occurrences_between(
    schedule: Schedule,
    start_local: datetime,
    end_local: datetime,
    *,
    include_start: bool = True,
) -> list[datetime]:
    if end_local < start_local:
        return []

    output: list[datetime] = []
    candidate = next_occurrence(schedule, start_local, include_reference=include_start)
    while candidate is not None and candidate <= end_local:
        output.append(candidate)
        candidate = next_occurrence(schedule, candidate, include_reference=False)
    return output


def _next_fixed_occurrence(
    schedule: Schedule,
    anchor_local: datetime,
    reference_local: datetime,
    include_reference: bool,
) -> datetime:
    delta = _fixed_delta(schedule.interval_unit, schedule.interval_value)
    if delta.total_seconds() <= 0:
        raise ValueError("Recurrence delta must be positive")

    elapsed_seconds = (reference_local - anchor_local).total_seconds()
    step_seconds = delta.total_seconds()
    if elapsed_seconds < 0:
        return anchor_local

    steps = max(0, floor(elapsed_seconds / step_seconds))
    candidate = anchor_local + (delta * steps)
    if candidate < reference_local or (candidate == reference_local and not include_reference):
        candidate += delta
    return candidate


def _next_calendar_occurrence(
    schedule: Schedule,
    anchor_local: datetime,
    reference_local: datetime,
    include_reference: bool,
) -> datetime | None:
    anchor_month_index = (anchor_local.year * 12) + (anchor_local.month - 1)
    reference_month_index = (reference_local.year * 12) + (reference_local.month - 1)
    step_months = (
        schedule.interval_value
        if schedule.interval_unit == IntervalUnit.MONTH.value
        else schedule.interval_value * 12
    )

    if reference_month_index <= anchor_month_index:
        candidate = _calendar_candidate(anchor_local, 0)
        if candidate is not None and (
            candidate > reference_local or (include_reference and candidate == reference_local)
        ):
            return candidate

    months_since_anchor = max(0, reference_month_index - anchor_month_index)
    step_index = max(0, floor(months_since_anchor / step_months))

    while True:
        candidate = _calendar_candidate(anchor_local, step_index * step_months)
        if candidate is not None:
            if candidate > reference_local or (include_reference and candidate == reference_local):
                return candidate
        step_index += 1


def _previous_fixed_occurrence(
    schedule: Schedule,
    anchor_local: datetime,
    reference_local: datetime,
    include_reference: bool,
) -> datetime | None:
    delta = _fixed_delta(schedule.interval_unit, schedule.interval_value)
    if delta.total_seconds() <= 0:
        raise ValueError("Recurrence delta must be positive")

    elapsed_seconds = (reference_local - anchor_local).total_seconds()
    if elapsed_seconds < 0:
        return None

    step_seconds = delta.total_seconds()
    steps = max(0, floor(elapsed_seconds / step_seconds))
    candidate = anchor_local + (delta * steps)
    if candidate > reference_local or (candidate == reference_local and not include_reference):
        candidate -= delta
    if candidate < anchor_local:
        return None
    return candidate


def _previous_calendar_occurrence(
    schedule: Schedule,
    anchor_local: datetime,
    reference_local: datetime,
    include_reference: bool,
) -> datetime | None:
    anchor_month_index = (anchor_local.year * 12) + (anchor_local.month - 1)
    reference_month_index = (reference_local.year * 12) + (reference_local.month - 1)
    step_months = (
        schedule.interval_value
        if schedule.interval_unit == IntervalUnit.MONTH.value
        else schedule.interval_value * 12
    )
    step_index = max(0, floor(max(0, reference_month_index - anchor_month_index) / step_months))

    while step_index >= 0:
        candidate = _calendar_candidate(anchor_local, step_index * step_months)
        if candidate is not None:
            if candidate < reference_local or (include_reference and candidate == reference_local):
                return candidate
        step_index -= 1
    return None


def _calendar_candidate(anchor_local: datetime, month_offset: int) -> datetime | None:
    year, month = _add_month_offset(anchor_local.year, anchor_local.month, month_offset)
    try:
        candidate_date = date(year, month, anchor_local.day)
    except ValueError:
        return None
    return datetime.combine(candidate_date, anchor_local.timetz(), tzinfo=anchor_local.tzinfo)


def _add_month_offset(year: int, month: int, offset: int) -> tuple[int, int]:
    raw_month_index = ((year * 12) + (month - 1)) + offset
    new_year, month_index = divmod(raw_month_index, 12)
    return new_year, month_index + 1


def _fixed_delta(interval_unit: str, interval_value: int) -> timedelta:
    if interval_unit == IntervalUnit.SECOND.value:
        return timedelta(seconds=interval_value)
    if interval_unit == IntervalUnit.MINUTE.value:
        return timedelta(minutes=interval_value)
    if interval_unit == IntervalUnit.HOUR.value:
        return timedelta(hours=interval_value)
    if interval_unit == IntervalUnit.DAY.value:
        return timedelta(days=interval_value)
    if interval_unit == IntervalUnit.WEEK.value:
        return timedelta(weeks=interval_value)
    raise ValueError(f"Unsupported fixed interval unit: {interval_unit}")
