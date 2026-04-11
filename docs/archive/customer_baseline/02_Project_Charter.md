# 02 — Project Charter

## 1. Project information

- Project name:
  SelfSnap Win11

- Internal short name:
  SelfSnap

- Document version:
  v0.1 customer charter

- Date:
  2026-03-19

- Customer / sponsor:
  Daniel

- Project owner:
  Daniel

- Intended product / delivery lead:
  To be assigned by delivery team; role required

- Intended technical lead:
  To be assigned by delivery team; role required

- Primary reviewer(s):
  Customer plus delivery lead plus technical lead

---

## 2. Project purpose

This project exists to create a lightweight Windows 11 utility that automatically captures scheduled screenshots for personal self-observation and local recordkeeping. The current alternative is manual memory, ad hoc screenshots, or no consistent record at all. The project is worth pursuing now because it is small enough to validate quickly, useful in its own right, and potentially extensible into a broader class of personal data-collection software later.

---

## 3. Business objective

- Primary objective:
  Deliver a usable Windows 11 MVP that performs scheduled desktop screenshot capture reliably and stores results locally.

- Secondary objective:
  Validate whether this type of automated local data collection is personally useful and productizable.

- What value should exist after delivery?
  The customer should have a reliable, lightweight way to capture time-based screen snapshots for later review, along with enough structure to decide whether to invest further.

---

## 4. Primary user and context

- Primary user:
  Daniel, initially as a single technical personal user.

- Secondary users:
  None required for v1. Broader users may be explored only later.

- Usage environment:
  Personal Windows 11 desktop or laptop environment with one or more monitors.

- Any notable technical profile of the user:
  Comfortable with Python and software development, but still wants the resulting product to behave like real software rather than a loose script.

---

## 5. Project summary

SelfSnap Win11 is a Windows 11-only background desktop utility that captures screenshots at configured times, stores them locally together with metadata and logs, and gives the user transparent control over scheduling and manual capture. The first useful version should be lightweight, honest about failure conditions, local-first, and simple enough for one personal user to run reliably without turning the project into an overbuilt system.

---

## 6. Initial scope

- Included in v1:
  - [x] Windows 11-only support
  - [x] scheduled screenshot capture at configured times
  - [x] support for all connected monitors
  - [x] local storage of composite screenshot output
  - [x] metadata and logging
  - [x] manual capture action
  - [x] transparent enable / disable control
  - [x] best-effort wake-from-sleep option may be included if feasible

---

## 7. Out of scope

- Excluded from v1:
  - [x] macOS and Linux support
  - [x] mobile support
  - [x] cloud sync or remote upload
  - [x] stealth or hidden surveillance behavior
  - [x] enterprise fleet management
  - [x] guaranteed capture when the machine is fully powered off
  - [x] Windows service architecture
  - [x] broad analytics or interpretation layer

---

## 8. Constraints

### Platform constraints
- Must work on Windows 11.
- No compatibility target for Windows Vista or Windows XP.
- Windows 10 may be considered later, but is not a v1 requirement.

### Technical constraints
- Customer strongly prefers a Python-first implementation for v1.
- Customer strongly prefers a lightweight desktop utility shape rather than a browser extension.
- The architecture should avoid Windows service design for interactive desktop capture behavior.

### Privacy / security constraints
- Local-only storage in v1.
- No cloud sync or remote upload in v1.
- The app must be transparent to the user and not operate as stealth software.

### Budget / time constraints
- This should remain a lean MVP effort.
- Early value and fast iteration matter more than broad platform coverage.

### Operational constraints
- Expected to run in a logged-in user context.
- Should tolerate normal machine restarts and user sessions.
- Wake-from-sleep should be treated as best-effort, not absolute.

---

## 9. Success metrics

- Success metric 1:
  A Windows 11 user can configure the product and obtain reliable scheduled captures without repeated manual troubleshooting.

- Success metric 2:
  The product remains lightweight enough to be acceptable as an always-available background utility.

- Success metric 3:
  Outputs are stored locally in an organized manner with metadata and logs that truthfully reflect what happened.

- Optional additional metrics:
  - setup remains simple,
  - manual capture works consistently,
  - failure states are understandable,
  - future productization remains plausible.

---

## 10. Major risks

- Risk:
  Scope inflation.

- Why it matters:
  A small useful MVP could get delayed by premature cross-platform or analytics ambitions.

- Possible mitigation:
  Freeze Windows 11-only scope and define strong non-goals.

---

- Risk:
  Misleading assumptions about screen capture behavior.

- Why it matters:
  A failed or black capture may not mean “computer off,” which could corrupt user trust.

- Possible mitigation:
  Record explicit status outcomes and do not over-infer.

---

- Risk:
  Privacy discomfort.

- Why it matters:
  Screenshots may contain sensitive content and the app could feel invasive if poorly designed.

- Possible mitigation:
  Require visible control, local-only storage, and explicit enable / disable behavior.

---

- Risk:
  Technical over-engineering.

- Why it matters:
  The project could become a platform architecture exercise instead of a useful tool.

- Possible mitigation:
  Keep v1 narrow and outcome-oriented.

---

## 11. Decision authority

- Who approves scope changes?
  Daniel

- Who approves technical direction?
  Technical lead proposes; Daniel approves major direction changes for this customer-led MVP.

- Who approves release?
  Daniel, informed by delivery lead and QA sign-off.

- Who approves spending, if relevant?
  Daniel

---

## 12. Approval block

- Customer / sponsor:
  Daniel

- Signature / approval note:
  Approved as customer-side project charter baseline.

- Date:
  2026-03-19

- Product / delivery lead:
  Pending assignment

- Signature / approval note:
  Pending

- Date:
  Pending

- Technical lead:
  Pending assignment

- Signature / approval note:
  Pending

- Date:
  Pending
