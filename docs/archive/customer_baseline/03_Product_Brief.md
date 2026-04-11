# 03 — Product Brief

## 1. Product identity

- Product name:
  SelfSnap Win11

- One-line description:
  A lightweight Windows 11 background utility that captures local screenshots at configured times for personal review.

- Internal code name, if any:
  SelfSnap

---

## 2. Problem statement

Today, there is no simple, trustworthy, local-first utility in this project context that automatically records what was on the screen at chosen times. The current alternatives are memory, manual screenshots, or not collecting the information at all. That creates friction and makes later reflection unreliable.

---

## 3. Opportunity

Software is the right answer because the desired behavior is repetitive, time-based, and better handled automatically than manually. A scheduled screenshot utility is a narrow but practical way to generate a concrete record without requiring continuous active effort from the user. The opportunity is attractive now because the first version can be small, useful, and directly informative about whether broader personal-data tooling is worth building.

---

## 4. Target user

- Primary user:
  One technically capable personal user.

- Secondary user:
  Potential later users with similar self-observation or productivity-review needs, but not relevant to v1 delivery.

- User environment:
  Personal Windows 11 desktop or laptop.

- User technical sophistication:
  Comfortable with development tools, but still benefits from clean user-facing behavior.

- Any special habits or constraints:
  May use multiple monitors. May allow the machine to sleep. Prefers local control and low friction.

---

## 5. User outcome

- Primary outcome:
  After using this product, the user can review what was on the screen at scheduled times without relying on memory.

- Secondary outcome:
  After using this product, the user can build a local record of screen-state history for self-review.

- Nice-to-have outcomes:
  - clearer understanding of usage patterns,
  - foundation for later behavior analysis,
  - faster recall of what was being worked on.

---

## 6. Product promise

- This product helps the user automatically collect trustworthy local screen snapshots at chosen times while staying lightweight, transparent, and easy to control.

---

## 7. Core value

### Main value
Reliable automatic local capture of screen state at configured times.

### Secondary value
A practical foundation for future self-tracking or workflow-analysis software.

### Emotional / practical value
More clarity, less dependence on memory, more confidence that important moments or states were not lost.

---

## 8. v1 shape

- Minimum useful version:
  A Windows 11 tray-style utility with scheduled capture, manual capture, local storage, composite output, metadata, and transparent control.

- Required capabilities:
  - schedule one or more daily capture times,
  - capture current desktop state,
  - support all connected monitors,
  - save results locally,
  - log honest status outcomes,
  - allow manual capture and disable / pause control.

- Optional early extras:
  - per-monitor saved files,
  - best-effort wake-from-sleep,
  - simple last-result view.

- What can wait until later:
  - richer history browser,
  - analytics,
  - search,
  - tagging,
  - cross-platform support,
  - cloud sync.

---

## 9. Experience principles

- [x] lightweight
- [x] transparent
- [x] reliable
- [x] quiet
- [x] configurable
- [x] privacy-conscious
- [x] simple to install
- [x] simple to disable
- [x] unobtrusive
- [x] honest about failures

Explain the selected principles:
The product should feel like a disciplined utility, not a research prototype leaking internal complexity into the user experience. It should not demand constant attention, should not hide what it is doing, and should not turn uncertainty into false confidence.

---

## 10. Non-goals

- Non-goal 1:
  Become a cross-platform desktop suite in v1.

- Non-goal 2:
  Become a stealth monitoring tool.

- Non-goal 3:
  Become a cloud-synced data platform in v1.

- Non-goal 4:
  Become an enterprise-managed compliance product.

- Non-goal 5:
  Solve advanced behavior analysis in the initial version.

---

## 11. Success definition

This product is worth continuing if:
- it works reliably enough to be used in real life on Windows 11,
- the outputs are actually useful for later review,
- the product still feels clean and lightweight rather than burdensome.

Specific proof points:
- scheduled captures happen and are stored locally as expected,
- the user can tell whether the app is enabled and can control it easily,
- logs and metadata make failure conditions understandable.

---

## 12. Open product questions

- [OPEN QUESTION] Is a tiny built-in history viewer worth the extra effort in v1?
- [OPEN QUESTION] Is wake-from-sleep a core selling point or just an optional enhancement?
- [OPEN QUESTION] Should encryption-at-rest be positioned as a future hardening step or included early?
