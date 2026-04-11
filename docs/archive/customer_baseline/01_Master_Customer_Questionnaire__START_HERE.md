# 01 — Master Customer Questionnaire (Start Here)

## 1. Vision

- Vision statement:
  Build a lightweight Windows 11 desktop tool that automatically captures scheduled screenshots for personal self-observation, behavioral review, and local recordkeeping without becoming intrusive, bloated, or privacy-hostile.

- One-sentence summary:
  I want a local-first Windows 11 utility that takes screenshots at configured times so I can later review what was on my screen and better understand my actual computer-use patterns.

- Confidence tag:
  **[CONFIDENT]**

---

## 2. Outcome

- Primary outcome:
  The software should create a reliable local record of screen state at selected times.

- Secondary outcomes:
  - Support self-observation and personal review.
  - Reduce the need for memory or manual note-taking about what I was doing.
  - Create a lightweight behavioral data source that can later inform a more advanced product.

- What changes for the user after this exists?
  The user no longer has to rely only on memory or ad hoc manual screenshots. A usable record exists automatically.

- Confidence tag:
  **[CONFIDENT]**

---

## 3. User

- Primary user:
  One technical personal user.

- Secondary users:
  Potentially other developers or self-tracking users later, but not in v1 planning.

- Environment:
  Personal Windows 11 machine, likely a desktop or laptop workstation.

- Technical comfort level:
  Comfortable with Python and development tools, but still wants a user-facing tool that behaves cleanly.

- Confidence tag:
  **[CONFIDENT]**

---

## 4. Platform

- Mandatory platform(s):
  Windows 11.

- Optional future platform(s):
  Windows 10 later, only if worth it after the Windows 11 version is solid.

- Excluded for v1:
  macOS, Linux, mobile, Windows XP, Windows Vista, and any cross-platform promise.

- Confidence tag:
  **[CONFIDENT]**

---

## 5. Core behavior

- Core behavior sentence:
  The software should run as a lightweight Windows 11 background utility and take screenshots automatically at user-configured times.

- Required behavior bullets:
  - [x] Capture the current desktop state at configured times.
  - [x] Support all currently connected monitors.
  - [x] Save a composite image locally.
  - [x] Save metadata and logs locally.
  - [x] Allow manual capture.
  - [x] Provide transparent control over enable / disable state.
  - [x] Report failure states honestly instead of pretending that every failed screenshot means the machine was off.

- Things the user can control:
  - schedule times,
  - enable / disable state,
  - manual capture,
  - storage path,
  - retention behavior,
  - whether best-effort wake should be attempted.

- Things that must happen automatically:
  - scheduled triggering,
  - capture attempt,
  - metadata write,
  - log write,
  - retention cleanup if enabled.

- Confidence tag:
  **[CONFIDENT]**

---

## 6. Data

- Data produced by the product:
  - screenshot image files,
  - composite screenshot output,
  - per-capture metadata,
  - logs,
  - configuration data.

- Where data should be stored:
  Local machine only in v1.

- Who should access it:
  The current user only, through normal local-machine access.

- Any data-sharing restrictions:
  No cloud sync, no remote upload, no stealth forwarding in v1.

- Confidence tag:
  **[CONFIDENT]**

---

## 7. Privacy and trust

- Sensitive concerns:
  Screenshots may contain messages, credentials visible on-screen, personal content, private browsing, financial information, or work-related material.

- What must be visible to the user:
  The app should have visible control and should not behave as hidden surveillance software.

- What should never happen:
  - silent cloud upload,
  - hidden monitoring mode,
  - misleading status reporting,
  - pretending that all black or failed captures mean “computer off.”

- Confidence tag:
  **[CONFIDENT]**

---

## 8. Success

1. The user can configure the tool and get reliable scheduled captures on Windows 11 without constant manual intervention.
2. The product stays lightweight and transparent enough to feel acceptable as a background utility.
3. The stored outputs are useful for later review and the failure cases are recorded honestly.

- Nice-to-have success indicators:
  - setup is quick,
  - storage remains organized,
  - the app can optionally attempt wake-from-sleep where supported,
  - future productization still looks plausible.

- Confidence tag:
  **[CONFIDENT]**

---

## 9. Non-goals

- Out of scope for v1:
  - [x] macOS support
  - [x] Linux support
  - [x] mobile support
  - [x] browser-extension-only implementation
  - [x] enterprise administration features
  - [x] cloud sync
  - [x] stealth monitoring
  - [x] Windows service architecture
  - [x] guaranteed capture from full shutdown
  - [x] in-app analytics dashboard

- Deferred for later:
  - richer review UI,
  - search and tagging,
  - cross-device sync,
  - cross-platform packaging,
  - more advanced behavior analysis.

- Confidence tag:
  **[CONFIDENT]**

---

## 10. Open questions

- [OPEN QUESTION] Should per-monitor images be mandatory in v1 or only optional alongside the composite image?
- [OPEN QUESTION] Is a tray-only review flow sufficient, or is a small in-app history view worth adding?
- [OPEN QUESTION] Should local storage encryption be a v1 requirement or a later hardening step?

---

## Completion check

- [x] I wrote the vision in plain language.
- [x] I separated outcomes from implementation.
- [x] I wrote at least 3 success criteria.
- [x] I wrote at least 5 non-goals.
- [x] I marked open questions honestly.
