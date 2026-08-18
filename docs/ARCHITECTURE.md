# Architecture

ReleaseFence is one Python module with no runtime dependencies. The design favors an auditable linear pipeline over plugins or background services.

1. `main()` parses the `scan` command and exit threshold.
2. `scan_repository()` walks a stable local tree without following symlinked files or directories and builds a bounded UTF-8 text cache from regular files only.
3. Independent checks append immutable `Finding` values. Each finding contains a rule, severity, local fact, evidence, and remediation.
4. Findings are sorted by a fixed key. Stable IDs hash rule/path/line/evidence, never the absolute checkout path.
5. `json_text()` and `html_text()` render the same report. Atomic writes avoid partial artifacts.

On systems with descriptor-relative filesystem APIs, traversal opens each file relative to the already-open parent directory and refuses a symlink in the final component. The portable fallback rejects symlinks and Windows reparse points and validates the opened handle against the in-root lexical path before reading. Both paths verify directory and file metadata after collection; concurrent changes become `scan-incomplete` errors rather than an apparently clean report.

The scanner skips `.git` contents except a real in-tree `.git/config`, limits every regular-file read to 2 MB plus one byte, samples large files with an 8 KiB read, and never opens FIFOs, sockets, or device files. Directory traversal and file-read failures become `scan-incomplete` errors; special entries and indirect worktree metadata remain visible warnings. It makes no network requests. JSON schema version and tool version are separate so report consumers can negotiate changes. See [API stability](API_STABILITY.md).

Trust boundaries are the repository path, manifest/text parsers, filesystem metadata, and output paths. A result is evidence for human review, not proof of ownership or legal clearance.
