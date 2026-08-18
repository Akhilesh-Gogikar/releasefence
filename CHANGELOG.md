# Changelog

All notable changes are recorded here. The project follows Semantic Versioning after its first public tag.

## [Unreleased]

Target: 0.1.1. This section is not a release or tag.

### Fixed

- Bound every file read, reject symlink/junction escapes (including `.git`), detect concurrent tree changes, avoid opening special filesystem entries, and make incomplete scans visible.
- Redact URL credentials, sensitive query/fragment values, and absolute symlink targets from report evidence.
- Handle IPv6 and malformed URL candidates without aborting a scan.
- Recognize and redact SCP-style Git user information, including internal hosts.
- Recognize single-label internal hosts and avoid treating arbitrary `config.toml` URLs as package registries.
- Emit stdout and file reports as deterministic UTF-8/LF and report output-write failures without a Python traceback.

### Changed

- Clarify scan scope, synthetic self-scan behavior, accessibility claims, and private ecosystem-link staging.

## [0.1.0] - 2026-08-17

### Added

- Local CLI with deterministic JSON and self-contained HTML reports.
- Explainable release-boundary findings with stable IDs, severities, evidence, and remediation.
- License/manifest, provenance, remote/registry, internal URL, submodule/symlink, binary, large-file, and Git LFS checks.
- Synthetic green, amber, and red examples and standard-library tests.

[0.1.0]: https://github.com/akigogikar/releasefence/releases/tag/v0.1.0
