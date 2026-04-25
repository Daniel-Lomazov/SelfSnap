# 05 — Scope, Constraints, and Non-Goals

[ARCHIVED BASELINE]
This file is part of the original customer baseline pack preserved in [README.md](README.md).
It is historical reference material and not the active product or maintainer contract.

## 1. In-scope for v1

### Platform scope
- Windows 11 only
- normal logged-in desktop usage context
- personal-machine-first assumptions

### Functional scope
- scheduled time-based screenshot capture
- capture of all connected displays
- composite image output
- local metadata and logs
- manual capture action
- enable / disable and pause control

### Control scope
- lightweight tray-style control surface or equivalent small control UI
- schedule editing
- storage path editing
- review of latest status or latest result path

### Data scope
- local-only storage
- user-controlled storage path
- optional retention rules
- no remote upload

---

## 2. Out of scope for v1

### Excluded platforms
- macOS
- Linux
- mobile
- Windows XP / Vista compatibility targets

### Excluded features
- cloud sync
- stealth capture mode
- enterprise admin controls
- advanced analytics dashboard
- full in-app history browser if it delays MVP
- guaranteed capture from full shutdown

### Excluded deployment / business modes
- enterprise deployment
- cross-platform commercial release
- browser-extension-only implementation

---

## 3. Constraints

### Platform constraints
- Must work on Windows 11.

### Technical constraints
- Customer strongly prefers Python-first development for v1.
- The product should not be designed as a Windows service for desktop capture behavior.

### Privacy constraints
- Local-only storage in v1.
- User-visible control is mandatory.
- Stealth behavior is not allowed.

### Operational constraints
- Must behave like a lightweight background utility.
- Must record honest outcomes instead of misleading inferred states.
- Full shutdown should not be treated as a capturable state.

### Time / budget constraints
- MVP should stay lean and avoid unnecessary platform or feature expansion.

---

## 4. Preferences

- Preference:
  Python-first implementation.

- Reason:
  Faster learning, faster iteration, stronger personal ownership, and a better path for self-maintenance.

- Negotiable?
  Maybe

---

- Preference:
  Tray app plus one-shot worker architecture.

- Reason:
  Seems well aligned with Windows utility behavior and scheduled execution.

- Negotiable?
  Yes

---

- Preference:
  Composite plus optional per-monitor outputs.

- Reason:
  Composite is easiest to review; per-monitor outputs may add clarity later.

- Negotiable?
  Yes

---

- Preference:
  Best-effort wake-from-sleep support.

- Reason:
  It increases usefulness but should not distort the MVP if it becomes complex.

- Negotiable?
  Yes

---

## 5. Assumptions

- Assumption 1:
  The user will run the product on Windows 11 in a standard desktop environment.

- Assumption 2:
  The user is willing to store screenshots locally.

- Assumption 3:
  A logged-in user session is the normal execution context.

- Assumption 4:
  The first serious use case is personal self-observation rather than enterprise oversight.

---

## 6. Deferred items

- Deferred item 1:
  Cross-platform support

- Deferred item 2:
  Rich history browser

- Deferred item 3:
  Search and tagging

- Deferred item 4:
  Cloud sync or remote backup

- Deferred item 5:
  Advanced interpretation or analytics layer

---

## 7. Non-goals

- Non-goal 1:
  Build a general surveillance product.

- Non-goal 2:
  Build a cross-platform suite in the first version.

- Non-goal 3:
  Guarantee capture from all power states.

- Non-goal 4:
  Solve deep behavior analysis in the MVP.

- Non-goal 5:
  Turn the MVP into an enterprise-managed system.

---

## 8. Boundary tests

- If the team delivered only the in-scope items, would the result still be useful?
  Yes. A Windows 11 utility with scheduled local capture, metadata, and transparent control would already validate the concept.

- Is any major user value currently hiding inside “deferred” without being admitted?
  Not obviously. The deferred items are enhancements, not the core value itself.

- Is any item currently called “must-have” actually a preference?
  The Python-first implementation is a strong preference but not a pure product requirement. It should remain challengeable if a compelling alternative is proposed.

- Have we accidentally included future-platform ambitions in v1?
  No. Those have been explicitly excluded.

- Is privacy visible enough in the scope?
  Yes, because local-only storage, user-visible control, and anti-stealth positioning are explicit.

---

## 9. Final boundary statement

- For v1, this project will deliver a lightweight Windows 11 local screenshot utility, on personal desktop usage contexts, for a single initial user, while explicitly not attempting cross-platform support, stealth behavior, cloud sync, enterprise management, or guaranteed capture from full shutdown.
