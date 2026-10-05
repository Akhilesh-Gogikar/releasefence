# Changelog

All notable changes are recorded here. The project follows Semantic Versioning after its first public tag.

## [Unreleased]

### Changed

- Report loopback URLs (`localhost`, `127.0.0.0/8`, `::1`) as `info`-level `loopback-url` findings instead of critical `internal-url` findings, so intentionally local-only servers no longer turn a report red. Private-network addresses and internal hostnames remain critical `internal-url` findings, and loopback Git remotes and submodule URLs are still flagged.
- List DirectiveGraph in ECOSYSTEM.md now that it is public, guarded by an allowlist test that names no unreleased project.

## [0.1.1] - 2026-10-04

### Fixed

- Bound every file read, reject symlink/junction escapes (including `.git`), detect concurrent tree changes, avoid opening special filesystem entries, and make incomplete scans visible.
- Redact URL credentials, sensitive query/fragment values, and absolute symlink targets from report evidence.
- Handle IPv6 and malformed URL candidates without aborting a scan.
- Recognize and redact SCP-style Git user information, including internal hosts.
- Recognize single-label internal hosts and avoid treating arbitrary `config.toml` URLs as package registries.
- Emit stdout and file reports as deterministic UTF-8/LF and report output-write failures without a Python traceback.
- Redact rooted symlink targets such as `/x` and `\x` on Windows with Python 3.13+, where `os.path.isabs` no longer treats them as absolute.

### Changed

- Clarify scan scope, synthetic self-scan behavior, accessibility claims, and private ecosystem-link staging.
- Move the repository to `Akhilesh-Gogikar`, keep maintainer launch planning out of the repository, and list related tools only after they are public.

## [0.1.0] - 2026-08-17

### Added

- Local CLI with deterministic JSON and self-contained HTML reports.
- Explainable release-boundary findings with stable IDs, severities, evidence, and remediation.
- License/manifest, provenance, remote/registry, internal URL, submodule/symlink, binary, large-file, and Git LFS checks.
- Synthetic green, amber, and red examples and standard-library tests.

[Unreleased]: https://github.com/Akhilesh-Gogikar/releasefence/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/Akhilesh-Gogikar/releasefence/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Akhilesh-Gogikar/releasefence/releases/tag/v0.1.0
