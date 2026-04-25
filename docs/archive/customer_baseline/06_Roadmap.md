# 06 — Downstream Document Roadmap

[ARCHIVED BASELINE]
This file is part of the original customer baseline pack preserved in [README.md](README.md).
It is historical reference material and not the active product or maintainer contract.

With the first five customer documents filled, the next step should be team-authored delivery documents.

## What the team should produce next for this project

### 1. PRD
The team should turn the filled customer pack into a structured product requirements document covering:
- user stories,
- feature boundaries,
- acceptance criteria,
- out-of-scope confirmation,
- open product questions.

### 2. SRS
The team should convert the product view into a concrete software requirements specification covering:
- configuration,
- scheduling behavior,
- capture behavior,
- storage behavior,
- error and status handling,
- data model,
- interfaces,
- non-functional targets.

### 3. Architecture Design Document
The team should describe:
- process model,
- worker / agent split,
- scheduler interaction,
- capture backend abstraction,
- storage design,
- failure pathways,
- packaging approach.

### 4. ADR set
Expected early ADRs include:
- Windows 11 only for v1,
- Python-first implementation,
- local-only storage in v1,
- transparent tray-based control,
- no Windows service architecture,
- honest status taxonomy,
- composite output required.

### 5. Privacy and Risk Assessment
This project requires a meaningful privacy and misuse review because screenshots may include sensitive content.

### 6. Test Strategy and UAT Plan
The team should define:
- capture success scenarios,
- multi-monitor scenarios,
- sleep / wake scenarios,
- disabled-state scenarios,
- retention scenarios,
- failure transparency scenarios.

### 7. Release Checklist
The team should define what must be true before the first personal release is considered acceptable.

## What the customer should ask the team explicitly

Ask the team to:
- challenge assumptions, especially around capture semantics,
- avoid misleading inferences,
- preserve local-only trust boundaries in v1,
- keep the MVP small and useful,
- clearly separate product requirements from implementation choices.

## What the team should challenge

The team should feel free to challenge:
- whether per-monitor outputs belong in the earliest MVP,
- whether wake-from-sleep is worth early effort,
- whether a tray UI should exist in the very first internal prototype,
- whether Python-first remains the right choice for later productization.
