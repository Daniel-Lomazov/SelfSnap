from __future__ import annotations

from selfsnap.models import AppConfig
from selfsnap.tray.settings_window import show_settings_dialog


def test_show_settings_dialog_builds_without_runtime_name_errors(temp_paths, monkeypatch) -> None:
    config = AppConfig(
        capture_storage_root=str(temp_paths.default_capture_root),
        archive_storage_root=str(temp_paths.default_archive_root),
    )

    def _close_immediately(self) -> None:
        self.update_idletasks()
        self.destroy()

    monkeypatch.setattr("tkinter.Tk.mainloop", _close_immediately)

    result = show_settings_dialog(config, temp_paths)

    assert result.updated_config is None
    assert result.requested_reset is False
