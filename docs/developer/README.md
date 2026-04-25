# SelfSnap Developer Docs

This folder contains the active developer-facing contract and validation docs for the current repo state.
Use these docs when changing product behavior, validating releases, or checking whether the implementation still matches the intended runtime and trust boundary.
They track active preview behavior, not a stable release contract.

These files are not the stable end-user starting point and they are not archived historical material.
For the full docs map, start with [../README.md](../README.md).

## Navigation

- [../../README.md](../../README.md): top-level product overview and quick-start hub
- [../README.md](../README.md): full docs map
- [../user/README.md](../user/README.md): current user-doc hub
- [../archive/README.md](../archive/README.md): historical-doc hub

## Suggested Reading Order

1. [product-requirements-document-v1.md](product-requirements-document-v1.md) for the active product contract.
2. [software-requirements-specification-and-architecture-v1.md](software-requirements-specification-and-architecture-v1.md) for runtime, storage, scheduler, and UI contracts.
3. [validation-checklist.md](validation-checklist.md) for reusable validation and release checks.

## Contents

- [product-requirements-document-v1.md](product-requirements-document-v1.md): current product scope, principles, must-haves, and non-goals.
- [software-requirements-specification-and-architecture-v1.md](software-requirements-specification-and-architecture-v1.md): runtime and architecture contract for current HEAD.
- [validation-checklist.md](validation-checklist.md): active validation surface for release and regression work.

## Keep These In Sync

- Product scope or user-visible commitments: [../../README.md](../../README.md), [product-requirements-document-v1.md](product-requirements-document-v1.md), and [../user/README.md](../user/README.md)
- Runtime, architecture, or trust-boundary behavior: [software-requirements-specification-and-architecture-v1.md](software-requirements-specification-and-architecture-v1.md) and [validation-checklist.md](validation-checklist.md)
- Maintainer entry guidance and doc routing: [../README.md](../README.md) and [../archive/README.md](../archive/README.md)

## Related Docs

- For current user docs, use [../user/README.md](../user/README.md).
- For archived release notes, baseline packs, and superseded planning material, use [../archive/README.md](../archive/README.md).