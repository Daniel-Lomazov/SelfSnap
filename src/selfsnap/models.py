from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time
from enum import StrEnum
import re
from typing import Any


SCHEMA_VERSION = 3
SCHEDULE_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")
LOCAL_TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$")
LEGACY_LOCAL_TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class SelfSnapError(Exception):
    """Base exception for application-level failures."""


class ConfigValidationError(SelfSnapError):
    """Raised when configuration data is malformed."""


class CaptureBackendError(SelfSnapError):
    """Raised when the capture backend cannot produce an image."""


class TriggerSource(StrEnum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    RECONCILE = "reconcile"


class OutcomeCategory(StrEnum):
    SUCCESS = "success"
    MISSED = "missed"
    SKIPPED = "skipped"
    FAILED = "failed"


class OutcomeCode(StrEnum):
    CAPTURE_SAVED = "capture_saved"
    SLOT_MISSED_NO_ATTEMPT = "slot_missed_no_attempt"
    SCHEDULED_DISABLED = "scheduled_disabled"
    CAPTURE_BACKEND_ERROR = "capture_backend_error"
    IMAGE_WRITE_ERROR = "image_write_error"
    DB_WRITE_ERROR = "db_write_error"
    CONFIG_INVALID = "config_invalid"
    SCHEDULER_SYNC_ERROR = "scheduler_sync_error"
    UNEXPECTED_ERROR = "unexpected_error"


class StoragePreset(StrEnum):
    LOCAL_PICTURES = "local_pictures"
    ONEDRIVE_PICTURES = "onedrive_pictures"
    CUSTOM = "custom"


class IntervalUnit(StrEnum):
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class CaptureMode(StrEnum):
    COMPOSITE = "composite"
    PER_MONITOR = "per_monitor"


class ImageFormat(StrEnum):
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"


def normalize_time_string(value: str) -> str:
    value = value.strip()
    if LOCAL_TIME_PATTERN.match(value):
        return value
    if LEGACY_LOCAL_TIME_PATTERN.match(value):
        return f"{value}:00"
    raise ConfigValidationError("start_time_local must be in HH:MM:SS 24-hour format")


@dataclass(slots=True)
class Schedule:
    schedule_id: str
    label: str
    interval_value: int
    interval_unit: str
    start_date_local: str
    start_time_local: str
    enabled: bool = True

    def validate(self) -> None:
        if not self.schedule_id or not SCHEDULE_ID_PATTERN.match(self.schedule_id):
            msg = "schedule_id must contain only lowercase a-z, 0-9, and underscores"
            raise ConfigValidationError(msg)
        if not self.label.strip():
            raise ConfigValidationError("label must not be empty")
        if self.interval_value < 1:
            raise ConfigValidationError("interval_value must be >= 1")
        if self.interval_unit not in {item.value for item in IntervalUnit}:
            raise ConfigValidationError(
                "interval_unit must be second, minute, hour, day, week, month, or year"
            )
        try:
            date.fromisoformat(self.start_date_local)
        except ValueError as exc:
            raise ConfigValidationError("start_date_local must be in YYYY-MM-DD format") from exc
        try:
            time.fromisoformat(normalize_time_string(self.start_time_local))
        except ValueError as exc:
            raise ConfigValidationError("start_time_local must be in HH:MM:SS format") from exc

    @property
    def normalized_start_time_local(self) -> str:
        return normalize_time_string(self.start_time_local)

    @classmethod
    def _from_legacy_dict(cls, data: dict[str, Any]) -> "Schedule":
        local_time = normalize_time_string(str(data["local_time"]))
        schedule = cls(
            schedule_id=str(data["schedule_id"]),
            label=str(data["label"]),
            interval_value=1,
            interval_unit=IntervalUnit.DAY.value,
            start_date_local=date.today().isoformat(),
            start_time_local=local_time,
            enabled=bool(data.get("enabled", True)),
        )
        schedule.validate()
        return schedule

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Schedule":
        if "interval_unit" not in data:
            return cls._from_legacy_dict(data)
        schedule = cls(
            schedule_id=str(data["schedule_id"]),
            label=str(data["label"]),
            interval_value=int(data.get("interval_value", 1)),
            interval_unit=str(data["interval_unit"]),
            start_date_local=str(data["start_date_local"]),
            start_time_local=normalize_time_string(str(data["start_time_local"])),
            enabled=bool(data.get("enabled", True)),
        )
        schedule.validate()
        return schedule

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["start_time_local"] = self.normalized_start_time_local
        return payload


@dataclass(slots=True)
class AppConfig:
    schema_version: int = SCHEMA_VERSION
    app_enabled: bool = False
    first_run_completed: bool = False
    storage_preset: str = StoragePreset.LOCAL_PICTURES.value
    capture_storage_root: str = ""
    archive_storage_root: str = ""
    retention_mode: str = "keep_forever"
    retention_days: int | None = None
    purge_enabled: bool = False
    retention_grace_days: int = 30
    start_tray_on_login: bool = True
    log_level: str = "INFO"
    show_last_capture_status: bool = True
    notify_on_failed_or_missed: bool = True
    notify_on_every_capture: bool = False
    show_capture_overlay: bool = False
    wake_for_scheduled_captures: bool = False
    scheduler_sync_state: str = "ok"
    scheduler_sync_message: str | None = None
    settings_window_width: int = 960
    settings_window_height: int = 760
    slot_match_tolerance_seconds: int = 120
    capture_mode: str = CaptureMode.COMPOSITE.value
    image_format: str = ImageFormat.PNG.value
    image_quality: int = 85
    schedules: list[Schedule] = field(default_factory=list)

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ConfigValidationError(
                f"schema_version must be {SCHEMA_VERSION}, got {self.schema_version}"
            )
        if not self.capture_storage_root.strip():
            raise ConfigValidationError("capture_storage_root must not be empty")
        if not self.archive_storage_root.strip():
            raise ConfigValidationError("archive_storage_root must not be empty")
        if self.storage_preset not in {item.value for item in StoragePreset}:
            raise ConfigValidationError(
                "storage_preset must be local_pictures, onedrive_pictures, or custom"
            )
        if self.retention_mode not in {"keep_forever", "keep_days"}:
            raise ConfigValidationError("retention_mode must be keep_forever or keep_days")
        if self.retention_mode == "keep_days":
            if self.retention_days is None or self.retention_days < 1:
                raise ConfigValidationError("retention_days must be >= 1 when retention_mode is keep_days")
        elif self.retention_days is not None and self.retention_days < 1:
            raise ConfigValidationError("retention_days must be >= 1 when supplied")
        if self.log_level not in {"INFO", "DEBUG"}:
            raise ConfigValidationError("log_level must be INFO or DEBUG")
        if self.scheduler_sync_state not in {"ok", "failed"}:
            raise ConfigValidationError("scheduler_sync_state must be ok or failed")
        if self.settings_window_width < 960:
            raise ConfigValidationError("settings_window_width must be >= 960")
        if self.settings_window_height < 760:
            raise ConfigValidationError("settings_window_height must be >= 760")
        if self.slot_match_tolerance_seconds < 0:
            raise ConfigValidationError("slot_match_tolerance_seconds must be >= 0")
        if self.capture_mode not in {item.value for item in CaptureMode}:
            raise ConfigValidationError("capture_mode must be composite or per_monitor")
        if self.image_format not in {item.value for item in ImageFormat}:
            raise ConfigValidationError("image_format must be png, jpeg, or webp")
        if not 1 <= self.image_quality <= 100:
            raise ConfigValidationError("image_quality must be between 1 and 100")
        if self.retention_grace_days < 1:
            raise ConfigValidationError("retention_grace_days must be >= 1")
        seen_ids: set[str] = set()
        for schedule in self.schedules:
            schedule.validate()
            if schedule.schedule_id in seen_ids:
                raise ConfigValidationError(f"duplicate schedule_id: {schedule.schedule_id}")
            seen_ids.add(schedule.schedule_id)

    def get_schedule(self, schedule_id: str) -> Schedule | None:
        for schedule in self.schedules:
            if schedule.schedule_id == schedule_id:
                return schedule
        return None

    def scheduler_sync_failed(self) -> bool:
        return self.scheduler_sync_state == "failed"

    def mark_scheduler_sync_failed(self, message: str) -> None:
        self.scheduler_sync_state = "failed"
        self.scheduler_sync_message = message

    def mark_scheduler_sync_ok(self) -> None:
        self.scheduler_sync_state = "ok"
        self.scheduler_sync_message = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        raw_schema_version = int(data.get("schema_version", SCHEMA_VERSION))
        if raw_schema_version not in {1, 2, SCHEMA_VERSION}:
            raise ConfigValidationError(
                f"schema_version must be 1, 2, or {SCHEMA_VERSION}, got {raw_schema_version}"
            )

        config = cls(
            schema_version=SCHEMA_VERSION,
            app_enabled=bool(data.get("app_enabled", False)),
            first_run_completed=bool(data.get("first_run_completed", False)),
            storage_preset=str(data.get("storage_preset", StoragePreset.LOCAL_PICTURES.value)),
            capture_storage_root=str(data.get("capture_storage_root", "")),
            archive_storage_root=str(data.get("archive_storage_root", "")),
            retention_mode=str(data.get("retention_mode", "keep_forever")),
            retention_days=data.get("retention_days"),
            purge_enabled=bool(data.get("purge_enabled", False)),
            retention_grace_days=int(data.get("retention_grace_days", 30)),
            start_tray_on_login=bool(data.get("start_tray_on_login", True)),
            log_level=str(data.get("log_level", "INFO")),
            show_last_capture_status=bool(data.get("show_last_capture_status", True)),
            notify_on_failed_or_missed=bool(data.get("notify_on_failed_or_missed", True)),
            notify_on_every_capture=bool(data.get("notify_on_every_capture", False)),
            show_capture_overlay=bool(data.get("show_capture_overlay", False)),
            wake_for_scheduled_captures=bool(data.get("wake_for_scheduled_captures", False)),
            scheduler_sync_state=str(data.get("scheduler_sync_state", "ok")),
            scheduler_sync_message=data.get("scheduler_sync_message"),
            settings_window_width=int(data.get("settings_window_width", 960)),
            settings_window_height=int(data.get("settings_window_height", 760)),
            slot_match_tolerance_seconds=int(data.get("slot_match_tolerance_seconds", 120)),
            capture_mode=str(data.get("capture_mode", CaptureMode.COMPOSITE.value)),
            image_format=str(data.get("image_format", ImageFormat.PNG.value)),
            image_quality=int(data.get("image_quality", 85)),
            schedules=[Schedule.from_dict(item) for item in data.get("schedules", [])],
        )
        config.validate()
        return config

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["schedules"] = [schedule.to_dict() for schedule in self.schedules]
        return payload


@dataclass(slots=True)
class CaptureRecord:
    record_id: str
    trigger_source: str
    schedule_id: str | None
    planned_local_ts: str | None
    started_utc: str | None
    finished_utc: str | None
    outcome_category: str
    outcome_code: str
    image_path: str | None
    file_present: bool
    image_sha256: str | None
    monitor_count: int | None
    composite_width: int | None
    composite_height: int | None
    file_bytes: int | None
    error_code: str | None
    error_message: str | None
    archived: bool
    archived_at_utc: str | None
    retention_deleted_at_utc: str | None
    app_version: str
    created_utc: str
    purged_utc: str | None = None

    def to_db_tuple(self) -> tuple[Any, ...]:
        return (
            self.record_id,
            self.trigger_source,
            self.schedule_id,
            self.planned_local_ts,
            self.started_utc,
            self.finished_utc,
            self.outcome_category,
            self.outcome_code,
            self.image_path,
            1 if self.file_present else 0,
            self.image_sha256,
            self.monitor_count,
            self.composite_width,
            self.composite_height,
            self.file_bytes,
            self.error_code,
            self.error_message,
            1 if self.archived else 0,
            self.archived_at_utc,
            self.retention_deleted_at_utc,
            self.purged_utc,
            self.app_version,
            self.created_utc,
        )

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "CaptureRecord":
        return cls(
            record_id=row["record_id"],
            trigger_source=row["trigger_source"],
            schedule_id=row["schedule_id"],
            planned_local_ts=row["planned_local_ts"],
            started_utc=row["started_utc"],
            finished_utc=row["finished_utc"],
            outcome_category=row["outcome_category"],
            outcome_code=row["outcome_code"],
            image_path=row["image_path"],
            file_present=bool(row["file_present"]),
            image_sha256=row["image_sha256"],
            monitor_count=row["monitor_count"],
            composite_width=row["composite_width"],
            composite_height=row["composite_height"],
            file_bytes=row["file_bytes"],
            error_code=row["error_code"],
            error_message=row["error_message"],
            archived=bool(row["archived"]),
            archived_at_utc=row["archived_at_utc"],
            retention_deleted_at_utc=row["retention_deleted_at_utc"],
            purged_utc=row.get("purged_utc"),
            app_version=row["app_version"],
            created_utc=row["created_utc"],
        )
