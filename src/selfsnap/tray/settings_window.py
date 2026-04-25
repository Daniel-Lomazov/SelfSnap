from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, replace
from tkinter import filedialog, font as tk_font, messagebox, ttk

from selfsnap.config_store import load_or_create_config, save_config
from selfsnap.db import connect, ensure_database
from selfsnap.models import AppConfig, CaptureRecord, ConfigValidationError, StoragePreset
from selfsnap.paths import AppPaths
from selfsnap.records import get_latest_record
from selfsnap.runtime_launch import launch_background, resolve_manual_capture_background_invocation
from selfsnap.storage import (
    apply_storage_preset,
    storage_path_for_display,
    storage_path_from_display,
    validate_storage_config,
)
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
from selfsnap.ui.diagnostics import (
    DiagnosticSummary,
    format_local_timestamp,
    last_activity_summary,
    notification_summary,
    operational_summary,
    retention_summary,
    scheduler_sync_summary,
    storage_summary,
)
from selfsnap.ui.fluent import (
    ACCENT_BG,
    ACCENT_COLOR,
    BORDER_COLOR,
    CARD_BG,
    DANGER_BG,
    DANGER_FG,
    INFO_BG,
    INFO_FG,
    TEXT_MUTED,
    TEXT_SECONDARY,
    WARNING_BG,
    WARNING_FG,
    WINDOW_BG,
    apply_fluent_window,
    bind_dynamic_wrap,
    create_card,
    create_inset_panel,
    create_page_header,
    create_scrollable_page,
    SectionBlock,
    ScrollablePage,
)
from selfsnap.ui.presentation import (
    maintenance_summary_text,
    scheduler_status_detail,
    settings_page_subtitle,
    settings_window_title,
    settings_header_status,
    storage_summary_text,
    visibility_summary_text,
)
from selfsnap.ui_labels import (
    capture_mode_label,
    capture_mode_labels,
    capture_mode_value,
    image_format_label,
    image_format_labels,
    image_format_value,
    local_privacy_notice,
    retention_mode_label,
    retention_mode_labels,
    retention_mode_value,
    retention_policy_label,
    storage_preset_label,
    storage_preset_labels,
    storage_preset_value,
)
from selfsnap.window_sizing import (
    SETTINGS_WINDOW_MIN_HEIGHT,
    SETTINGS_WINDOW_MIN_WIDTH,
    build_centered_window_geometry,
    clamp_settings_window_size,
)

HISTORY_REFRESH_INTERVAL_MS = 5000
CONFIG_POLL_INTERVAL_MS = 1000
STACKED_COMPACT_LAYOUT_MAX_WIDTH = 660
RESPONSIVE_CARD_SPLIT_MIN_WIDTH = 820

SCHEDULE_TREE_COLUMN_SPECS: tuple[tuple[str, int, int, str], ...] = (
    ("label", 112, 3, "w"),
    ("recurrence", 160, 4, "w"),
    ("start", 128, 3, "w"),
    ("enabled", 72, 0, "center"),
)


def resolve_schedule_tree_column_widths(available_width: int) -> dict[str, int]:
    widths = {name: minimum for name, minimum, _weight, _anchor in SCHEDULE_TREE_COLUMN_SPECS}
    minimum_total = sum(widths.values())
    if available_width <= minimum_total:
        return widths

    extra_width = available_width - minimum_total
    weighted_specs = [(name, weight) for name, _minimum, weight, _anchor in SCHEDULE_TREE_COLUMN_SPECS if weight > 0]
    if not weighted_specs:
        return widths

    total_weight = sum(weight for _name, weight in weighted_specs)
    remainders: list[tuple[int, str]] = []
    for name, weight in weighted_specs:
        added_width, remainder = divmod(extra_width * weight, total_weight)
        widths[name] += added_width
        remainders.append((remainder, name))

    leftover = available_width - sum(widths.values())
    for _remainder, name in sorted(remainders, reverse=True):
        if leftover <= 0:
            break
        widths[name] += 1
        leftover -= 1
    return widths


def use_stacked_schedule_layout(window_width: int) -> bool:
    return window_width <= STACKED_COMPACT_LAYOUT_MAX_WIDTH


def use_stacked_settings_card_layout(window_width: int) -> bool:
    return window_width < RESPONSIVE_CARD_SPLIT_MIN_WIDTH


def should_sync_polled_app_enabled(
    *,
    current_ui_value: bool,
    saved_value: bool,
    disk_value: bool,
    local_dirty: bool,
) -> bool:
    if disk_value == current_ui_value:
        return False
    if local_dirty and current_ui_value != saved_value:
        return False
    return True


@dataclass(slots=True)
class SettingsDialogResult:
    updated_config: AppConfig | None
    window_size: tuple[int, int]
    requested_reset: bool = False


def show_settings_dialog(config: AppConfig, paths: AppPaths) -> SettingsDialogResult:
    root = tk.Tk()
    root.title(settings_window_title())
    root.update_idletasks()
    window_width, window_height = SETTINGS_WINDOW_MIN_WIDTH, SETTINGS_WINDOW_MIN_HEIGHT
    use_stacked_compact_layout = window_width <= STACKED_COMPACT_LAYOUT_MAX_WIDTH
    root.geometry(
        build_centered_window_geometry(
            root.winfo_screenwidth(),
            root.winfo_screenheight(),
            window_width,
            window_height,
        )
    )
    root.minsize(SETTINGS_WINDOW_MIN_WIDTH, SETTINGS_WINDOW_MIN_HEIGHT)
    root.resizable(True, True)
    apply_fluent_window(root)

    app_enabled_var = tk.BooleanVar(master=root, value=config.app_enabled)
    preset_var = tk.StringVar(master=root, value=storage_preset_label(config.storage_preset))
    capture_root_var = tk.StringVar(
        master=root,
        value=storage_path_for_display(paths, config.capture_storage_root),
    )
    archive_root_var = tk.StringVar(
        master=root,
        value=storage_path_for_display(paths, config.archive_storage_root),
    )
    retention_mode_var = tk.StringVar(
        master=root, value=retention_mode_label(config.retention_mode)
    )
    retention_days_var = tk.StringVar(
        master=root, value="" if config.retention_days is None else str(config.retention_days)
    )
    capture_mode_var = tk.StringVar(master=root, value=capture_mode_label(config.capture_mode))
    image_format_var = tk.StringVar(master=root, value=image_format_label(config.image_format))
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
    capture_feedback_var = tk.StringVar(master=root, value="")
    general_details_var = tk.StringVar(master=root, value="")
    internal_preset_update = {"active": False}
    drafts: list[RecurringScheduleDraft] = [
        draft_from_schedule(schedule) for schedule in config.schedules
    ]
    selected_indices: list[int] = []
    history_refresh_job: str | None = None
    config_poll_job: str | None = None
    saved_app_enabled_value = {"value": config.app_enabled}
    app_enabled_dirty = {"value": False}

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
    latest_capture_var = tk.StringVar(master=root, value=_latest_capture_summary(latest_record))

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    shell = tk.Frame(root, bg=WINDOW_BG)
    shell.grid(row=0, column=0, sticky="nsew", padx=10, pady=(8, 0))
    shell.columnconfigure(0, weight=1)
    shell.rowconfigure(3, weight=1)

    def _field_label(parent: tk.Misc, text: str) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            bg=str(parent.cget("bg")),
            fg=TEXT_MUTED,
            font=("Segoe UI Semibold", 9),
            anchor="w",
            justify="left",
        )

    def _helper_label(parent: tk.Misc, text: str, *, foreground: str = TEXT_MUTED) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            bg=str(parent.cget("bg")),
            fg=foreground,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
        )

    def _badge_palette(tone: str) -> tuple[str, str]:
        if tone == "accent":
            return ACCENT_BG, ACCENT_COLOR
        if tone == "info":
            return INFO_BG, INFO_FG
        if tone == "warning":
            return WARNING_BG, WARNING_FG
        if tone == "danger":
            return DANGER_BG, DANGER_FG
        return "#edf2f7", TEXT_SECONDARY

    def _set_badge(label: tk.Label | None, text: str, tone: str) -> None:
        if label is None:
            return
        bg, fg = _badge_palette(tone)
        label.configure(text=text, bg=bg, fg=fg)

    def _safe_int(value: str, fallback: int | None) -> int | None:
        text = value.strip()
        if not text:
            return fallback
        try:
            return int(text)
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

    def _selected_capture_mode() -> str:
        try:
            return capture_mode_value(capture_mode_var.get())
        except ConfigValidationError:
            return config.capture_mode

    def _selected_image_format() -> str:
        try:
            return image_format_value(image_format_var.get())
        except ConfigValidationError:
            return config.image_format

    def _preview_config() -> AppConfig:
        retention_mode = _selected_retention_mode()
        retention_days = None
        if retention_mode == "keep_days":
            retention_days = _safe_int(retention_days_var.get(), config.retention_days or 1)
        return replace(
            config,
            app_enabled=app_enabled_var.get() if config.first_run_completed else config.app_enabled,
            storage_preset=_selected_storage_preset(),
            capture_storage_root=storage_path_from_display(paths, capture_root_var.get()),
            archive_storage_root=storage_path_from_display(paths, archive_root_var.get()),
            retention_mode=retention_mode,
            retention_days=retention_days,
            purge_enabled=purge_enabled_var.get(),
            retention_grace_days=_safe_int(
                retention_grace_days_var.get(), config.retention_grace_days
            )
            or config.retention_grace_days,
            capture_mode=_selected_capture_mode(),
            image_format=_selected_image_format(),
            image_quality=_safe_int(image_quality_var.get(), config.image_quality)
            or config.image_quality,
            start_tray_on_login=start_tray_on_login_var.get(),
            wake_for_scheduled_captures=wake_for_scheduled_captures_var.get(),
            show_last_capture_status=show_last_capture_status_var.get(),
            notify_on_failed_or_missed=notify_on_failed_or_missed_var.get(),
            notify_on_every_capture=notify_on_every_capture_var.get(),
            show_capture_overlay=show_capture_overlay_var.get(),
        )

    def _capture_settings_summary(preview: AppConfig) -> str:
        try:
            retention_text = retention_policy_label(
                preview.retention_mode,
                preview.retention_days,
                preview.purge_enabled,
                preview.retention_grace_days,
            )
        except ConfigValidationError:
            retention_text = "Retention pending validation"
        format_text = image_format_label(preview.image_format)
        if preview.image_format in {"jpeg", "webp"}:
            format_text = f"{format_text} {preview.image_quality}%"
        return "\n".join([retention_text, capture_mode_label(preview.capture_mode), format_text])

    def _general_status_details(preview: AppConfig) -> str:
        if not preview.first_run_completed:
            state_message = "Finish first-run setup before scheduled captures can be enabled."
        elif preview.scheduler_sync_failed():
            state_message = scheduler_status_detail(preview) or (
                "Scheduled captures are enabled, but Windows Task Scheduler needs attention."
            )
        elif preview.app_enabled:
            state_message = "SelfSnap is ready for scheduled background capture."
        else:
            state_message = "Scheduled captures are paused. Capture Now still works."
        return _multiline_summary_text(f"{state_message}\n{schedules_summary_text(drafts)}")

    def _experience_summary(preview: AppConfig) -> str:
        return _multiline_summary_text(
            visibility_summary_text(
                start_tray_on_login=preview.start_tray_on_login,
                wake_for_scheduled_captures=preview.wake_for_scheduled_captures,
                show_last_capture_status=preview.show_last_capture_status,
                notify_on_failed_or_missed=preview.notify_on_failed_or_missed,
                notify_on_every_capture=preview.notify_on_every_capture,
                show_capture_overlay=preview.show_capture_overlay,
            )
        )

    def _storage_overview_summary(preview: AppConfig) -> str:
        return _multiline_summary_text(
            storage_summary_text(
                storage_preset=preview.storage_preset,
                retention_mode=preview.retention_mode,
                retention_days=preview.retention_days,
                capture_mode=preview.capture_mode,
                image_format=preview.image_format,
                image_quality=preview.image_quality,
                purge_enabled=preview.purge_enabled,
                retention_grace_days=preview.retention_grace_days,
            )
        )

    def _destinations_summary(preview: AppConfig) -> str:
        return f"{storage_preset_label(preview.storage_preset)} preset\nCapture and archive destinations"

    def _set_preset_from_label(selected_label: str) -> None:
        internal_preset_update["active"] = True
        try:
            preset = storage_preset_value(selected_label)
            preset_config = apply_storage_preset(paths, config, preset)
            preset_var.set(storage_preset_label(preset))
            capture_root_var.set(storage_path_for_display(paths, preset_config.capture_storage_root))
            archive_root_var.set(storage_path_for_display(paths, preset_config.archive_storage_root))
        finally:
            internal_preset_update["active"] = False
        _update_path_state()
        _refresh_dynamic_content()

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

    def _mark_app_enabled_dirty() -> None:
        app_enabled_dirty["value"] = app_enabled_var.get() != saved_app_enabled_value["value"]

    def _refresh_latest_capture_status() -> None:
        nonlocal latest_record
        latest_record = _load_latest_record()
        latest_capture_var.set(_latest_capture_summary(latest_record))
        _refresh_dynamic_content()

    def _capture_now_from_settings() -> None:
        try:
            launch_background(resolve_manual_capture_background_invocation(paths))
        except Exception as exc:
            messagebox.showerror(
                "Capture Failed",
                f"Could not start a manual capture:\n{exc}",
                parent=root,
            )
            return
        capture_feedback_var.set("Capture launched in the background.")
        root.after(2500, _refresh_latest_capture_status)
        root.after(5000, lambda: capture_feedback_var.set(""))

    def _capture_size() -> tuple[int, int]:
        root.update_idletasks()
        return clamp_settings_window_size(root.winfo_width(), root.winfo_height())

    def _multiline_summary_text(text: str) -> str:
        normalized = text.replace(" • ", "\n").replace(" | ", "\n")
        return "\n".join(line.strip() for line in normalized.splitlines() if line.strip())

    def _configure_card_pair_layout(
        container: tk.Misc,
        primary_card: SectionBlock,
        secondary_card: SectionBlock,
        *,
        stacked: bool,
        uniform_group: str,
        gap: int = 4,
    ) -> None:
        if stacked:
            container.columnconfigure(0, weight=1, uniform="")
            container.columnconfigure(1, weight=0, minsize=0, uniform="")
            primary_card.frame.grid_configure(
                row=0,
                column=0,
                sticky="ew",
                padx=(0, 0),
                pady=(0, 0),
            )
            secondary_card.frame.grid_configure(
                row=1,
                column=0,
                sticky="ew",
                padx=(0, 0),
                pady=(gap, 0),
            )
            return

        container.columnconfigure(0, weight=1, uniform=uniform_group)
        container.columnconfigure(1, weight=1, minsize=0, uniform=uniform_group)
        primary_card.frame.grid_configure(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, gap),
            pady=(0, 0),
        )
        secondary_card.frame.grid_configure(
            row=0,
            column=1,
            sticky="nsew",
            padx=(0, 0),
            pady=(0, 0),
        )

    def _configure_card_grid_layout(
        container: tk.Misc,
        cards: list[SectionBlock],
        *,
        stacked: bool,
        uniform_group: str,
        gap: int = 4,
    ) -> None:
        if stacked:
            container.columnconfigure(0, weight=1, uniform="")
            container.columnconfigure(1, weight=0, minsize=0, uniform="")
        else:
            container.columnconfigure(0, weight=1, uniform=uniform_group)
            container.columnconfigure(1, weight=1, minsize=0, uniform=uniform_group)

        for index, card in enumerate(cards):
            row_index = index if stacked else index // 2
            column_index = 0 if stacked else index % 2
            card.frame.grid_configure(
                row=row_index,
                column=column_index,
                sticky="nsew" if not stacked else "ew",
                padx=(0, gap) if not stacked and column_index == 0 else (0, 0),
                pady=(0, gap),
            )

    header_text, header_tone = settings_header_status(config)
    header = create_page_header(
        shell,
        eyebrow=None,
        title="SelfSnap Settings",
        subtitle=settings_page_subtitle(),
        badge_text=header_text,
        badge_tone=header_tone,
    )
    header.frame.grid(row=0, column=0, sticky="ew")
    bind_dynamic_wrap(shell, root, header.subtitle_label, padding=44)

    trust_label = tk.Label(
        shell,
        text=local_privacy_notice(),
        bg=WINDOW_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 8),
        justify="left",
        anchor="w",
    )
    trust_label.grid(row=1, column=0, sticky="ew", pady=(1, 0))
    bind_dynamic_wrap(shell, root, trust_label, padding=36)

    scheduler_notice_label = tk.Label(
        shell,
        bg=WINDOW_BG,
        fg=WARNING_FG,
        font=("Segoe UI Semibold", 8),
        justify="left",
        anchor="w",
    )
    scheduler_notice_label.grid(row=2, column=0, sticky="ew", pady=(1, 0))

    notebook = ttk.Notebook(shell)
    notebook.grid(row=3, column=0, sticky="nsew", pady=(4, 0))

    tab_pages: dict[str, ScrollablePage] = {}

    def _make_tab(title: str) -> tk.Frame:
        page = create_scrollable_page(notebook)
        tab_pages[title] = page
        notebook.add(page.container, text=title)
        page.content.columnconfigure(0, weight=1)
        return page.content

    def _selected_tab_title() -> str | None:
        selected = notebook.select()
        if not selected:
            return None
        return str(notebook.tab(selected, "text"))

    def _scroll_tab_to_top(title: str, *, passes: int = 4) -> None:
        page = tab_pages.get(title)
        if page is None:
            return
        page.pin_to_top(passes=passes)

    def _handle_tab_changed(_event=None) -> None:
        if _selected_tab_title() == "Schedules":
            notebook.focus_set()
            _scroll_tab_to_top("Schedules")

    notebook.bind("<<NotebookTabChanged>>", _handle_tab_changed, add="+")

    general_tab = _make_tab("General")
    storage_tab = _make_tab("Storage")
    schedules_tab = _make_tab("Schedules")
    diagnostics_tab = _make_tab("Diagnostics")
    maintenance_tab = _make_tab("Maintenance")

    general_grid = tk.Frame(general_tab, bg=WINDOW_BG)
    general_grid.grid(row=0, column=0, sticky="ew")
    general_grid.columnconfigure(0, weight=1)
    general_grid.columnconfigure(1, weight=1)

    general_status_card = create_card(
        general_grid,
        title="Quick Actions",
        summary=latest_capture_var.get(),
        badge_text=header_text,
        tone=header_tone,
    )
    if use_stacked_compact_layout:
        general_status_card.frame.grid(row=0, column=0, sticky="ew")
    else:
        general_status_card.frame.grid(row=0, column=0, sticky="ew", padx=(0, 4))
    bind_dynamic_wrap(general_status_card.frame, root, general_status_card.summary_label, padding=32)
    general_status_card.body.columnconfigure(0, weight=1)
    general_status_card.body.columnconfigure(1, weight=0)

    general_details_label = _helper_label(general_status_card.body, general_details_var.get())
    general_details_label.configure(textvariable=general_details_var)
    general_details_label.grid(row=0, column=0, columnspan=2, sticky="ew")
    bind_dynamic_wrap(general_status_card.body, root, general_details_label, padding=26, minimum=180)

    general_toggle = ttk.Checkbutton(
        general_status_card.body,
        text="Scheduled captures enabled",
        variable=app_enabled_var,
        command=_mark_app_enabled_dirty,
    )
    general_toggle.grid(row=1, column=0, sticky="w", pady=(8, 0))
    if not config.first_run_completed:
        general_toggle.state(["disabled"])

    ttk.Button(
        general_status_card.body,
        text="Capture Now",
        command=_capture_now_from_settings,
        style="Wide.TButton",
    ).grid(row=1, column=1, sticky="e", pady=(8, 0))

    feedback_label = _helper_label(general_status_card.body, "")
    feedback_label.configure(textvariable=capture_feedback_var)
    feedback_label.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))
    bind_dynamic_wrap(general_status_card.body, root, feedback_label, padding=26, minimum=160)

    experience_card = create_card(
        general_grid,
        title="Experience",
        summary=_experience_summary(config),
        badge_text="General",
        tone="info",
    )
    if use_stacked_compact_layout:
        experience_card.frame.grid(row=1, column=0, sticky="ew", pady=(4, 0))
    else:
        experience_card.frame.grid(row=0, column=1, sticky="ew")
    bind_dynamic_wrap(experience_card.frame, root, experience_card.summary_label, padding=32)
    experience_options = [
        ("Start tray on login", start_tray_on_login_var),
        ("Wake for scheduled captures when supported", wake_for_scheduled_captures_var),
        ("Show latest capture status in tray menu", show_last_capture_status_var),
        ("Notify on failed or missed captures", notify_on_failed_or_missed_var),
        ("Notify on every scheduled and manual capture", notify_on_every_capture_var),
        ("Show brief on-screen overlay after capture", show_capture_overlay_var),
    ]
    experience_card.body.columnconfigure(0, weight=1)
    for index, (label_text, variable) in enumerate(experience_options):
        ttk.Checkbutton(
            experience_card.body,
            text=label_text,
            variable=variable,
        ).grid(row=index, column=0, sticky="w", pady=(0, 0) if index == 0 else (4, 0))

    storage_overview_card = create_card(
        general_tab,
        title="Storage Overview",
        summary=_storage_overview_summary(config),
        badge_text="Storage",
        tone="accent",
    )
    storage_overview_card.frame.grid(row=1, column=0, sticky="ew", pady=(6, 0))
    bind_dynamic_wrap(storage_overview_card.frame, root, storage_overview_card.summary_label, padding=32)
    overview_helper = _helper_label(
        storage_overview_card.body,
        "Use the Storage tab to change destinations, retention, capture format, and purge policy.",
    )
    overview_helper.grid(row=0, column=0, sticky="ew")
    bind_dynamic_wrap(storage_overview_card.body, root, overview_helper, padding=26, minimum=180)

    storage_grid = tk.Frame(storage_tab, bg=WINDOW_BG)
    storage_grid.grid(row=0, column=0, sticky="ew")
    storage_grid.columnconfigure(0, weight=1)
    storage_grid.columnconfigure(1, weight=1)

    destinations_card = create_card(
        storage_grid,
        title="Destinations",
        summary=_destinations_summary(config),
        badge_text="Locations",
        tone="accent",
    )
    if use_stacked_compact_layout:
        destinations_card.frame.grid(row=0, column=0, sticky="ew")
    else:
        destinations_card.frame.grid(row=0, column=0, sticky="ew", padx=(0, 4))
    bind_dynamic_wrap(destinations_card.frame, root, destinations_card.summary_label, padding=32)
    destinations_card.body.columnconfigure(0, weight=1)

    _field_label(destinations_card.body, "Storage preset").grid(row=0, column=0, sticky="ew")
    preset_combo = ttk.Combobox(
        destinations_card.body,
        textvariable=preset_var,
        state="readonly",
        values=storage_preset_labels(),
        width=22,
    )
    preset_combo.grid(row=1, column=0, sticky="ew", pady=(4, 6))

    _field_label(destinations_card.body, "Capture storage root").grid(row=2, column=0, sticky="ew")
    capture_row = tk.Frame(destinations_card.body, bg=CARD_BG)
    capture_row.grid(row=3, column=0, sticky="ew", pady=(4, 6))
    capture_row.columnconfigure(0, weight=1)
    capture_entry = ttk.Entry(capture_row, textvariable=capture_root_var)
    capture_entry.grid(row=0, column=0, sticky="ew")
    capture_browse = ttk.Button(
        capture_row,
        text="Browse",
        command=lambda: _browse_directory(root, capture_root_var, paths),
        style="Small.TButton",
    )
    capture_browse.grid(row=0, column=1, sticky="e", padx=(6, 0))

    _field_label(destinations_card.body, "Archive storage root").grid(row=4, column=0, sticky="ew")
    archive_row = tk.Frame(destinations_card.body, bg=CARD_BG)
    archive_row.grid(row=5, column=0, sticky="ew", pady=(4, 0))
    archive_row.columnconfigure(0, weight=1)
    archive_entry = ttk.Entry(archive_row, textvariable=archive_root_var)
    archive_entry.grid(row=0, column=0, sticky="ew")
    archive_browse = ttk.Button(
        archive_row,
        text="Browse",
        command=lambda: _browse_directory(root, archive_root_var, paths),
        style="Small.TButton",
    )
    archive_browse.grid(row=0, column=1, sticky="e", padx=(6, 0))

    capture_settings_card = create_card(
        storage_grid,
        title="Capture Output",
        summary=_capture_settings_summary(config),
        badge_text="Output",
        tone="info",
    )
    if use_stacked_compact_layout:
        capture_settings_card.frame.grid(row=1, column=0, sticky="ew", pady=(4, 0))
    else:
        capture_settings_card.frame.grid(row=0, column=1, sticky="ew")
    bind_dynamic_wrap(capture_settings_card.frame, root, capture_settings_card.summary_label, padding=32)

    settings_row = tk.Frame(capture_settings_card.body, bg=CARD_BG)
    settings_row.grid(row=0, column=0, sticky="ew")
    settings_row.columnconfigure(0, weight=1)
    settings_row.columnconfigure(1, weight=1)

    _field_label(settings_row, "Retention policy").grid(row=0, column=0, sticky="ew")
    _field_label(settings_row, "Archive after days").grid(
        row=0,
        column=1,
        sticky="ew",
        padx=(6, 0),
    )
    ttk.Combobox(
        settings_row,
        textvariable=retention_mode_var,
        values=retention_mode_labels(),
        state="readonly",
    ).grid(row=1, column=0, sticky="ew", pady=(4, 6))

    ttk.Entry(settings_row, textvariable=retention_days_var, width=10).grid(
        row=1,
        column=1,
        sticky="ew",
        padx=(6, 0),
        pady=(4, 6),
    )

    _field_label(settings_row, "Capture mode").grid(row=2, column=0, sticky="ew")
    _field_label(settings_row, "Image format").grid(
        row=2,
        column=1,
        sticky="ew",
        padx=(6, 0),
    )
    ttk.Combobox(
        settings_row,
        textvariable=capture_mode_var,
        values=capture_mode_labels(),
        state="readonly",
    ).grid(row=3, column=0, sticky="ew", pady=(4, 6))
    ttk.Combobox(
        settings_row,
        textvariable=image_format_var,
        values=image_format_labels(),
        state="readonly",
    ).grid(row=3, column=1, sticky="ew", padx=(6, 0), pady=(4, 6))

    quality_row = tk.Frame(capture_settings_card.body, bg=CARD_BG)
    quality_row.grid(row=1, column=0, sticky="ew")
    quality_row.columnconfigure(0, weight=1)
    quality_row.columnconfigure(1, weight=1)
    _field_label(quality_row, "Quality (JPEG/WebP)").grid(row=0, column=0, sticky="ew")
    _field_label(quality_row, "Grace days").grid(row=0, column=1, sticky="ew", padx=(6, 0))
    ttk.Entry(quality_row, textvariable=image_quality_var, width=10).grid(
        row=1,
        column=0,
        sticky="ew",
        pady=(4, 0),
    )
    ttk.Entry(quality_row, textvariable=retention_grace_days_var, width=10).grid(
        row=1,
        column=1,
        sticky="ew",
        padx=(6, 0),
        pady=(4, 0),
    )

    ttk.Checkbutton(
        capture_settings_card.body,
        text="Permanently delete after grace period",
        variable=purge_enabled_var,
    ).grid(row=2, column=0, sticky="w", pady=(8, 0))

    schedules_card = create_card(
        schedules_tab,
        title="Recurring Schedules",
        summary=schedules_summary_text(drafts),
        badge_text="Recurring capture",
        tone="accent",
    )
    schedules_card.frame.grid(row=0, column=0, sticky="ew")
    bind_dynamic_wrap(schedules_card.frame, root, schedules_card.summary_label, padding=32)
    schedules_card.body.columnconfigure(0, weight=1)

    schedule_help_label = tk.Label(
        schedules_card.body,
        text=schedule_help_text(),
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 9),
        justify="left",
        anchor="w",
    )
    schedule_help_label.grid(row=0, column=0, sticky="ew")
    bind_dynamic_wrap(schedules_card.body, root, schedule_help_label, padding=28, minimum=200)

    schedules_body = tk.Frame(schedules_card.body, bg=CARD_BG)
    schedules_body.grid(row=1, column=0, sticky="ew", pady=(6, 0))
    schedules_body.columnconfigure(0, weight=1)
    schedules_body.columnconfigure(1, weight=0, minsize=0)
    schedules_body.rowconfigure(0, weight=1)
    schedules_body.rowconfigure(1, weight=0)

    schedule_layout_state = {"stacked": use_stacked_schedule_layout(window_width)}

    list_panel = create_inset_panel(
        schedules_body,
        title="Configured captures",
        summary="Click Status to pause or resume a schedule directly from the list.",
    )
    list_panel.frame.grid(row=0, column=0, sticky="ew")
    list_panel.body.columnconfigure(0, weight=1)
    list_panel.body.rowconfigure(0, weight=1)
    bind_dynamic_wrap(list_panel.frame, root, list_panel.summary_label, padding=22, minimum=150)

    editor_panel = create_inset_panel(
        schedules_body,
        title="Editor",
        summary=editor_selection_summary(0),
        tone="accent",
    )
    editor_panel.frame.grid(row=1, column=0, sticky="ew", pady=(4, 0))
    editor_panel.body.columnconfigure(0, weight=1)
    editor_panel.body.columnconfigure(1, weight=1)
    bind_dynamic_wrap(editor_panel.frame, root, editor_panel.summary_label, padding=22, minimum=150)

    history_panel = create_inset_panel(
        schedules_card.body,
        title="Recent runs",
        summary="Refreshes automatically every 5 seconds for the selected schedule.",
    )
    history_panel.frame.grid(row=2, column=0, sticky="ew", pady=(4, 0))
    history_panel.body.columnconfigure(0, weight=1)
    bind_dynamic_wrap(history_panel.frame, root, history_panel.summary_label, padding=22, minimum=150)

    schedule_tree = ttk.Treeview(
        list_panel.body,
        columns=("label", "recurrence", "start", "enabled"),
        show="headings",
        selectmode="extended",
        height=4,
    )
    schedule_tree.heading("label", text="Label")
    schedule_tree.heading("recurrence", text="Recurrence")
    schedule_tree.heading("start", text="Start")
    schedule_tree.heading("enabled", text="Status")
    for column_name, minimum_width, _weight, anchor in SCHEDULE_TREE_COLUMN_SPECS:
        schedule_tree.column(
            column_name,
            width=minimum_width,
            minwidth=minimum_width,
            anchor=anchor,
            stretch=False,
        )
    schedule_tree.grid(row=0, column=0, sticky="nsew")
    tree_scrollbar = ttk.Scrollbar(list_panel.body, orient="vertical", command=schedule_tree.yview)
    tree_scrollbar.grid(row=0, column=1, sticky="ns")
    tree_scrollbar_x = ttk.Scrollbar(list_panel.body, orient="horizontal", command=schedule_tree.xview)
    tree_scrollbar_x.grid(row=1, column=0, sticky="ew", pady=(4, 0))
    schedule_tree.configure(yscrollcommand=tree_scrollbar.set, xscrollcommand=tree_scrollbar_x.set)

    _heading_font = tk_font.Font(family="Segoe UI", size=10, weight="bold")
    _cell_font = tk_font.Font(family="Segoe UI", size=10)
    _COL_PAD = 16  # horizontal padding per column

    def _autofit_tree_columns(event: tk.Event | None = None) -> None:
        headings = {"label": "Label", "recurrence": "Recurrence", "start": "Start", "enabled": "Status"}
        widths: dict[str, int] = {
            col: _heading_font.measure(text) + _COL_PAD
            for col, text in headings.items()
        }
        for iid in schedule_tree.get_children():
            vals = schedule_tree.item(iid, "values")
            for col, val in zip(("label", "recurrence", "start", "enabled"), vals):
                w = _cell_font.measure(str(val)) + _COL_PAD
                if w > widths[col]:
                    widths[col] = w
        for col_name, _min, _weight, anchor in SCHEDULE_TREE_COLUMN_SPECS:
            schedule_tree.column(
                col_name,
                width=widths[col_name],
                minwidth=widths[col_name],
                anchor=anchor,
                stretch=False,
            )

    def _resize_schedule_tree_columns(event: tk.Event | None = None) -> None:
        _autofit_tree_columns(event)

    schedule_layout_job: str | None = None

    def _apply_schedule_panel_layout(event: tk.Event | None = None, *, force: bool = False) -> None:
        nonlocal schedule_layout_job
        schedule_layout_job = None
        current_width = root.winfo_width() if event is None else int(getattr(event, "width", root.winfo_width()))
        stacked = use_stacked_schedule_layout(current_width)
        if not force and schedule_layout_state["stacked"] == stacked:
            return
        schedule_layout_state["stacked"] = stacked

        if stacked:
            schedules_body.columnconfigure(0, weight=1, uniform="")
            schedules_body.columnconfigure(1, weight=0, minsize=0, uniform="")
            list_panel.frame.grid_configure(row=0, column=0, sticky="ew", padx=(0, 0), pady=(0, 0))
            editor_panel.frame.grid_configure(row=1, column=0, sticky="ew", padx=(0, 0), pady=(4, 0))
            schedule_tree.configure(height=4)
        else:
            schedules_body.columnconfigure(0, weight=1, uniform="schedule_panels")
            schedules_body.columnconfigure(1, weight=1, uniform="schedule_panels")
            list_panel.frame.grid_configure(row=0, column=0, sticky="nsew", padx=(0, 4), pady=(0, 0))
            editor_panel.frame.grid_configure(row=0, column=1, sticky="nsew", padx=(0, 0), pady=(0, 0))
            schedule_tree.configure(height=5)

        root.after_idle(_resize_schedule_tree_columns)

    def _queue_schedule_panel_layout(event: tk.Event | None = None) -> None:
        nonlocal schedule_layout_job
        if event is not None and event.widget is not root:
            return
        if schedule_layout_job is not None:
            try:
                root.after_cancel(schedule_layout_job)
            except tk.TclError:
                pass
        schedule_layout_job = root.after(75, _apply_schedule_panel_layout)

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

    def _draft_from_schedule_form(
        schedule_id: str | None = None,
        enabled: bool = True,
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

    def _set_editor_state(state) -> None:
        for widget in widgets_to_toggle:
            try:
                if isinstance(widget, ttk.Combobox):
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
        general_details_var.set(_general_status_details(_preview_config()))

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
        root.after_idle(_autofit_tree_columns)

    def _refresh_history(schedule_id: str | None) -> None:
        history_list.configure(state="normal")
        history_list.delete(0, "end")
        if schedule_id is None:
            history_list.configure(state="disabled")
            return
        try:
            from selfsnap.records import get_by_schedule

            with connect(paths.db_path) as conn:
                records = get_by_schedule(conn, schedule_id, limit=5)
            for record in records:
                ts = format_local_timestamp(record.started_utc or record.created_utc or "")
                icon = {
                    "success": "✓",
                    "failed": "✗",
                    "missed": "–",
                    "skipped": "○",
                }.get(record.outcome_category, "?")
                history_list.insert("end", f"{icon}  {ts}  {record.outcome_code}")
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

    def _cancel_config_poll() -> None:
        nonlocal config_poll_job
        if config_poll_job is not None:
            try:
                root.after_cancel(config_poll_job)
            except tk.TclError:
                pass
            config_poll_job = None

    def _poll_external_config_changes() -> None:
        nonlocal config, config_poll_job
        try:
            disk_config = load_or_create_config(paths)
            if should_sync_polled_app_enabled(
                current_ui_value=app_enabled_var.get(),
                saved_value=saved_app_enabled_value["value"],
                disk_value=disk_config.app_enabled,
                local_dirty=app_enabled_dirty["value"],
            ):
                app_enabled_var.set(disk_config.app_enabled)
                saved_app_enabled_value["value"] = disk_config.app_enabled
                app_enabled_dirty["value"] = False
                config = replace(config, app_enabled=disk_config.app_enabled)
        except Exception:
            pass
        config_poll_job = root.after(CONFIG_POLL_INTERVAL_MS, _poll_external_config_changes)

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
        state = selection_state(len(selected_indices))
        _set_editor_state(state)
        editor_panel.summary_label.configure(text=editor_selection_summary(len(selected_indices)))

    def _add_schedule() -> None:
        try:
            draft = _draft_from_schedule_form(enabled=True)
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
            drafts[index] = _draft_from_schedule_form(
                schedule_id=drafts[index].schedule_id,
                enabled=drafts[index].enabled,
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

    _field_label(editor_panel.body, "Label").grid(row=0, column=0, sticky="ew")
    label_entry = ttk.Entry(editor_panel.body, textvariable=label_var)
    label_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 6))

    _field_label(editor_panel.body, "Every N").grid(row=2, column=0, sticky="ew")
    _field_label(editor_panel.body, "Unit").grid(row=2, column=1, sticky="ew", padx=(4, 0))
    every_spinbox = tk.Spinbox(
        editor_panel.body,
        from_=1,
        to=999999,
        textvariable=every_var,
        width=9,
        relief="solid",
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
        highlightcolor=ACCENT_COLOR,
    )
    every_spinbox.grid(row=3, column=0, sticky="w", pady=(4, 6))
    unit_combo = ttk.Combobox(
        editor_panel.body,
        textvariable=unit_var,
        values=unit_labels(),
        state="readonly",
    )
    unit_combo.grid(row=3, column=1, sticky="ew", padx=(4, 0), pady=(4, 6))

    _field_label(editor_panel.body, "Start date").grid(row=4, column=0, sticky="ew")
    _field_label(editor_panel.body, "Start time").grid(row=4, column=1, sticky="ew", padx=(4, 0))
    start_date_entry = ttk.Entry(editor_panel.body, textvariable=start_date_var)
    start_date_entry.grid(row=5, column=0, sticky="ew", pady=(4, 6))
    start_time_entry = ttk.Entry(editor_panel.body, textvariable=start_time_var)
    start_time_entry.grid(row=5, column=1, sticky="ew", padx=(4, 0), pady=(4, 6))

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
    save_schedule_button.pack(side="right", padx=(0, 4))
    add_button.pack(side="right", padx=(0, 4))

    history_list = tk.Listbox(
        history_panel.body,
        height=2 if use_stacked_compact_layout else 3,
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
    list_btn_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))
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
    schedule_tree.bind("<Configure>", _autofit_tree_columns, add="+")
    root.bind("<Configure>", _queue_schedule_panel_layout, add="+")
    _apply_schedule_panel_layout(force=True)
    _refresh_tree([])
    root.after_idle(_autofit_tree_columns)
    _load_draft_to_form(_new_default_draft())
    _set_editor_state(selection_state(0))
    editor_panel.summary_label.configure(text=editor_selection_summary(0))
    history_refresh_job = root.after(HISTORY_REFRESH_INTERVAL_MS, _poll_history)

    diagnostics_grid = tk.Frame(diagnostics_tab, bg=WINDOW_BG)
    diagnostics_grid.grid(row=0, column=0, sticky="ew")
    diagnostics_grid.columnconfigure(0, weight=1)
    diagnostics_grid.columnconfigure(1, weight=1)

    diagnostic_cards: dict[str, tuple[SectionBlock, tk.Label]] = {}

    def _make_diagnostic_card(
        key: str,
        title: str,
        row_index: int,
        column_index: int,
    ) -> None:
        card = create_card(
            diagnostics_grid,
            title=title,
            summary="Loading…",
            badge_text="Info",
            tone="info",
        )
        card.frame.grid(
            row=row_index,
            column=column_index,
            sticky="ew",
            padx=(0, 4) if column_index == 0 else (0, 0),
            pady=(0, 4),
        )
        bind_dynamic_wrap(card.frame, root, card.summary_label, padding=32, minimum=150)
        detail_label = _helper_label(card.body, "")
        detail_label.grid(row=0, column=0, sticky="ew")
        bind_dynamic_wrap(card.body, root, detail_label, padding=26, minimum=150)
        diagnostic_cards[key] = (card, detail_label)

    _make_diagnostic_card("scheduler", "Scheduler Sync", 0, 0)
    _make_diagnostic_card("activity", "Last Activity", 0, 1)
    _make_diagnostic_card("storage", "Storage", 1, 0)
    _make_diagnostic_card("retention", "Retention", 1, 1)
    _make_diagnostic_card("notifications", "Notifications", 2, 0)
    _make_diagnostic_card("operations", "Operational Context", 2, 1)
    diagnostic_card_order = [
        diagnostic_cards["scheduler"][0],
        diagnostic_cards["activity"][0],
        diagnostic_cards["storage"][0],
        diagnostic_cards["retention"][0],
        diagnostic_cards["notifications"][0],
        diagnostic_cards["operations"][0],
    ]

    maintenance_card = create_card(
        maintenance_tab,
        title="Maintenance",
        summary=maintenance_summary_text(),
        badge_text="Danger zone",
        tone="danger",
    )
    maintenance_card.frame.grid(row=0, column=0, sticky="ew")
    bind_dynamic_wrap(maintenance_card.frame, root, maintenance_card.summary_label, padding=32)
    maintenance_card.body.columnconfigure(0, weight=1)

    maintenance_message = _helper_label(
        maintenance_card.body,
        text=(
            "Reset Capture History permanently deletes SelfSnap capture/archive files, "
            "database history, logs, schedules, and local user settings, then relaunches first run."
        ),
        foreground=DANGER_FG,
    )
    maintenance_message.grid(row=0, column=0, sticky="ew")
    bind_dynamic_wrap(maintenance_card.body, root, maintenance_message, padding=26, minimum=180)

    tray_actions_note = _helper_label(
        maintenance_card.body,
        "Reinstall, update checks, restart, and uninstall remain available from the tray menu.",
    )
    tray_actions_note.grid(row=1, column=0, sticky="ew", pady=(6, 0))
    bind_dynamic_wrap(maintenance_card.body, root, tray_actions_note, padding=26, minimum=180)

    result = SettingsDialogResult(
        updated_config=None,
        window_size=(window_width, window_height),
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
        _cancel_config_poll()
        result.window_size = _capture_size()
        result.requested_reset = True
        root.destroy()

    ttk.Button(
        maintenance_card.body,
        text="Reset Capture History",
        command=_request_reset,
        style="Wide.TButton",
    ).grid(row=2, column=0, sticky="w", pady=(6, 0))

    responsive_layout_job: str | None = None
    general_layout_state = {"stacked": use_stacked_settings_card_layout(window_width)}
    storage_layout_state = {"stacked": use_stacked_settings_card_layout(window_width)}
    diagnostics_layout_state = {"stacked": use_stacked_settings_card_layout(window_width)}

    def _apply_general_layout(current_width: int, *, force: bool = False) -> None:
        stacked = use_stacked_settings_card_layout(current_width)
        if not force and general_layout_state["stacked"] == stacked:
            return
        general_layout_state["stacked"] = stacked
        _configure_card_pair_layout(
            general_grid,
            general_status_card,
            experience_card,
            stacked=stacked,
            uniform_group="general_cards",
        )

    def _apply_storage_layout(current_width: int, *, force: bool = False) -> None:
        stacked = use_stacked_settings_card_layout(current_width)
        if not force and storage_layout_state["stacked"] == stacked:
            return
        storage_layout_state["stacked"] = stacked
        _configure_card_pair_layout(
            storage_grid,
            destinations_card,
            capture_settings_card,
            stacked=stacked,
            uniform_group="storage_cards",
        )

    def _apply_diagnostics_layout(current_width: int, *, force: bool = False) -> None:
        stacked = use_stacked_settings_card_layout(current_width)
        if not force and diagnostics_layout_state["stacked"] == stacked:
            return
        diagnostics_layout_state["stacked"] = stacked
        _configure_card_grid_layout(
            diagnostics_grid,
            diagnostic_card_order,
            stacked=stacked,
            uniform_group="diagnostic_cards",
        )

    def _apply_responsive_settings_layouts(
        event: tk.Event | None = None,
        *,
        force: bool = False,
    ) -> None:
        nonlocal responsive_layout_job
        responsive_layout_job = None
        current_width = (
            root.winfo_width()
            if event is None
            else int(getattr(event, "width", root.winfo_width()))
        )
        _apply_general_layout(current_width, force=force)
        _apply_storage_layout(current_width, force=force)
        _apply_diagnostics_layout(current_width, force=force)

    def _queue_responsive_settings_layouts(event: tk.Event | None = None) -> None:
        nonlocal responsive_layout_job
        if event is not None and event.widget is not root:
            return
        if responsive_layout_job is not None:
            try:
                root.after_cancel(responsive_layout_job)
            except tk.TclError:
                pass
        responsive_layout_job = root.after(75, _apply_responsive_settings_layouts)

    def _set_diagnostic_card(key: str, summary: DiagnosticSummary) -> None:
        card, detail_label = diagnostic_cards[key]
        tone_map = {"good": "accent", "warn": "warning", "neutral": "info"}
        badge_text = {"good": "Healthy", "warn": "Attention", "neutral": "Info"}[summary.tone]
        card.summary_label.configure(text=summary.headline)
        detail_label.configure(text=summary.detail)
        _set_badge(card.badge_label, badge_text, tone_map[summary.tone])

    def _refresh_dynamic_content(*_args) -> None:
        preview = _preview_config()
        status_text, status_tone = settings_header_status(preview)
        _set_badge(header.badge_label, status_text, status_tone)
        _set_badge(general_status_card.badge_label, status_text, status_tone)
        general_status_card.summary_label.configure(text=latest_capture_var.get())
        general_details_var.set(_general_status_details(preview))
        experience_card.summary_label.configure(text=_experience_summary(preview))
        storage_overview_card.summary_label.configure(text=_storage_overview_summary(preview))
        destinations_card.summary_label.configure(text=_destinations_summary(preview))
        capture_settings_card.summary_label.configure(text=_capture_settings_summary(preview))
        scheduler_notice_label.configure(text=scheduler_status_detail(preview) or "")
        _set_diagnostic_card("scheduler", scheduler_sync_summary(preview))
        _set_diagnostic_card("activity", last_activity_summary(latest_record))
        for key, builder in (
            ("storage", lambda: storage_summary(preview, paths)),
            ("retention", lambda: retention_summary(preview)),
            ("notifications", lambda: notification_summary(preview)),
            ("operations", lambda: operational_summary(preview, paths)),
        ):
            try:
                summary = builder()
            except (ConfigValidationError, ValueError) as exc:
                summary = DiagnosticSummary(
                    headline="Pending validation",
                    detail=str(exc),
                    tone="warn",
                )
            _set_diagnostic_card(key, summary)

    action_row = tk.Frame(root, bg=WINDOW_BG, padx=10, pady=8)
    action_row.grid(row=1, column=0, sticky="ew")

    def _apply_settings() -> None:
        nonlocal config
        if len(selected_indices) == 1:
            try:
                drafts[selected_indices[0]] = _draft_from_schedule_form(
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
                app_enabled=app_enabled_var.get()
                if config.first_run_completed
                else config.app_enabled,
                storage_preset=storage_preset_value(preset_var.get().strip()),
                capture_storage_root=storage_path_from_display(paths, capture_root_var.get()),
                archive_storage_root=storage_path_from_display(paths, archive_root_var.get()),
                retention_mode=retention_mode,
                retention_days=retention_days,
                purge_enabled=purge_enabled_var.get(),
                retention_grace_days=int(retention_grace_days_var.get())
                if retention_grace_days_var.get().strip().isdigit()
                else config.retention_grace_days,
                capture_mode=capture_mode_value(capture_mode_var.get()),
                image_format=image_format_value(image_format_var.get()),
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
        config = updated
        saved_app_enabled_value["value"] = updated.app_enabled
        app_enabled_dirty["value"] = False
        result.updated_config = updated
        result.window_size = _capture_size()
        _refresh_tree(select=selected_indices[:1] if selected_indices else [])
        _save_btn.configure(text="Saved")
        root.after(1500, lambda: _save_btn.configure(text="Save"))

    def _cancel() -> None:
        _cancel_history_poll()
        _cancel_config_poll()
        result.window_size = _capture_size()
        root.destroy()

    _save_btn = ttk.Button(action_row, text="Save", command=_apply_settings, style="Wide.TButton")
    _save_btn.pack(side="right")
    ttk.Button(action_row, text="Close", command=_cancel, style="Wide.TButton").pack(
        side="right",
        padx=(0, 8),
    )

    for variable in (
        app_enabled_var,
        preset_var,
        capture_root_var,
        archive_root_var,
        retention_mode_var,
        retention_days_var,
        capture_mode_var,
        image_format_var,
        image_quality_var,
        purge_enabled_var,
        retention_grace_days_var,
        start_tray_on_login_var,
        wake_for_scheduled_captures_var,
        show_last_capture_status_var,
        notify_on_failed_or_missed_var,
        notify_on_every_capture_var,
        show_capture_overlay_var,
    ):
        variable.trace_add("write", _refresh_dynamic_content)

    preset_combo.bind(
        "<<ComboboxSelected>>", lambda _event: _set_preset_from_label(preset_var.get())
    )
    capture_root_var.trace_add("write", _mark_custom)
    archive_root_var.trace_add("write", _mark_custom)
    root.bind("<Configure>", _queue_responsive_settings_layouts, add="+")
    _update_path_state()
    _apply_responsive_settings_layouts(force=True)
    _refresh_dynamic_content()
    _poll_external_config_changes()
    root.protocol("WM_DELETE_WINDOW", _cancel)
    root.mainloop()
    return result


def _browse_directory(parent: tk.Tk, target: tk.StringVar, paths: AppPaths) -> None:
    initial_dir = storage_path_from_display(paths, target.get()) or None
    chosen = filedialog.askdirectory(parent=parent, initialdir=initial_dir)
    if chosen:
        target.set(storage_path_for_display(paths, chosen))


def _latest_capture_summary(record: CaptureRecord | None) -> str:
    if record is None:
        return "Latest capture: none yet"
    timestamp_utc = record.started_utc or record.created_utc or ""
    return f"Latest capture: {record.outcome_code} at {format_local_timestamp(timestamp_utc)}"