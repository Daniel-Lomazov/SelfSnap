from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from tkinter import filedialog, messagebox, ttk

from selfsnap.config_store import save_config
from selfsnap.models import AppConfig, ConfigValidationError, StoragePreset
from selfsnap.paths import AppPaths
from selfsnap.storage import apply_storage_preset, validate_storage_config
from selfsnap.tray.schedule_editor import (
    RecurringScheduleDraft,
    default_draft,
    default_unit_label,
    draft_from_form,
    draft_from_schedule,
    draft_to_schedule,
    editor_selection_summary,
    enabled_label,
    format_date_text,
    format_time_text,
    schedules_summary_text,
    schedule_help_text,
    selection_state,
    unit_label,
    unit_labels,
    unit_phrase,
)
from selfsnap.ui.fluent import (
    ACCENT_COLOR,
    BORDER_COLOR,
    CARD_BG,
    DANGER_FG,
    TEXT_MUTED,
    WARNING_FG,
    WINDOW_BG,
    apply_fluent_window,
    bind_dynamic_wrap,
    create_card,
    create_inset_panel,
    create_page_header,
    create_scrollable_page,
)
from selfsnap.ui.presentation import (
    maintenance_summary_text,
    scheduler_status_detail,
    settings_header_status,
    storage_summary_text,
    visibility_summary_text,
)
from selfsnap.ui_labels import (
    capture_mode_label,
    capture_mode_labels,
    capture_mode_value,
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
    apply_fluent_window(root)

    preset_var = tk.StringVar(master=root, value=storage_preset_label(config.storage_preset))
    capture_root_var = tk.StringVar(master=root, value=config.capture_storage_root)
    archive_root_var = tk.StringVar(master=root, value=config.archive_storage_root)
    retention_mode_var = tk.StringVar(
        master=root, value=retention_mode_label(config.retention_mode)
    )
    retention_days_var = tk.StringVar(
        master=root, value="" if config.retention_days is None else str(config.retention_days)
    )
    capture_mode_var = tk.StringVar(master=root, value=capture_mode_label(config.capture_mode))
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

    page = create_scrollable_page(root)
    page.container.grid(row=0, column=0, sticky="nsew", padx=18, pady=(18, 0))
    content = page.content
    content.columnconfigure(0, weight=1)

    def _field_label(
        parent: tk.Misc,
        text: str,
        *,
        foreground: str = TEXT_MUTED,
    ) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            bg=str(parent.cget("bg")),
            fg=foreground,
            font=("Segoe UI Semibold", 9),
            anchor="w",
            justify="left",
        )

    def _helper_label(
        parent: tk.Misc,
        text: str,
        *,
        foreground: str = TEXT_MUTED,
    ) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            bg=str(parent.cget("bg")),
            fg=foreground,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
        )

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

    row = 0

    header_text, header_tone = settings_header_status(config)
    header = create_page_header(
        content,
        eyebrow="Windows 11 inspired",
        title="SelfSnap Settings",
        subtitle=(
            "A clean, local-first control surface for storage, recurring captures, "
            "notifications, and maintenance."
        ),
        badge_text=header_text,
        badge_tone=header_tone,
    )
    header.frame.grid(row=row, column=0, sticky="ew")
    bind_dynamic_wrap(content, root, header.subtitle_label, padding=72)
    row += 1

    trust_label = tk.Label(
        content,
        text=local_privacy_notice(),
        bg=WINDOW_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10),
        justify="left",
        anchor="w",
    )
    trust_label.grid(row=row, column=0, sticky="ew", pady=(10, 0))
    bind_dynamic_wrap(content, root, trust_label, padding=64)
    row += 1

    scheduler_notice = scheduler_status_detail(config)
    if scheduler_notice is not None:
        scheduler_label = tk.Label(
            content,
            text=scheduler_notice,
            bg=WINDOW_BG,
            fg=WARNING_FG,
            font=("Segoe UI Semibold", 9),
            justify="left",
            anchor="w",
        )
        scheduler_label.grid(row=row, column=0, sticky="ew", pady=(8, 0))
        bind_dynamic_wrap(content, root, scheduler_label, padding=64, minimum=280)
        row += 1

    overview = tk.Frame(content, bg=WINDOW_BG)
    overview.grid(row=row, column=0, sticky="ew", pady=(16, 0))
    overview.columnconfigure(0, weight=6)
    overview.columnconfigure(1, weight=5)
    row += 1

    storage_card = create_card(
        overview,
        title="Storage",
        summary=storage_summary_text(
            storage_preset=config.storage_preset,
            retention_mode=config.retention_mode,
            retention_days=config.retention_days,
            capture_mode=config.capture_mode,
            image_format=config.image_format,
            image_quality=config.image_quality,
            purge_enabled=config.purge_enabled,
            retention_grace_days=config.retention_grace_days,
        ),
        badge_text="Local-first",
        tone="accent",
    )
    storage_card.frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    bind_dynamic_wrap(storage_card.frame, root, storage_card.summary_label, padding=48, minimum=220)

    visibility_card = create_card(
        overview,
        title="Experience",
        summary=visibility_summary_text(
            start_tray_on_login=config.start_tray_on_login,
            wake_for_scheduled_captures=config.wake_for_scheduled_captures,
            show_last_capture_status=config.show_last_capture_status,
            notify_on_failed_or_missed=config.notify_on_failed_or_missed,
            notify_on_every_capture=config.notify_on_every_capture,
            show_capture_overlay=config.show_capture_overlay,
        ),
        badge_text="Tray surface",
        tone="info",
    )
    visibility_card.frame.grid(row=0, column=1, sticky="nsew")
    bind_dynamic_wrap(
        visibility_card.frame,
        root,
        visibility_card.summary_label,
        padding=48,
        minimum=220,
    )

    storage_card.body.columnconfigure(0, weight=1)

    _field_label(storage_card.body, "Storage preset").grid(row=0, column=0, sticky="ew")
    preset_combo = ttk.Combobox(
        storage_card.body,
        textvariable=preset_var,
        state="readonly",
        values=storage_preset_labels(),
        width=24,
    )
    preset_combo.grid(row=1, column=0, sticky="ew", pady=(4, 12))

    _field_label(storage_card.body, "Capture storage root").grid(row=2, column=0, sticky="ew")
    capture_row = tk.Frame(storage_card.body, bg=CARD_BG)
    capture_row.grid(row=3, column=0, sticky="ew", pady=(4, 12))
    capture_row.columnconfigure(0, weight=1)
    capture_entry = ttk.Entry(capture_row, textvariable=capture_root_var)
    capture_entry.grid(row=0, column=0, sticky="ew")
    capture_browse = ttk.Button(
        capture_row,
        text="Browse",
        command=lambda: _browse_directory(root, capture_root_var),
        style="Small.TButton",
    )
    capture_browse.grid(row=0, column=1, sticky="e", padx=(8, 0))

    _field_label(storage_card.body, "Archive storage root").grid(row=4, column=0, sticky="ew")
    archive_row = tk.Frame(storage_card.body, bg=CARD_BG)
    archive_row.grid(row=5, column=0, sticky="ew", pady=(4, 12))
    archive_row.columnconfigure(0, weight=1)
    archive_entry = ttk.Entry(archive_row, textvariable=archive_root_var)
    archive_entry.grid(row=0, column=0, sticky="ew")
    archive_browse = ttk.Button(
        archive_row,
        text="Browse",
        command=lambda: _browse_directory(root, archive_root_var),
        style="Small.TButton",
    )
    archive_browse.grid(row=0, column=1, sticky="e", padx=(8, 0))

    retention_row = tk.Frame(storage_card.body, bg=CARD_BG)
    retention_row.grid(row=6, column=0, sticky="ew", pady=(0, 12))
    retention_row.columnconfigure(0, weight=1)
    retention_row.columnconfigure(1, weight=1)
    _field_label(retention_row, "Retention policy").grid(row=0, column=0, sticky="ew")
    _field_label(retention_row, "Archive after days").grid(
        row=0,
        column=1,
        sticky="ew",
        padx=(10, 0),
    )
    ttk.Combobox(
        retention_row,
        textvariable=retention_mode_var,
        values=retention_mode_labels(),
        state="readonly",
    ).grid(row=1, column=0, sticky="ew", pady=(4, 0))
    ttk.Entry(retention_row, textvariable=retention_days_var, width=10).grid(
        row=1,
        column=1,
        sticky="ew",
        padx=(10, 0),
        pady=(4, 0),
    )

    capture_options_row = tk.Frame(storage_card.body, bg=CARD_BG)
    capture_options_row.grid(row=7, column=0, sticky="ew", pady=(0, 12))
    capture_options_row.columnconfigure(0, weight=1)
    capture_options_row.columnconfigure(1, weight=1)
    capture_options_row.columnconfigure(2, weight=1)
    _field_label(capture_options_row, "Capture mode").grid(row=0, column=0, sticky="ew")
    _field_label(capture_options_row, "Image format").grid(
        row=0,
        column=1,
        sticky="ew",
        padx=(10, 0),
    )
    _field_label(capture_options_row, "Quality").grid(
        row=0,
        column=2,
        sticky="ew",
        padx=(10, 0),
    )
    ttk.Combobox(
        capture_options_row,
        textvariable=capture_mode_var,
        values=capture_mode_labels(),
        state="readonly",
    ).grid(row=1, column=0, sticky="ew", pady=(4, 0))
    ttk.Combobox(
        capture_options_row,
        textvariable=image_format_var,
        values=["PNG", "JPEG", "WEBP"],
        state="readonly",
    ).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(4, 0))
    ttk.Entry(capture_options_row, textvariable=image_quality_var, width=10).grid(
        row=1,
        column=2,
        sticky="ew",
        padx=(10, 0),
        pady=(4, 0),
    )

    purge_row = tk.Frame(storage_card.body, bg=CARD_BG)
    purge_row.grid(row=8, column=0, sticky="ew")
    purge_row.columnconfigure(0, weight=1)
    ttk.Checkbutton(
        purge_row,
        text="Permanently delete after grace period",
        variable=purge_enabled_var,
    ).grid(row=0, column=0, sticky="w")
    grace_group = tk.Frame(purge_row, bg=CARD_BG)
    grace_group.grid(row=0, column=1, sticky="e")
    _field_label(grace_group, "Grace days").grid(row=0, column=0, sticky="w")
    ttk.Entry(grace_group, textvariable=retention_grace_days_var, width=10).grid(
        row=1,
        column=0,
        sticky="e",
        pady=(4, 0),
    )

    visibility_card.body.columnconfigure(0, weight=1)
    _field_label(visibility_card.body, "Tray and launch").grid(row=0, column=0, sticky="ew")
    ttk.Checkbutton(
        visibility_card.body,
        text="Start tray on login",
        variable=start_tray_on_login_var,
    ).grid(row=1, column=0, sticky="w", pady=(6, 0))
    ttk.Checkbutton(
        visibility_card.body,
        text="Wake for scheduled captures when supported",
        variable=wake_for_scheduled_captures_var,
    ).grid(row=2, column=0, sticky="w", pady=(4, 0))
    ttk.Checkbutton(
        visibility_card.body,
        text="Show latest capture status in tray menu",
        variable=show_last_capture_status_var,
    ).grid(row=3, column=0, sticky="w", pady=(4, 0))
    tk.Frame(visibility_card.body, bg=BORDER_COLOR, height=1).grid(
        row=4,
        column=0,
        sticky="ew",
        pady=(14, 14),
    )
    _field_label(visibility_card.body, "Notifications and overlay").grid(
        row=5,
        column=0,
        sticky="ew",
    )
    ttk.Checkbutton(
        visibility_card.body,
        text="Notify on failed or missed captures",
        variable=notify_on_failed_or_missed_var,
    ).grid(row=6, column=0, sticky="w", pady=(6, 0))
    ttk.Checkbutton(
        visibility_card.body,
        text="Notify on every scheduled and manual capture",
        variable=notify_on_every_capture_var,
    ).grid(row=7, column=0, sticky="w", pady=(4, 0))
    ttk.Checkbutton(
        visibility_card.body,
        text="Show brief on-screen overlay after capture",
        variable=show_capture_overlay_var,
    ).grid(row=8, column=0, sticky="w", pady=(4, 0))

    schedules_card = create_card(
        content,
        title="Schedules",
        summary=schedules_summary_text(drafts),
        badge_text="Recurring capture",
        tone="accent",
    )
    schedules_card.frame.grid(row=row, column=0, sticky="ew", pady=(16, 0))
    bind_dynamic_wrap(schedules_card.frame, root, schedules_card.summary_label, padding=48)
    row += 1

    schedules_card.body.columnconfigure(0, weight=1)

    schedule_help_label = tk.Label(
        schedules_card.body,
        text=schedule_help_text(),
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10),
        justify="left",
        anchor="w",
    )
    schedule_help_label.grid(row=0, column=0, sticky="ew")
    bind_dynamic_wrap(schedules_card.body, root, schedule_help_label, padding=42, minimum=300)

    schedules_body = tk.Frame(schedules_card.body, bg=CARD_BG)
    schedules_body.grid(row=1, column=0, sticky="ew", pady=(14, 0))
    schedules_body.columnconfigure(0, weight=1)
    schedules_body.columnconfigure(1, weight=1)

    list_panel = create_inset_panel(
        schedules_body,
        title="Configured captures",
        summary="Click Status to pause or resume a schedule directly from the list.",
    )
    list_panel.frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    list_panel.body.columnconfigure(0, weight=1)
    list_panel.body.rowconfigure(0, weight=1)
    bind_dynamic_wrap(list_panel.frame, root, list_panel.summary_label, padding=36, minimum=220)

    editor_panel = create_inset_panel(
        schedules_body,
        title="Editor",
        summary=editor_selection_summary(0),
        tone="accent",
    )
    editor_panel.frame.grid(row=0, column=1, sticky="nsew")
    editor_panel.body.columnconfigure(0, weight=1)
    editor_panel.body.columnconfigure(1, weight=1)
    bind_dynamic_wrap(editor_panel.frame, root, editor_panel.summary_label, padding=36, minimum=220)

    history_panel = create_inset_panel(
        schedules_card.body,
        title="Recent runs",
        summary="Refreshes automatically every 5 seconds for the selected schedule.",
    )
    history_panel.frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
    history_panel.body.columnconfigure(0, weight=1)
    bind_dynamic_wrap(history_panel.frame, root, history_panel.summary_label, padding=36, minimum=240)

    schedule_tree = ttk.Treeview(
        list_panel.body,
        columns=("label", "recurrence", "start", "enabled"),
        show="headings",
        selectmode="extended",
        height=10,
    )
    schedule_tree.heading("label", text="Label")
    schedule_tree.heading("recurrence", text="Recurrence")
    schedule_tree.heading("start", text="Start")
    schedule_tree.heading("enabled", text="Status")
    schedule_tree.column("label", width=180, anchor="w", stretch=True)
    schedule_tree.column("recurrence", width=230, anchor="w", stretch=True)
    schedule_tree.column("start", width=180, anchor="w", stretch=True)
    schedule_tree.column("enabled", width=96, anchor="center", stretch=False)
    schedule_tree.grid(row=0, column=0, sticky="nsew")
    tree_scrollbar = ttk.Scrollbar(list_panel.body, orient="vertical", command=schedule_tree.yview)
    tree_scrollbar.grid(row=0, column=1, sticky="ns")
    schedule_tree.configure(yscrollcommand=tree_scrollbar.set)

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

    def _draft_from_form(schedule_id: str | None = None, enabled: bool = True) -> RecurringScheduleDraft:
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
        editor_panel.summary_label.configure(text=editor_selection_summary(len(selected_indices)))

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

    def _refresh_schedule_summary() -> None:
        schedules_card.summary_label.configure(text=schedules_summary_text(drafts))

    def _format_local_timestamp(utc_text: str) -> str:
        if not utc_text:
            return "(unknown time)"
        text = utc_text.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return utc_text[:19].replace("T", " ")
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone().strftime("%Y-%m-%d %H:%M:%S")

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
                    enabled_label(draft.enabled),
                ),
            )
        if select:
            for index in select:
                schedule_tree.selection_add(str(index))
            schedule_tree.see(str(select[0]))
        _update_selection_from_tree()
        _refresh_schedule_summary()

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
                ts = _format_local_timestamp(r.started_utc or r.created_utc or "")
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
            drafts[index] = _draft_from_form(schedule_id=drafts[index].schedule_id, enabled=drafts[index].enabled)
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

    _field_label(editor_panel.body, "Label").grid(row=0, column=0, sticky="ew")
    label_entry = ttk.Entry(editor_panel.body, textvariable=label_var)
    label_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 10))

    _field_label(editor_panel.body, "Every N").grid(row=2, column=0, sticky="ew")
    _field_label(editor_panel.body, "Unit").grid(row=2, column=1, sticky="ew", padx=(10, 0))
    every_spinbox = tk.Spinbox(
        editor_panel.body,
        from_=1,
        to=999999,
        textvariable=every_var,
        width=12,
        relief="solid",
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
        highlightcolor=ACCENT_COLOR,
    )
    every_spinbox.grid(row=3, column=0, sticky="w", pady=(4, 10))
    unit_combo = ttk.Combobox(
        editor_panel.body,
        textvariable=unit_var,
        values=unit_labels(),
        state="readonly",
    )
    unit_combo.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(4, 10))

    _field_label(editor_panel.body, "Start date").grid(row=4, column=0, sticky="ew")
    _field_label(editor_panel.body, "Start time").grid(row=4, column=1, sticky="ew", padx=(10, 0))
    start_date_entry = ttk.Entry(editor_panel.body, textvariable=start_date_var)
    start_date_entry.grid(row=5, column=0, sticky="ew", pady=(4, 10))
    start_time_entry = ttk.Entry(editor_panel.body, textvariable=start_time_var)
    start_time_entry.grid(row=5, column=1, sticky="ew", padx=(10, 0), pady=(4, 10))

    form_buttons = tk.Frame(editor_panel.body, bg=str(editor_panel.body.cget("bg")))
    form_buttons.grid(row=6, column=0, columnspan=2, sticky="ew")
    form_buttons.columnconfigure(0, weight=1)

    add_button = ttk.Button(form_buttons, text="Add", command=_add_schedule, style="Small.TButton")
    save_schedule_button = ttk.Button(
        form_buttons,
        text="Save",
        command=_save_schedule,
        style="Small.TButton",
    )
    cancel_schedule_button = ttk.Button(
        form_buttons,
        text="Cancel",
        command=_cancel_schedule_edit,
        style="Small.TButton",
    )
    cancel_schedule_button.pack(side="right")
    save_schedule_button.pack(side="right", padx=(0, 8))
    add_button.pack(side="right", padx=(0, 8))

    history_list = tk.Listbox(
        history_panel.body,
        height=6,
        state="disabled",
        selectmode="browse",
        relief="flat",
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
        highlightcolor=ACCENT_COLOR,
        bg="#ffffff",
        activestyle="none",
    )
    history_list.grid(row=0, column=0, sticky="ew")

    widgets_to_toggle.extend(
        [label_entry, every_spinbox, unit_combo, start_date_entry, start_time_entry]
    )

    list_btn_bar = tk.Frame(list_panel.body, bg=str(list_panel.body.cget("bg")))
    list_btn_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    list_delete_btn = ttk.Button(
        list_btn_bar,
        text="Delete Selected",
        command=_delete_schedule,
        style="Small.TButton",
    )
    list_delete_btn.pack(side="right")

    def _on_enabled_click(event: tk.Event) -> None:
        col = schedule_tree.identify_column(event.x)
        item = schedule_tree.identify_row(event.y)
        if col != "#4" or not item:
            return
        index = int(item)
        drafts[index].enabled = not drafts[index].enabled
        current_vals = list(schedule_tree.item(item, "values"))
        current_vals[3] = enabled_label(drafts[index].enabled)
        schedule_tree.item(item, values=current_vals)
        _refresh_schedule_summary()

    def _on_treeview_motion(event: tk.Event) -> None:
        col = schedule_tree.identify_column(event.x)
        schedule_tree.configure(cursor="hand2" if col == "#4" else "")

    schedule_tree.bind("<Button-1>", _on_enabled_click, add="+")
    schedule_tree.bind("<Motion>", _on_treeview_motion)
    schedule_tree.bind("<<TreeviewSelect>>", _update_selection_from_tree)
    _refresh_tree([])
    _load_draft_to_form(_new_default_draft())
    _selected_mode()
    history_refresh_job = root.after(HISTORY_REFRESH_INTERVAL_MS, _poll_history)

    maintenance_card = create_card(
        content,
        title="Maintenance",
        summary=maintenance_summary_text(),
        badge_text="Danger zone",
        tone="danger",
    )
    maintenance_card.frame.grid(row=row, column=0, sticky="ew", pady=(16, 0))
    maintenance_card.body.columnconfigure(0, weight=1)
    bind_dynamic_wrap(maintenance_card.frame, root, maintenance_card.summary_label, padding=48)
    row += 1

    maintenance_message = _helper_label(
        maintenance_card.body,
        text=(
            "Reset Capture History permanently deletes SelfSnap capture/archive files, "
            "database history, logs, schedules, and local user settings, then relaunches first run."
        ),
        foreground=DANGER_FG,
    )
    maintenance_message.grid(row=0, column=0, sticky="ew")
    bind_dynamic_wrap(maintenance_card.body, root, maintenance_message, padding=42, minimum=280)

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
        maintenance_card.body,
        text="Reset Capture History",
        command=_request_reset,
        style="Wide.TButton",
    ).grid(row=1, column=0, sticky="w", pady=(12, 0))

    def _update_storage_summary(*_args) -> None:
        try:
            storage_preset = storage_preset_value(preset_var.get())
        except ConfigValidationError:
            storage_preset = config.storage_preset
        try:
            retention_mode = retention_mode_value(retention_mode_var.get())
        except ConfigValidationError:
            retention_mode = config.retention_mode
        try:
            capture_mode = capture_mode_value(capture_mode_var.get())
        except ConfigValidationError:
            capture_mode = config.capture_mode
        storage_card.summary_label.configure(
            text=storage_summary_text(
                storage_preset=storage_preset,
                retention_mode=retention_mode,
                retention_days=retention_days_var.get(),
                capture_mode=capture_mode,
                image_format=image_format_var.get(),
                image_quality=image_quality_var.get(),
                purge_enabled=purge_enabled_var.get(),
                retention_grace_days=retention_grace_days_var.get(),
            )
        )

    def _update_visibility_summary(*_args) -> None:
        visibility_card.summary_label.configure(
            text=visibility_summary_text(
                start_tray_on_login=start_tray_on_login_var.get(),
                wake_for_scheduled_captures=wake_for_scheduled_captures_var.get(),
                show_last_capture_status=show_last_capture_status_var.get(),
                notify_on_failed_or_missed=notify_on_failed_or_missed_var.get(),
                notify_on_every_capture=notify_on_every_capture_var.get(),
                show_capture_overlay=show_capture_overlay_var.get(),
            )
        )

    for variable in (
        preset_var,
        retention_mode_var,
        retention_days_var,
        capture_mode_var,
        image_format_var,
        image_quality_var,
        purge_enabled_var,
        retention_grace_days_var,
    ):
        variable.trace_add("write", _update_storage_summary)

    for variable in (
        start_tray_on_login_var,
        wake_for_scheduled_captures_var,
        show_last_capture_status_var,
        notify_on_failed_or_missed_var,
        notify_on_every_capture_var,
        show_capture_overlay_var,
    ):
        variable.trace_add("write", _update_visibility_summary)

    _update_storage_summary()
    _update_visibility_summary()

    action_row = tk.Frame(root, bg=WINDOW_BG, padx=18, pady=14)
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
                capture_mode=capture_mode_value(capture_mode_var.get()),
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
        _save_btn.configure(text="Saved")
        root.after(1500, lambda: _save_btn.configure(text="Save"))

    def _cancel() -> None:
        _cancel_history_poll()
        result.window_size = _capture_size()
        root.destroy()

    _save_btn = ttk.Button(action_row, text="Save", command=_apply_settings, style="Wide.TButton")
    _save_btn.pack(side="right")
    ttk.Button(action_row, text="Close", command=_cancel, style="Wide.TButton").pack(
        side="right",
        padx=(0, 8),
    )

    preset_combo.bind(
        "<<ComboboxSelected>>", lambda _event: _set_preset_from_label(preset_var.get())
    )
    _update_path_state()
    root.protocol("WM_DELETE_WINDOW", _cancel)
    root.mainloop()
    return result


def _browse_directory(parent: tk.Tk, target: tk.StringVar) -> None:
    chosen = filedialog.askdirectory(parent=parent, initialdir=target.get() or None)
    if chosen:
        target.set(chosen)
