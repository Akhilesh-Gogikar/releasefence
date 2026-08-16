# Scope

## Purpose

Founders have separate tools for licenses, secrets, dependencies, and security, but no local decision-oriented preflight for moving a private repository toward public release.

## v0 boundary

- Run local-only repository boundary checks.
- Detect license/manifest conflicts, private remotes and registries, internal URLs, submodule lineage, binary/LFS blobs, and missing provenance records.
- Render one evidence-linked HTML report and a machine-readable JSON result.

## Explicit non-goals

- Legal clearance or legal advice.
- A replacement for ScanCode, ORT, FOSSology, REUSE, TruffleHog, or OpenSSF Scorecard.
- Uploading source or findings to a hosted service.

## Clean-room exclusions

- No source, fixtures, prompts, traces, schemas, requirements, or examples from private company, partner, customer, or unpublished research repositories.
- No customer or partner names, data, incidents, screenshots, or derived requirements.
- No public release until ownership, license, trademark, security, and contractual reviews are recorded.

## First proof gate

Three synthetic repositories produce stable green, amber, and red reports, and every finding links to a deterministic local fact.
