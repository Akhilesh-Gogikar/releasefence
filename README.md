# ReleaseFence

> **Private incubation repository. Do not publish or announce yet.**

Local OSS release-readiness preflight with an explainable static report.

## Problem

Founders have separate tools for licenses, secrets, dependencies, and security, but no local decision-oriented preflight for moving a private repository toward public release.

## Planned v0

- Run local-only repository boundary checks.
- Detect license/manifest conflicts, private remotes and registries, internal URLs, submodule lineage, binary/LFS blobs, and missing provenance records.
- Render one evidence-linked HTML report and a machine-readable JSON result.

## Non-goals

- Legal clearance or legal advice.
- A replacement for ScanCode, ORT, FOSSology, REUSE, TruffleHog, or OpenSSF Scorecard.
- Uploading source or findings to a hosted service.

## Repository state

This repository contains only the clean-room project brief and planning scaffold. No implementation has started.

- Scope and exclusions: [SCOPE.md](SCOPE.md)
- Source/provenance log: [PROVENANCE.md](PROVENANCE.md)
- Initial execution plan: [docs/PLAN.md](docs/PLAN.md)

## Licensing

No public license is granted while this repository is private. Select an OSS license only after ownership and third-party provenance review.
