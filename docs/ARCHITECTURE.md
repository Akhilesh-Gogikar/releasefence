# Architecture

ReleaseFence is one Python module with no runtime dependencies. The design favors an auditable linear pipeline over plugins or background services.

1. `main()` parses the `scan` command and exit threshold.
2. `scan_repository()` walks a local tree without following symlinked files and builds a bounded UTF-8 text cache.
3. Independent checks append immutable `Finding` values. Each finding contains a rule, severity, local fact, evidence, and remediation.
4. Findings are sorted by a fixed key. Stable IDs hash rule/path/line/evidence, never the absolute checkout path.
5. `json_text()` and `html_text()` render the same report. Atomic writes avoid partial artifacts.

The scanner skips `.git` contents except `.git/config`, limits text inspection to 2 MB per file, and makes no network requests. JSON schema version and tool version are separate so report consumers can negotiate changes. See [API stability](API_STABILITY.md).

Trust boundaries are the repository path, manifest/text parsers, filesystem metadata, and output paths. A result is evidence for human review, not proof of ownership or legal clearance.
