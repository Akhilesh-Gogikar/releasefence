# API and output stability

ReleaseFence 0.x is alpha software.

License scanning supports simple string assignments and bounded single-line `pyproject.toml` license tables with exactly one `text` or `file` key. Text is recognized heuristically as a license marker or identifier; PEP 621 does not require it to be SPDX. File references are not followed and produce `license-unverified` manual-review warnings. Multiline, escaped, malformed or multi-key tables produce `manifest-invalid` manual-review warnings. No legal conclusion is implied.

- CLI commands, exit meanings, rule identifiers, and JSON fields may change in a minor 0.x release when accuracy requires it.
- `schema_version` changes when a consumer must adapt. Additive fields may appear without a schema bump during 0.x.
- Finding IDs are stable for the same rule/path/line/evidence tuple; changing evidence intentionally changes the ID.
- JSON ordering and formatting are deterministic but consumers must parse JSON rather than compare whitespace.
- HTML is a human report, not a machine API. Its visual structure may evolve while accessibility and local evidence remain required.

Deprecations will be called out in [CHANGELOG.md](../CHANGELOG.md). A 1.0 release will define a longer compatibility window after real-world rule and schema feedback.
