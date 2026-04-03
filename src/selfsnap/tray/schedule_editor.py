from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from uuid import uuid4

from selfsnap.models import ConfigValidationError, Schedule

_UNIT_LABELS = {
    "second": "Seconds",
    "minute": "Minutes",
    "hour": "Hours",
    "day": "Days",
    "week": "Weeks",
    "month": "Months",
    "year": "Years",
}
_UNIT_LABEL_TO_VALUE = {label: value for value, label in _UNIT_LABELS.items()}


@dataclass(slots=True)
class RecurringScheduleDraft:
    label: str
    enabled: bool
    interval_value: int
    interval_unit: str
    start_date_local: date
    start_time_local: time
    schedule_id: str | None = None


@dataclass(slots=True)
class EditorControlState:
    mode: str
    add_enabled: bool
    save_enabled: bool
    cancel_enabled: bool
    delete_enabled: bool
    fields_enabled: bool


def schedule_help_text() -> str:
    return (
        "Add schedules as Every N seconds, minutes, hours, days, weeks, months, or years. "
        "The start date and start time anchor the recurrence. Defaults are Every 1 day, today, "
        "and now. Select one row to edit it in place, select many rows to delete only, click "
        "the On/Off column to toggle quickly, recent runs refresh every 5 seconds for a single "
        "selected schedule, and note that month/year schedules skip invalid dates instead of "
        "rolling to the last day."
    )


def first_run_schedule_help_text() -> str:
    return (
        "You can add recurring captures later in Settings > Schedules using Every N seconds, "
        "minutes, hours, days, weeks, months, or years. Defaults are Every 1 day, today, and now."
    )


def unit_labels() -> list[str]:
    return list(_UNIT_LABELS.values())


def default_unit_label() -> str:
    return unit_label("day")


def unit_value(label: str) -> str:
    try:
        return _UNIT_LABEL_TO_VALUE[label]
    except KeyError as exc:
        raise ConfigValidationError(f"Unsupported interval unit label: {label}") from exc


def unit_label(value: str) -> str:
    try:
        return _UNIT_LABELS[value]
    except KeyError as exc:
        raise ConfigValidationError(f"Unsupported interval unit: {value}") from exc


def summary_text(draft: RecurringScheduleDraft) -> str:
    normalized = normalize_draft(draft)
    interval_text = unit_phrase(normalized.interval_value, normalized.interval_unit)
    recurrence = f"Every {normalized.interval_value} {interval_text}"
    status = "enabled" if normalized.enabled else "disabled"
    return (
        f"{normalized.label} | {recurrence} "
        f"starting {format_date_text(normalized.start_date_local)} "
        f"at {format_time_text(normalized.start_time_local)} | {status}"
    )


def default_draft(now: datetime | None = None) -> RecurringScheduleDraft:
    current = _local_now(now)
    return RecurringScheduleDraft(
        label="New Schedule",
        enabled=True,
        interval_value=1,
        interval_unit="day",
        start_date_local=current.date(),
        start_time_local=current.time().replace(microsecond=0),
    )


def draft_from_schedule(schedule: Schedule, now: datetime | None = None) -> RecurringScheduleDraft:
    fallback_now = _local_now(now)
    start_date_text = str(getattr(schedule, "start_date_local", fallback_now.date().isoformat()))
    start_time_text = str(
        getattr(
            schedule,
            "start_time_local",
            getattr(
                schedule,
                "local_time",
                fallback_now.time().replace(microsecond=0).strftime("%H:%M:%S"),
            ),
        )
    )
    return RecurringScheduleDraft(
        label=schedule.label,
        enabled=schedule.enabled,
        interval_value=int(getattr(schedule, "interval_value", 1)),
        interval_unit=str(getattr(schedule, "interval_unit", "day")),
        start_date_local=parse_date_text(start_date_text),
        start_time_local=parse_time_text(start_time_text),
        schedule_id=getattr(schedule, "schedule_id", None),
    )


def draft_to_schedule(draft: RecurringScheduleDraft) -> Schedule:
    normalized = normalize_draft(draft)
    schedule_id = normalized.schedule_id or generate_schedule_id()
    return Schedule(
        schedule_id=schedule_id,
        label=normalized.label,
        interval_value=normalized.interval_value,
        interval_unit=normalized.interval_unit,
        start_date_local=format_date_text(normalized.start_date_local),
        start_time_local=format_time_text(normalized.start_time_local),
        enabled=normalized.enabled,
    )


def normalize_draft(draft: RecurringScheduleDraft) -> RecurringScheduleDraft:
    if not draft.label.strip():
        raise ConfigValidationError("label must not be empty")
    if draft.interval_value < 1:
        raise ConfigValidationError("interval_value must be >= 1")
    if draft.interval_unit not in _UNIT_LABELS:
        raise ConfigValidationError("Unsupported interval unit")
    return RecurringScheduleDraft(
        label=draft.label.strip(),
        enabled=bool(draft.enabled),
        interval_value=int(draft.interval_value),
        interval_unit=draft.interval_unit,
        start_date_local=draft.start_date_local,
        start_time_local=draft.start_time_local.replace(microsecond=0),
        schedule_id=draft.schedule_id,
    )


def selection_state(selection_count: int) -> EditorControlState:
    if selection_count <= 0:
        return EditorControlState(
            mode="add",
            add_enabled=True,
            save_enabled=False,
            cancel_enabled=False,
            delete_enabled=False,
            fields_enabled=True,
        )
    if selection_count == 1:
        return EditorControlState(
            mode="single",
            add_enabled=False,
            save_enabled=True,
            cancel_enabled=True,
            delete_enabled=True,
            fields_enabled=True,
        )
    return EditorControlState(
        mode="multi",
        add_enabled=False,
        save_enabled=False,
        cancel_enabled=False,
        delete_enabled=True,
        fields_enabled=False,
    )


def schedule_inventory_text(drafts: list[RecurringScheduleDraft]) -> str:
    total = len(drafts)
    if total == 0:
        return "0 schedules | no recurring captures configured"
    enabled = sum(1 for draft in drafts if draft.enabled)
    disabled = total - enabled
    parts = [
        f"{total} {'schedule' if total == 1 else 'schedules'}",
        f"{enabled} enabled",
    ]
    if disabled:
        parts.append(f"{disabled} disabled")
    return " | ".join(parts)


def schedule_selection_guidance(selection_count: int) -> str:
    if selection_count <= 0:
        return (
            "Add a schedule, or select one row to edit in place. Click the On/Off column to "
            "toggle a schedule without opening the editor."
        )
    if selection_count == 1:
        return (
            "Editing one schedule. Save commits field changes, Cancel restores the form, and "
            "Recent Runs refreshes automatically while this row stays selected."
        )
    return (
        "Bulk selection is active. Delete stays available, while field editing remains locked "
        "until one row remains selected."
    )


def parse_int_text(value: str) -> int:
    try:
        parsed = int(value.strip())
    except ValueError as exc:
        raise ConfigValidationError("Every N must be a whole number") from exc
    if parsed < 1:
        raise ConfigValidationError("Every N must be >= 1")
    return parsed


def parse_date_text(value: str) -> date:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise ConfigValidationError("Start date must be YYYY-MM-DD") from exc


def parse_time_text(value: str) -> time:
    text = value.strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(text, fmt).time().replace(microsecond=0)
        except ValueError:
            continue
    raise ConfigValidationError("Start time must be HH:MM or HH:MM:SS")


def format_date_text(value: date) -> str:
    return value.isoformat()


def format_time_text(value: time) -> str:
    return value.replace(microsecond=0).strftime("%H:%M:%S")


def format_time_compact(value: time) -> str:
    return value.replace(microsecond=0).strftime("%H:%M")


def draft_from_form(
    label: str,
    interval_value: str,
    unit_label_value: str,
    start_date: str,
    start_time: str,
    enabled: bool,
    schedule_id: str | None = None,
) -> RecurringScheduleDraft:
    return normalize_draft(
        RecurringScheduleDraft(
            label=label,
            enabled=enabled,
            interval_value=parse_int_text(interval_value),
            interval_unit=unit_value(unit_label_value),
            start_date_local=parse_date_text(start_date),
            start_time_local=parse_time_text(start_time),
            schedule_id=schedule_id,
        )
    )


def unit_phrase(interval_value: int, interval_unit: str) -> str:
    base = interval_unit
    if interval_value == 1:
        return base
    return f"{base}s"


def generate_schedule_id() -> str:
    return f"sched_{uuid4().hex[:12]}"


def _local_now(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now().astimezone()
    if now.tzinfo is None:
        return now.astimezone()
    return now.astimezone()
