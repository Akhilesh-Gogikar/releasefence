# API and output stability

ReleaseFence 0.x is alpha software.

- CLI commands, exit meanings, rule identifiers, and JSON fields may change in a minor 0.x release when accuracy requires it.
- `schema_version` changes when a consumer must adapt. Additive fields may appear without a schema bump during 0.x.
- Finding IDs are stable for the same rule/path/line/evidence tuple; changing evidence intentionally changes the ID.
- JSON ordering and formatting are deterministic but consumers must parse JSON rather than compare whitespace.
- HTML is a human report, not a machine API. Its visual structure may evolve while accessibility and local evidence remain required.

Deprecations will be called out in [CHANGELOG.md](../CHANGELOG.md). A 1.0 release will define a longer compatibility window after real-world rule and schema feedback.
