from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, replace
from tkinter import filedialog, messagebox, ttk

from selfsnap.config_store import save_config
from selfsnap.db import connect, ensure_database
from selfsnap.models import AppConfig, CaptureRecord, ConfigValidationError, StoragePreset
from selfsnap.paths import AppPaths
from selfsnap.records import get_latest_record
from selfsnap.storage import apply_storage_preset, validate_storage_config
from selfsnap.tray.diagnostics import (
    DiagnosticSummary,
    format_local_timestamp,
    last_activity_summary,
    notification_summary,
    operational_summary,
    retention_summary,
    scheduler_sync_summary,
    storage_summary,
)
from selfsnap.tray.schedule_editor import (
    RecurringScheduleDraft,
    default_draft,
    default_unit_label,
    draft_from_form,
    draft_from_schedule,
    draft_to_schedule,
    format_date_text,
    format_time_text,
    schedule_help_text,
    schedule_inventory_text,
    schedule_selection_guidance,
    selection_state,
    unit_label,
    unit_labels,
    unit_phrase,
)
from selfsnap.tray.ui_helpers import (
    bind_card_wrap,
    bind_wrap,
    create_diagnostic_card,
    set_diagnostic_card_content,
)
from selfsnap.ui_labels import (
    local_privacy_notice,
    retention_mode_label,
    retention_mode_labels,
    retention_mode_value,
    storage_preset_label,
    storage_preset_labels,
    storage_preset_value,
)

WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 760
HISTORY_REFRESH_INTERVAL_MS = 5000


@dataclass(slots=True)
class SettingsDialogResult:
    updated_config: AppConfig | None
    window_size: tuple[int, int]
    requested_reset: bool = False


def show_settings_dialog(config: AppConfig, paths: AppPaths) -> SettingsDialogResult:
    root = tk.Tk()
    root.title("SelfSnap Settings")
    root.update_idletasks()
    root.geometry(
        f"{max(config.settings_window_width, WINDOW_MIN_WIDTH)}x"
        f"{max(config.settings_window_height, WINDOW_MIN_HEIGHT)}"
    )
    root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
    root.resizable(True, True)

    preset_var = tk.StringVar(master=root, value=storage_preset_label(config.storage_preset))
    capture_root_var = tk.StringVar(master=root, value=config.capture_storage_root)
    archive_root_var = tk.StringVar(master=root, value=config.archive_storage_root)
    retention_mode_var = tk.StringVar(
        master=root, value=retention_mode_label(config.retention_mode)
    )
    retention_days_var = tk.StringVar(
        master=root, value="" if config.retention_days is None else str(config.retention_days)
    )
    capture_mode_var = tk.StringVar(
        master=root, value="Per Monitor" if config.capture_mode == "per_monitor" else "Composite"
    )
    image_format_var = tk.StringVar(master=root, value=config.image_format.upper())
    image_quality_var = tk.StringVar(master=root, value=str(config.image_quality))
    purge_enabled_var = tk.BooleanVar(master=root, value=config.purge_enabled)
    retention_grace_days_var = tk.StringVar(master=root, value=str(config.retention_grace_days))
    start_tray_on_login_var = tk.BooleanVar(master=root, value=config.start_tray_on_login)
    wake_for_scheduled_captures_var = tk.BooleanVar(
        master=root, value=config.wake_for_scheduled_captures
    )
    show_last_capture_status_var = tk.BooleanVar(master=root, value=config.show_last_capture_status)
    notify_on_failed_or_missed_var = tk.BooleanVar(
        master=root, value=config.notify_on_failed_or_missed
    )
    notify_on_every_capture_var = tk.BooleanVar(master=root, value=config.notify_on_every_capture)
    show_capture_overlay_var = tk.BooleanVar(master=root, value=config.show_capture_overlay)
    internal_preset_update = {"active": False}
    drafts: list[RecurringScheduleDraft] = [
        draft_from_schedule(schedule) for schedule in config.schedules
    ]
    selected_indices: list[int] = []
    history_refresh_job: str | None = None

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    container = ttk.Frame(root, padding=(0, 0, 0, 0))
    container.grid(row=0, column=0, sticky="nsew")
    container.columnconfigure(0, weight=1)
    container.rowconfigure(0, weight=1)

    canvas = tk.Canvas(container, highlightthickness=0)
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    canvas.configure(yscrollcommand=scrollbar.set)

    content = ttk.Frame(canvas, padding=10)
    content.columnconfigure(0, weight=1)
    canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")

    def _sync_canvas(_event=None) -> None:
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfigure(canvas_window, width=canvas.winfo_width())

    content.bind("<Configure>", _sync_canvas)
    canvas.bind("<Configure>", _sync_canvas)

    def _set_preset_from_label(selected_label: str) -> None:
        internal_preset_update["active"] = True
        try:
            preset = storage_preset_value(selected_label)
            preset_config = apply_storage_preset(paths, config, preset)
            preset_var.set(storage_preset_label(preset))
            capture_root_var.set(preset_config.capture_storage_root)
            archive_root_var.set(preset_config.archive_storage_root)
        finally:
            internal_preset_update["active"] = False
        _update_path_state()

    def _mark_custom(*_args) -> None:
        if internal_preset_update["active"]:
            return
        if preset_var.get() != storage_preset_label(StoragePreset.CUSTOM.value):
            preset_var.set(storage_preset_label(StoragePreset.CUSTOM.value))

    def _update_path_state() -> None:
        capture_entry.configure(state="normal")
        archive_entry.configure(state="normal")
        capture_browse.configure(state="normal")
        archive_browse.configure(state="normal")

    capture_root_var.trace_add("write", _mark_custom)
    archive_root_var.trace_add("write", _mark_custom)

    def _load_latest_record() -> CaptureRecord | None:
        if not paths.db_path.exists():
            return None
        try:
            ensure_database(paths.db_path)
            with connect(paths.db_path) as connection:
                return get_latest_record(connection)
        except Exception:
            return None

    latest_record = _load_latest_record()

    row = 0
    trust_label = ttk.Label(content, text=local_privacy_notice(), justify="left")
    trust_label.grid(row=row, column=0, sticky="ew", pady=(0, 8))
    bind_wrap(content, root, trust_label)
    row += 1

    overview_frame = ttk.LabelFrame(content, text="Diagnostics Overview", padding=10)
    overview_frame.grid(row=row, column=0, sticky="ew")
    overview_frame.columnconfigure(0, weight=1)
    overview_frame.columnconfigure(1, weight=1)
    row += 1

    scheduler_card = create_diagnostic_card(overview_frame, "Scheduler Sync")
    scheduler_card.frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
    last_activity_card = create_diagnostic_card(overview_frame, "Last Activity")
    last_activity_card.frame.grid(row=0, column=1, sticky="nsew", pady=(0, 8))
    storage_card = create_diagnostic_card(overview_frame, "Storage")
    storage_card.frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
    retention_card = create_diagnostic_card(overview_frame, "Retention")
    retention_card.frame.grid(row=1, column=1, sticky="nsew", pady=(0, 8))
    notification_card = create_diagnostic_card(overview_frame, "Notifications")
    notification_card.frame.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
    operational_card = create_diagnostic_card(overview_frame, "Operational Context")
    operational_card.frame.grid(row=2, column=1, sticky="nsew")
    for card in (
        scheduler_card,
        last_activity_card,
        storage_card,
        retention_card,
        notification_card,
        operational_card,
    ):
        bind_card_wrap(card, root)

    def _safe_int(value: str, fallback: int) -> int:
        stripped = value.strip()
        if not stripped:
            return fallback
        try:
            return int(stripped)
        except ValueError:
            return fallback

    def _selected_storage_preset() -> str:
        try:
            return storage_preset_value(preset_var.get().strip())
        except ConfigValidationError:
            return config.storage_preset

    def _selected_retention_mode() -> str:
        try:
            return retention_mode_value(retention_mode_var.get())
        except ConfigValidationError:
            return config.retention_mode

    def _preview_config() -> AppConfig:
        retention_mode = _selected_retention_mode()
        retention_days = None
        if retention_mode == "keep_days":
            fallback_days = config.retention_days if config.retention_days is not None else 1
            retention_days = _safe_int(retention_days_var.get(), fallback_days)
        image_format = image_format_var.get().strip().lower()
        if image_format not in {"png", "jpeg", "webp"}:
            image_format = config.image_format
        return replace(
            config,
            storage_preset=_selected_storage_preset(),
            capture_storage_root=capture_root_var.get().strip(),
            archive_storage_root=archive_root_var.get().strip(),
            retention_mode=retention_mode,
            retention_days=retention_days,
            purge_enabled=purge_enabled_var.get(),
            retention_grace_days=_safe_int(
                retention_grace_days_var.get(), config.retention_grace_days
            ),
            capture_mode="per_monitor" if capture_mode_var.get() == "Per Monitor" else "composite",
            image_format=image_format,
            image_quality=_safe_int(image_quality_var.get(), config.image_quality),
            start_tray_on_login=start_tray_on_login_var.get(),
            wake_for_scheduled_captures=wake_for_scheduled_captures_var.get(),
            show_last_capture_status=show_last_capture_status_var.get(),
            notify_on_failed_or_missed=notify_on_failed_or_missed_var.get(),
            notify_on_every_capture=notify_on_every_capture_var.get(),
            show_capture_overlay=show_capture_overlay_var.get(),
        )

    def _set_card(card, summary: DiagnosticSummary) -> None:
        set_diagnostic_card_content(
            card,
            headline=summary.headline,
            detail=summary.detail,
            tone=summary.tone,
        )

    def _refresh_overview(*_args) -> None:
        preview = _preview_config()
        _set_card(scheduler_card, scheduler_sync_summary(preview))
        _set_card(last_activity_card, last_activity_summary(latest_record))
        for card, builder in (
            (storage_card, lambda: storage_summary(preview, paths)),
            (retention_card, lambda: retention_summary(preview)),
            (notification_card, lambda: notification_summary(preview)),
            (operational_card, lambda: operational_summary(preview, paths)),
        ):
            try:
                summary = builder()
            except (ConfigValidationError, ValueError) as exc:
                summary = DiagnosticSummary(
                    headline="Pending validation",
                    detail=str(exc),
                    tone="warn",
                )
            _set_card(card, summary)

    storage_frame = ttk.LabelFrame(content, text="Storage and Capture", padding=10)
    storage_frame.grid(row=row, column=0, sticky="ew")
    storage_frame.columnconfigure(1, weight=1)
    row += 1

    ttk.Label(storage_frame, text="Storage Preset").grid(row=0, column=0, sticky="w", pady=(0, 6))
    preset_combo = ttk.Combobox(
        storage_frame,
        textvariable=preset_var,
        state="readonly",
        values=storage_preset_labels(),
        width=24,
    )
    preset_combo.grid(row=0, column=1, sticky="ew", pady=(0, 6))

    ttk.Label(storage_frame, text="Capture Storage Root").grid(
        row=1, column=0, sticky="w", pady=(0, 6)
    )
    capture_entry = ttk.Entry(storage_frame, textvariable=capture_root_var)
    capture_entry.grid(row=1, column=1, sticky="ew", pady=(0, 6))
    capture_browse = ttk.Button(
        storage_frame,
        text="Browse",
        command=lambda: _browse_directory(root, capture_root_var),
    )
    capture_browse.grid(row=1, column=2, sticky="w", padx=(6, 0), pady=(0, 6))

    ttk.Label(storage_frame, text="Archive Storage Root").grid(
        row=2, column=0, sticky="w", pady=(0, 6)
    )
    archive_entry = ttk.Entry(storage_frame, textvariable=archive_root_var)
    archive_entry.grid(row=2, column=1, sticky="ew", pady=(0, 6))
    archive_browse = ttk.Button(
        storage_frame,
        text="Browse",
        command=lambda: _browse_directory(root, archive_root_var),
    )
    archive_browse.grid(row=2, column=2, sticky="w", padx=(6, 0), pady=(0, 6))

    ttk.Label(storage_frame, text="Retention Mode").grid(row=3, column=0, sticky="w")
    ttk.Combobox(
        storage_frame,
        textvariable=retention_mode_var,
        values=retention_mode_labels(),
        width=18,
        state="readonly",
    ).grid(row=3, column=1, sticky="ew")
    ttk.Label(storage_frame, text="Archive After Days").grid(
        row=3, column=2, sticky="w", padx=(10, 0)
    )
    ttk.Entry(storage_frame, textvariable=retention_days_var, width=8).grid(
        row=3, column=3, sticky="w"
    )

    ttk.Label(storage_frame, text="Capture Mode").grid(row=5, column=0, sticky="w", pady=(4, 0))
    ttk.Combobox(
        storage_frame,
        textvariable=capture_mode_var,
        values=["Composite", "Per Monitor"],
        state="readonly",
        width=18,
    ).grid(row=5, column=1, sticky="ew", pady=(4, 0))

    ttk.Label(storage_frame, text="Image Format").grid(row=6, column=0, sticky="w", pady=(4, 0))
    ttk.Combobox(
        storage_frame,
        textvariable=image_format_var,
        values=["PNG", "JPEG", "WEBP"],
        state="readonly",
        width=12,
    ).grid(row=6, column=1, sticky="ew", pady=(4, 0))
    ttk.Label(storage_frame, text="Quality (JPEG/WebP)").grid(
        row=6, column=2, sticky="w", padx=(10, 0), pady=(4, 0)
    )
    ttk.Entry(storage_frame, textvariable=image_quality_var, width=8).grid(
        row=6, column=3, sticky="w", pady=(4, 0)
    )

    ttk.Checkbutton(
        storage_frame,
        text="Permanently delete after grace period",
        variable=purge_enabled_var,
    ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 0))
    ttk.Label(storage_frame, text="Grace Days").grid(
        row=4, column=2, sticky="w", padx=(10, 0), pady=(4, 0)
    )
    ttk.Entry(storage_frame, textvariable=retention_grace_days_var, width=8).grid(
        row=4, column=3, sticky="w", pady=(4, 0)
    )

    schedules_frame = ttk.LabelFrame(content, text="Schedules and Recent Runs", padding=10)
    schedules_frame.grid(row=row, column=0, sticky="ew", pady=(8, 0))
    schedules_frame.columnconfigure(0, weight=1)
    row += 1

    schedule_help_label = ttk.Label(schedules_frame, text=schedule_help_text(), justify="left")
    schedule_help_label.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    bind_wrap(schedules_frame, root, schedule_help_label, padding=56)

    schedule_inventory_var = tk.StringVar(master=root, value="")
    schedule_selection_var = tk.StringVar(master=root, value="")
    schedule_inventory_label = ttk.Label(
        schedules_frame,
        textvariable=schedule_inventory_var,
        justify="left",
        font=("Segoe UI", 10, "bold"),
    )
    schedule_inventory_label.grid(row=1, column=0, sticky="ew")
    schedule_selection_label = ttk.Label(
        schedules_frame,
        textvariable=schedule_selection_var,
        justify="left",
    )
    schedule_selection_label.grid(row=2, column=0, sticky="ew", pady=(4, 8))
    bind_wrap(schedules_frame, root, schedule_selection_label, padding=56)

    schedules_body = ttk.Frame(schedules_frame)
    schedules_body.grid(row=3, column=0, sticky="nsew")
    schedules_body.columnconfigure(0, weight=1)
    schedules_body.columnconfigure(1, weight=1)
    schedules_frame.rowconfigure(3, weight=1)

    list_frame = ttk.LabelFrame(schedules_body, text="Existing Schedules", padding=8)
    list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    list_frame.columnconfigure(0, weight=1)
    list_frame.rowconfigure(0, weight=1)

    schedule_tree = ttk.Treeview(
        list_frame,
        columns=("label", "recurrence", "start", "enabled"),
        show="headings",
        selectmode="extended",
        height=8,
    )
    schedule_tree.heading("label", text="Label")
    schedule_tree.heading("recurrence", text="Recurrence")
    schedule_tree.heading("start", text="Start")
    schedule_tree.heading("enabled", text="On/Off")
    schedule_tree.column("label", width=170, anchor="w", stretch=True)
    schedule_tree.column("recurrence", width=220, anchor="w", stretch=True)
    schedule_tree.column("start", width=170, anchor="w", stretch=True)
    schedule_tree.column("enabled", width=72, anchor="center", stretch=False)
    schedule_tree.grid(row=0, column=0, sticky="nsew")
    tree_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=schedule_tree.yview)
    tree_scrollbar.grid(row=0, column=1, sticky="ns")
    schedule_tree.configure(yscrollcommand=tree_scrollbar.set)

    editor_frame = ttk.LabelFrame(schedules_body, text="Schedule Editor", padding=8)
    editor_frame.grid(row=0, column=1, sticky="nsew")
    editor_frame.columnconfigure(1, weight=1)

    label_var = tk.StringVar(master=root, value=default_draft().label)
    every_var = tk.StringVar(master=root, value="1")
    unit_var = tk.StringVar(master=root, value=default_unit_label())
    start_date_var = tk.StringVar(
        master=root, value=format_date_text(default_draft().start_date_local)
    )
    start_time_var = tk.StringVar(
        master=root, value=format_time_text(default_draft().start_time_local)
    )
    widgets_to_toggle: list[tk.Widget] = []

    def _new_default_draft() -> RecurringScheduleDraft:
        return default_draft()

    def _draft_from_form(
        schedule_id: str | None = None, enabled: bool = True
    ) -> RecurringScheduleDraft:
        return draft_from_form(
            label=label_var.get(),
            interval_value=every_var.get(),
            unit_label_value=unit_var.get(),
            start_date=start_date_var.get(),
            start_time=start_time_var.get(),
            enabled=enabled,
            schedule_id=schedule_id,
        )

    def _selection_indices() -> list[int]:
        return sorted(int(item) for item in schedule_tree.selection())

    def _load_draft_to_form(draft: RecurringScheduleDraft) -> None:
        label_var.set(draft.label)
        every_var.set(str(draft.interval_value))
        try:
            unit_var.set(unit_label(draft.interval_unit))
        except ConfigValidationError:
            unit_var.set(default_unit_label())
        start_date_var.set(format_date_text(draft.start_date_local))
        start_time_var.set(format_time_text(draft.start_time_local))

    def _selected_mode() -> None:
        state = selection_state(len(selected_indices))
        _set_editor_state(state)

    def _set_editor_state(state) -> None:
        for widget in widgets_to_toggle:
            try:
                if isinstance(widget, ttk.Checkbutton):
                    widget.state(["!disabled"] if state.fields_enabled else ["disabled"])
                elif isinstance(widget, ttk.Combobox):
                    widget.state(["readonly"] if state.fields_enabled else ["disabled"])
                else:
                    widget.configure(state="normal" if state.fields_enabled else "disabled")
            except tk.TclError:
                continue
        add_button.state(["!disabled"] if state.add_enabled else ["disabled"])
        save_schedule_button.state(["!disabled"] if state.save_enabled else ["disabled"])
        cancel_schedule_button.state(["!disabled"] if state.cancel_enabled else ["disabled"])
        list_delete_btn.state(["!disabled"] if state.delete_enabled else ["disabled"])

    def _refresh_tree(select: list[int] | None = None) -> None:
        schedule_tree.delete(*schedule_tree.get_children())
        for index, draft in enumerate(drafts):
            recurrence_text = (
                f"Every {draft.interval_value} "
                f"{unit_phrase(draft.interval_value, draft.interval_unit)}"
            )
            start_text = (
                f"{format_date_text(draft.start_date_local)} "
                f"{format_time_text(draft.start_time_local)}"
            )
            schedule_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    draft.label,
                    recurrence_text,
                    start_text,
                    "✓" if draft.enabled else "✗",
                ),
            )
        if select:
            for index in select:
                schedule_tree.selection_add(str(index))
            schedule_tree.see(str(select[0]))
        _update_selection_from_tree()

    def _refresh_history(schedule_id: str | None) -> None:
        history_list.configure(state="normal")
        history_list.delete(0, "end")
        if schedule_id is None:
            history_list.configure(state="disabled")
            return
        try:
            from selfsnap.db import connect
            from selfsnap.records import get_by_schedule

            with connect(paths.db_path) as conn:
                records = get_by_schedule(conn, schedule_id, limit=5)
            for r in records:
                ts = format_local_timestamp(r.started_utc or r.created_utc or "")
                icon = {"success": "✓", "failed": "✗", "missed": "–", "skipped": "○"}.get(
                    r.outcome_category, "?"
                )
                history_list.insert("end", f"{icon}  {ts}  {r.outcome_code}")
        except Exception:
            history_list.insert("end", "(history unavailable)")
        finally:
            history_list.configure(state="disabled")

    def _clear_history() -> None:
        history_list.configure(state="normal")
        history_list.delete(0, "end")
        history_list.configure(state="disabled")

    def _cancel_history_poll() -> None:
        nonlocal history_refresh_job
        if history_refresh_job is not None:
            try:
                root.after_cancel(history_refresh_job)
            except tk.TclError:
                pass
            history_refresh_job = None

    def _poll_history() -> None:
        nonlocal history_refresh_job
        if len(selected_indices) == 1:
            _refresh_history(drafts[selected_indices[0]].schedule_id)
        history_refresh_job = root.after(HISTORY_REFRESH_INTERVAL_MS, _poll_history)

    def _update_selection_from_tree(_event=None) -> None:
        nonlocal selected_indices
        selected_indices = _selection_indices()
        if len(selected_indices) == 1:
            _load_draft_to_form(drafts[selected_indices[0]])
            _refresh_history(drafts[selected_indices[0]].schedule_id)
        elif len(selected_indices) == 0:
            _load_draft_to_form(_new_default_draft())
            _clear_history()
        else:
            _load_draft_to_form(drafts[selected_indices[0]])
            _clear_history()
        _selected_mode()
        _refresh_schedule_status()

    def _refresh_schedule_status() -> None:
        schedule_inventory_var.set(schedule_inventory_text(drafts))
        schedule_selection_var.set(schedule_selection_guidance(len(selected_indices)))

    def _add_schedule() -> None:
        try:
            draft = _draft_from_form(enabled=True)
        except ConfigValidationError as exc:
            messagebox.showerror("Invalid schedule", str(exc), parent=root)
            return
        drafts.append(draft)
        _refresh_tree([len(drafts) - 1])
        _load_draft_to_form(draft)

    def _save_schedule() -> None:
        if len(selected_indices) != 1:
            return
        index = selected_indices[0]
        try:
            drafts[index] = _draft_from_form(
                schedule_id=drafts[index].schedule_id, enabled=drafts[index].enabled
            )
        except ConfigValidationError as exc:
            messagebox.showerror("Invalid schedule", str(exc), parent=root)
            return
        _refresh_tree([index])
        _load_draft_to_form(drafts[index])

    def _cancel_schedule_edit() -> None:
        if len(selected_indices) == 1:
            _load_draft_to_form(drafts[selected_indices[0]])
            return
        _load_draft_to_form(_new_default_draft())

    def _delete_schedule() -> None:
        if not selected_indices:
            return
        for index in sorted(selected_indices, reverse=True):
            del drafts[index]
        if drafts:
            next_index = min(selected_indices[0], len(drafts) - 1)
            _refresh_tree([next_index])
            _load_draft_to_form(drafts[next_index])
        else:
            _refresh_tree([])
            _load_draft_to_form(_new_default_draft())

    ttk.Label(editor_frame, text="Label").grid(row=0, column=0, sticky="w", pady=(0, 6))
    label_entry = ttk.Entry(editor_frame, textvariable=label_var)
    label_entry.grid(row=0, column=1, sticky="ew", pady=(0, 6))

    ttk.Label(editor_frame, text="Every N").grid(row=1, column=0, sticky="w", pady=(0, 6))
    every_spinbox = tk.Spinbox(editor_frame, from_=1, to=999999, textvariable=every_var, width=10)
    every_spinbox.grid(row=1, column=1, sticky="w", pady=(0, 6))

    ttk.Label(editor_frame, text="Unit").grid(row=2, column=0, sticky="w", pady=(0, 6))
    unit_combo = ttk.Combobox(
        editor_frame,
        textvariable=unit_var,
        values=unit_labels(),
        state="readonly",
    )
    unit_combo.grid(row=2, column=1, sticky="ew", pady=(0, 6))

    ttk.Label(editor_frame, text="Start Date").grid(row=3, column=0, sticky="w", pady=(0, 6))
    start_date_entry = ttk.Entry(editor_frame, textvariable=start_date_var)
    start_date_entry.grid(row=3, column=1, sticky="ew", pady=(0, 6))

    ttk.Label(editor_frame, text="Start Time").grid(row=4, column=0, sticky="w", pady=(0, 6))
    start_time_entry = ttk.Entry(editor_frame, textvariable=start_time_var)
    start_time_entry.grid(row=4, column=1, sticky="ew", pady=(0, 6))

    form_buttons = ttk.Frame(editor_frame)
    form_buttons.grid(row=5, column=0, columnspan=2, sticky="ew")
    form_buttons.columnconfigure(0, weight=1)

    add_button = ttk.Button(form_buttons, text="Add", command=_add_schedule)
    save_schedule_button = ttk.Button(form_buttons, text="Save", command=_save_schedule)
    cancel_schedule_button = ttk.Button(form_buttons, text="Cancel", command=_cancel_schedule_edit)
    cancel_schedule_button.pack(side="right")
    save_schedule_button.pack(side="right", padx=(0, 8))
    add_button.pack(side="right", padx=(0, 8))

    history_frame = ttk.LabelFrame(schedules_body, text="Recent Runs", padding=6)
    history_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    history_frame.columnconfigure(0, weight=1)

    history_list = tk.Listbox(history_frame, height=5, state="disabled", selectmode="browse")
    history_list.grid(row=0, column=0, sticky="ew")

    widgets_to_toggle.extend(
        [label_entry, every_spinbox, unit_combo, start_date_entry, start_time_entry]
    )

    list_btn_bar = ttk.Frame(list_frame)
    list_btn_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
    list_delete_btn = ttk.Button(list_btn_bar, text="Delete Selected", command=_delete_schedule)
    list_delete_btn.pack(side="right")

    def _on_enabled_click(event: tk.Event) -> None:
        col = schedule_tree.identify_column(event.x)
        item = schedule_tree.identify_row(event.y)
        if col != "#4" or not item:
            return
        index = int(item)
        drafts[index].enabled = not drafts[index].enabled
        current_vals = list(schedule_tree.item(item, "values"))
        current_vals[3] = "✓" if drafts[index].enabled else "✗"
        schedule_tree.item(item, values=current_vals)
        _refresh_schedule_status()

    def _on_treeview_motion(event: tk.Event) -> None:
        col = schedule_tree.identify_column(event.x)
        schedule_tree.configure(cursor="hand2" if col == "#4" else "")

    schedule_tree.bind("<Button-1>", _on_enabled_click, add="+")
    schedule_tree.bind("<Motion>", _on_treeview_motion)
    schedule_tree.bind("<<TreeviewSelect>>", _update_selection_from_tree)
    _refresh_tree([])
    _load_draft_to_form(_new_default_draft())
    _selected_mode()
    _refresh_schedule_status()
    history_refresh_job = root.after(HISTORY_REFRESH_INTERVAL_MS, _poll_history)

    visibility_frame = ttk.LabelFrame(content, text="Tray, Notifications, and Power", padding=10)
    visibility_frame.grid(row=row, column=0, sticky="ew", pady=(8, 0))
    visibility_frame.columnconfigure(0, weight=1)
    row += 1

    ttk.Checkbutton(
        visibility_frame,
        text="Start tray on login",
        variable=start_tray_on_login_var,
    ).grid(row=0, column=0, sticky="w")
    ttk.Checkbutton(
        visibility_frame,
        text="Wake for scheduled captures when supported",
        variable=wake_for_scheduled_captures_var,
    ).grid(row=1, column=0, sticky="w")
    ttk.Checkbutton(
        visibility_frame,
        text="Show latest capture status in tray menu",
        variable=show_last_capture_status_var,
    ).grid(row=2, column=0, sticky="w")
    ttk.Checkbutton(
        visibility_frame,
        text="Notify on failed or missed captures",
        variable=notify_on_failed_or_missed_var,
    ).grid(row=3, column=0, sticky="w")
    ttk.Checkbutton(
        visibility_frame,
        text="Notify on every scheduled and manual capture",
        variable=notify_on_every_capture_var,
    ).grid(row=4, column=0, sticky="w")
    ttk.Checkbutton(
        visibility_frame,
        text="Show brief on-screen overlay after capture",
        variable=show_capture_overlay_var,
    ).grid(row=5, column=0, sticky="w")

    maintenance_frame = ttk.LabelFrame(content, text="Maintenance", padding=10)
    maintenance_frame.grid(row=row, column=0, sticky="ew", pady=(8, 0))
    maintenance_frame.columnconfigure(0, weight=1)
    row += 1

    maintenance_message = ttk.Label(
        maintenance_frame,
        text=(
            "Reset Capture History permanently deletes SelfSnap capture/archive files, "
            "database history, logs, schedules, and local user settings, then relaunches first run."
        ),
        justify="left",
        foreground="#7f1d1d",
    )
    maintenance_message.grid(row=0, column=0, sticky="ew", pady=(0, 6))
    bind_wrap(maintenance_frame, root, maintenance_message)

    result = SettingsDialogResult(
        updated_config=None,
        window_size=(config.settings_window_width, config.settings_window_height),
    )

    def _capture_size() -> tuple[int, int]:
        root.update_idletasks()
        return max(root.winfo_width(), WINDOW_MIN_WIDTH), max(
            root.winfo_height(), WINDOW_MIN_HEIGHT
        )

    def _request_reset() -> None:
        confirmed = messagebox.askyesno(
            "Reset Capture History",
            (
                "This permanently deletes SelfSnap capture files, archive files, logs, "
                "history, schedules, and user settings, then restarts into first run.\n\n"
                "This cannot be undone.\n\nContinue?"
            ),
            parent=root,
            icon="warning",
        )
        if not confirmed:
            return
        _cancel_history_poll()
        result.window_size = _capture_size()
        result.requested_reset = True
        root.destroy()

    ttk.Button(
        maintenance_frame,
        text="Reset Capture History",
        command=_request_reset,
    ).grid(row=1, column=0, sticky="w")

    action_row = ttk.Frame(root, padding=(10, 8))
    action_row.grid(row=1, column=0, sticky="ew")

    def _apply_settings() -> None:
        # Auto-commit any in-progress schedule edit before validating.
        if len(selected_indices) == 1:
            try:
                drafts[selected_indices[0]] = _draft_from_form(
                    schedule_id=drafts[selected_indices[0]].schedule_id,
                    enabled=drafts[selected_indices[0]].enabled,
                )
            except ConfigValidationError as exc:
                messagebox.showerror("Invalid schedule", str(exc), parent=root)
                return
        try:
            parsed_schedules = [draft_to_schedule(draft) for draft in drafts]
            retention_mode = retention_mode_value(retention_mode_var.get())
            retention_days = None
            if retention_mode == "keep_days":
                retention_days = int(retention_days_var.get())
            updated = replace(
                config,
                storage_preset=storage_preset_value(preset_var.get().strip()),
                capture_storage_root=capture_root_var.get().strip(),
                archive_storage_root=archive_root_var.get().strip(),
                retention_mode=retention_mode,
                retention_days=retention_days,
                purge_enabled=purge_enabled_var.get(),
                retention_grace_days=int(retention_grace_days_var.get())
                if retention_grace_days_var.get().strip().isdigit()
                else config.retention_grace_days,
                capture_mode="per_monitor"
                if capture_mode_var.get() == "Per Monitor"
                else "composite",
                image_format=image_format_var.get().lower(),
                image_quality=int(image_quality_var.get())
                if image_quality_var.get().strip().isdigit()
                else config.image_quality,
                start_tray_on_login=start_tray_on_login_var.get(),
                wake_for_scheduled_captures=wake_for_scheduled_captures_var.get(),
                show_last_capture_status=show_last_capture_status_var.get(),
                notify_on_failed_or_missed=notify_on_failed_or_missed_var.get(),
                notify_on_every_capture=notify_on_every_capture_var.get(),
                show_capture_overlay=show_capture_overlay_var.get(),
                settings_window_width=_capture_size()[0],
                settings_window_height=_capture_size()[1],
                schedules=parsed_schedules,
            )
            if updated.storage_preset != StoragePreset.CUSTOM.value:
                updated = apply_storage_preset(paths, updated, updated.storage_preset)
            else:
                validate_storage_config(paths, updated)
            updated.validate()
        except (ConfigValidationError, ValueError) as exc:
            messagebox.showerror("Invalid settings", str(exc), parent=root)
            return
        try:
            save_config(paths, updated)
        except Exception as exc:
            messagebox.showerror("Save Failed", f"Could not save settings:\n{exc}", parent=root)
            return
        result.updated_config = updated
        result.window_size = _capture_size()
        # Refresh the schedule tree so the Enabled column reflects the committed change.
        _refresh_tree(select=selected_indices[:1] if selected_indices else [])
        _save_btn.configure(text="✓ Saved")
        root.after(1500, lambda: _save_btn.configure(text="Save"))

    def _cancel() -> None:
        _cancel_history_poll()
        result.window_size = _capture_size()
        root.destroy()

    _save_btn = ttk.Button(action_row, text="Save", command=_apply_settings)
    _save_btn.pack(side="right")
    ttk.Button(action_row, text="Close", command=_cancel).pack(side="right", padx=(0, 8))

    preset_combo.bind(
        "<<ComboboxSelected>>", lambda _event: _set_preset_from_label(preset_var.get())
    )
    for variable in (
        preset_var,
        capture_root_var,
        archive_root_var,
        retention_mode_var,
        retention_days_var,
        purge_enabled_var,
        retention_grace_days_var,
        capture_mode_var,
        image_format_var,
        image_quality_var,
        start_tray_on_login_var,
        wake_for_scheduled_captures_var,
        show_last_capture_status_var,
        notify_on_failed_or_missed_var,
        notify_on_every_capture_var,
        show_capture_overlay_var,
    ):
        variable.trace_add("write", _refresh_overview)
    _update_path_state()
    _refresh_overview()
    root.protocol("WM_DELETE_WINDOW", _cancel)
    root.mainloop()
    return result


def _browse_directory(parent: tk.Tk, target: tk.StringVar) -> None:
    chosen = filedialog.askdirectory(parent=parent, initialdir=target.get() or None)
    if chosen:
        target.set(chosen)
