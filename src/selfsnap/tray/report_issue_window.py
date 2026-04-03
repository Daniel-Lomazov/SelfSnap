from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk

from selfsnap.issue_reporting import submit_issue_report
from selfsnap.paths import AppPaths

WINDOW_MIN_WIDTH = 760
WINDOW_MIN_HEIGHT = 480


@dataclass(slots=True)
class ReportIssueDialogResult:
    submitted: bool = False
    issue_url: str | None = None


def show_report_issue_dialog(paths: AppPaths) -> ReportIssueDialogResult:
    root = tk.Tk()
    root.title("Report SelfSnap Issue")
    root.geometry(f"{WINDOW_MIN_WIDTH}x{WINDOW_MIN_HEIGHT}")
    root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
    root.resizable(True, True)

    result = ReportIssueDialogResult()
    include_diagnostics_var = tk.BooleanVar(value=True)

    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)

    header = ttk.Frame(root, padding=(16, 16, 16, 0))
    header.grid(row=0, column=0, sticky="ew")
    header.columnconfigure(0, weight=1)

    intro = ttk.Label(
        header,
        text=(
            "Describe the problem in a short paragraph. SelfSnap stays offline "
            "unless you explicitly open feedback in the browser. It never "
            "attaches screenshots, local file paths, logs, or database contents "
            "automatically, and it shares only safe diagnostics when you leave "
            "that option enabled."
        ),
        justify="left",
        wraplength=680,
    )
    intro.grid(row=0, column=0, sticky="ew")

    text_frame = ttk.Frame(root, padding=(16, 12, 16, 0))
    text_frame.grid(row=1, column=0, sticky="nsew")
    text_frame.columnconfigure(0, weight=1)
    text_frame.rowconfigure(0, weight=1)

    description_text = tk.Text(text_frame, wrap="word", height=12)
    description_text.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=description_text.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    description_text.configure(yscrollcommand=scrollbar.set)

    options = ttk.Frame(root, padding=(16, 12, 16, 0))
    options.grid(row=2, column=0, sticky="ew")
    options.columnconfigure(0, weight=1)
    ttk.Checkbutton(
        options,
        text="Include safe diagnostics in the report",
        variable=include_diagnostics_var,
    ).grid(row=0, column=0, sticky="w")

    footer = ttk.Frame(root, padding=(16, 12))
    footer.grid(row=3, column=0, sticky="ew")

    def _submit() -> None:
        description = description_text.get("1.0", "end").strip()
        if not description:
            messagebox.showerror(
                "Report Issue", "Please describe the issue before submitting.", parent=root
            )
            return
        issue_result = submit_issue_report(
            paths,
            description,
            include_diagnostics=include_diagnostics_var.get(),
        )
        if not issue_result.ok:
            messagebox.showerror("Report Issue", issue_result.message, parent=root)
            return
        result.submitted = True
        result.issue_url = issue_result.issue_url
        messagebox.showinfo("Report Issue", issue_result.message, parent=root)
        root.destroy()

    ttk.Button(footer, text="Cancel", command=root.destroy).pack(side="right")
    ttk.Button(footer, text="Open GitHub Issue", command=_submit).pack(side="right", padx=(0, 8))

    root.after_idle(description_text.focus_set)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
    return result
