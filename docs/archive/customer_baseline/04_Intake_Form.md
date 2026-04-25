# 04 — Customer Intake Form

[ARCHIVED BASELINE]
This file is part of the original customer baseline pack preserved in [README.md](README.md).
It is historical reference material and not the active product or maintainer contract.

## A. Problem and intent

- What triggered this project?
  A desire to automatically collect a small but concrete form of personal activity data using screenshots, starting from a narrow and useful case.

- What do you want the product to help you observe, capture, automate, or verify?
  I want it to automatically capture what was on my screen at chosen times so I can later review real screen-state evidence rather than relying on memory.

- Why is this useful in real life?
  It provides an objective local record that may support self-observation, recall, and future product ideas around personal data collection.

Example / scenario:
- At 14:00 every day, the app captures what is currently visible on the desktop and stores it locally so I can later check what I was actually working on.

---

## B. Current workflow

- How do you handle this today, if at all?
  There is no reliable workflow. Manual screenshots are possible but inconsistent and easy to forget.

- What is inconvenient, missing, repetitive, unreliable, or impossible?
  Manual effort breaks the idea. Memory is incomplete. There is no consistent, structured local record.

- What manual workaround currently exists?
  Occasional deliberate screenshots, which are too inconsistent to count as a system.

Example / scenario:
- By the time I remember to take a screenshot, the relevant state may already be gone.

---

## C. Expected automatic behavior

What should the software do without the user manually triggering it?

- [x] scheduled action
- [x] startup behavior
- [x] background operation
- [x] retention cleanup
- [x] logging
- [x] status recording

Describe:
- The app should register or maintain scheduled capture behavior.
- At configured times, it should attempt a screenshot capture.
- It should save local outputs and metadata.
- It should log what happened.
- If retention is enabled, it should clean older items according to policy.
- The app should remain available as a lightweight background utility.

---

## D. Expected manual behavior

What should the user be able to do directly?

- [x] capture now
- [x] enable / disable
- [x] pause temporarily
- [x] open output folder
- [x] view last result
- [x] edit schedule
- [x] edit storage path

Describe:
- The user should be able to trigger a manual capture immediately.
- The user should be able to disable scheduled capture or pause it temporarily.
- The user should be able to open the capture folder and review the most recent outcome.
- The user should be able to edit at least the schedule and storage path.

---

## E. Platform and environment

- Mandatory OS:
  Windows 11

- Optional later OS:
  Windows 10 only if later justified

- Device type:
  Desktop or laptop

- Single monitor / multi-monitor:
  Multi-monitor support desired in v1

- Personal machine / work machine:
  Personal machine in the current project

- Logged-in session only?
  Yes, assume a normal logged-in user session for v1

- Typical power state patterns:
  Machine may sleep; full shutdown should be treated separately

- Any environment constraints:
  The product should behave like a real Windows background utility and should not rely on a browser context.

---

## F. Scheduling

- How should the user define time?
  Via configured daily times in local machine time.

- One time or multiple times?
  Multiple times should be supported eventually; a single time is sufficient for the earliest MVP if that simplifies validation.

- Daily / weekly / custom?
  Daily is the required starting mode.

- What timezone assumptions apply?
  Local machine timezone is sufficient for v1.

- What should happen if a scheduled time is missed?
  The event should be recorded honestly, not silently ignored.

- What should happen if the machine is asleep?
  Best-effort wake may be attempted if supported and enabled. If not captured, record the outcome honestly.

- What should happen if it is fully powered off?
  No fake black screenshot should be fabricated. Record as missed / unavailable / off-state as appropriate.

Use explicit statements:
- Mandatory:
  - scheduled capture at configured local times,
  - honest event recording,
  - no misleading inference from failed captures.

- Preferred:
  - support more than one daily time,
  - optional wake-from-sleep.

- Open questions:
  - whether missed events should be retried immediately after wake,
  - how aggressively wake behavior should be exposed in v1.

---

## G. Capture rules

- What exactly should be captured?
  The current visible desktop state across all connected monitors.

- All screens or selected screens?
  All connected monitors in v1.

- Separate files or one composite?
  Composite image is mandatory. Separate per-monitor outputs are preferred if easy.

- Is a locked screen acceptable as a result?
  The app should record honestly what could be captured in that state; it should not invent semantics beyond what actually happened.

- What should happen if protected content appears?
  The system should record honest status rather than assuming all content is capturable.

- Should black or empty capture ever be interpreted automatically?
  No. Black or failed capture should not be simplistically interpreted as “computer off.”

---

## H. Data and storage

- Output type(s):
  Screenshot image files, metadata records, logs, and configuration data.

- Local-only or remote?
  Local-only in v1.

- Default storage location preference:
  User-configurable local folder.

- Metadata required?
  Yes.

- Retention policy:
  User-configurable. Keep-forever and simple retention rules should both be considered.

- Should old captures auto-delete?
  Optional based on retention setting.

- Any naming convention preferences?
  Timestamp-based names are preferred.

- Any indexing or search expectation?
  Minimal indexing is useful. Full search is not required in v1.

---

## I. User review and control

- Is “open folder” sufficient for v1?
  Yes, likely sufficient.

- Is an in-app gallery needed?
  No, not required for v1.

- Should the app always show whether it is enabled?
  Yes.

- Is a tray icon acceptable?
  Yes, and likely the preferred control surface.

- Must the user be able to pause with one action?
  Yes.

---

## J. Privacy and trust boundaries

- What sensitive data may appear?
  Private messages, emails, credentials visible on-screen, financial data, personal browsing, work-related information, and any other visible desktop content.

- What must never happen?
  - hidden surveillance mode,
  - cloud upload in v1,
  - false status reporting,
  - uncontrolled sharing.

- Is cloud sync forbidden in v1?
  Yes.

- Is stealth or hidden operation forbidden?
  Yes.

- Should the user always know when the product is active?
  Yes.

---

## K. Performance expectations

- Target for idle impact:
  Low enough to feel negligible in daily use.

- Acceptable startup delay:
  Short and unobtrusive.

- Acceptable capture duration:
  Fast enough to complete without obvious friction during normal desktop use.

- Any unacceptable resource use:
  High constant CPU use, noticeable memory bloat, or behavior that makes the app feel heavy.

---

## L. Mandatory requirements

- Must-have 1:
  Windows 11 support.

- Must-have 2:
  Scheduled screenshot capture.

- Must-have 3:
  Local-only storage in v1.

- Must-have 4:
  Transparent enable / disable control.

- Must-have 5:
  Honest status and failure recording.

---

## M. Preferences / hypotheses

- Preference:
  Python-first implementation.

- Why you currently prefer it:
  Fast iteration, alignment with current personal development workflow, and easier self-ownership of the codebase.

- Whether it is negotiable:
  Somewhat negotiable later, but strongly preferred for v1.

---

- Preference:
  Tray app plus background worker shape.

- Why you currently prefer it:
  It feels like the right Windows utility form for this project.

- Whether it is negotiable:
  Yes, if a better Windows-native shape is justified.

---

- Preference:
  Composite image plus per-monitor outputs if feasible.

- Why you currently prefer it:
  Composite is easiest to review; per-monitor files may be operationally useful.

- Whether it is negotiable:
  Yes.

---

## N. Nice-to-haves

- Nice-to-have 1:
  Best-effort wake-from-sleep support.

- Nice-to-have 2:
  Per-monitor saved files.

- Nice-to-have 3:
  Simple last-result view.

- Nice-to-have 4:
  More than one daily time in the early usable version.

---

## O. Unacceptable outcomes

- Unacceptable outcome 1:
  The app behaves like hidden surveillance software.

- Unacceptable outcome 2:
  The app silently uploads screenshots anywhere.

- Unacceptable outcome 3:
  The app pretends to know why capture failed when it does not.

- Unacceptable outcome 4:
  The app becomes heavy, annoying, or operationally fragile.

---

## P. Open operational questions

- [OPEN QUESTION] Should retention cleanup run immediately after each capture or on a separate housekeeping pass?
- [OPEN QUESTION] Should missed events after sleep be marked only, or optionally retried?
- [OPEN QUESTION] Should the first MVP store only composite output if that materially simplifies delivery?
