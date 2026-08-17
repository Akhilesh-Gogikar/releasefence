# Issue seeds

These are ready-to-file proposals, not promises. Confirm the code still matches each seed before creating the issue. Use synthetic fixtures only.

## 1. Recognize PEP 621 license table declarations

**Proposed title:** `Recognize pyproject.toml license tables with deterministic evidence`

**Labels:** `good first issue`, `help wanted`, `rules`

**Rationale:** `_manifest_licenses()` recognizes string assignments but not the older `{text = ...}` or `{file = ...}` forms. A repository can therefore hide a conflict behind an unsupported declaration.

**Acceptance criteria:** parse bounded single-line `license = {text = "..."}` values; flag file-based declarations for manual review rather than reading arbitrary paths; preserve current string behavior and deterministic findings; document the limitation.

**Test plan:** add synthetic pyproject fixtures for string, text-table, file-table, malformed, and conflicting root-license cases; run the full unit suite and compare two identical reports.

**Skills:** beginner Python, regular expressions, TOML familiarity. **Estimated scope:** 2–4 hours. **Likely files:** `releasefence.py`, `tests/test_releasefence.py`, `docs/API_STABILITY.md`, `PROVENANCE.md`.

## 2. Account for unreadable or skipped files

**Proposed title:** `Report skipped and unreadable files in the ReleaseFence summary`

**Labels:** `good first issue`, `help wanted`, `reporting`

**Rationale:** `_read_text()` returns `None` for several causes, but the final report does not distinguish a binary from an unreadable or size-skipped text candidate. Reviewers need to know what was not inspected.

**Acceptance criteria:** add deterministic skipped-file counts/reasons without leaking absolute paths; avoid duplicate findings with existing binary/large-file rules; render the count in JSON and HTML; document schema impact.

**Test plan:** use temporary unreadable, oversized, binary, and invalid-UTF-8 files; skip permission assertions where the platform cannot enforce them; verify stable JSON ordering and accessible HTML text.

**Skills:** Python filesystem APIs, cross-platform testing, report design. **Estimated scope:** 4–8 hours. **Likely files:** `releasefence.py`, `tests/test_releasefence.py`, `docs/ARCHITECTURE.md`, `docs/API_STABILITY.md`.

## 3. Add a visible local exception file

**Proposed title:** `Design a versioned local exception file with visible applied findings`

**Labels:** `help wanted`, `design needed`, `configuration`

**Rationale:** teams need to suppress reviewed facts without making them disappear. A local exception should remain evident and deterministic.

**Acceptance criteria:** agree on a minimal versioned JSON schema; match only stable rule/path/evidence fields; require a nonempty rationale; show applied, stale, and invalid exceptions in JSON/HTML; never fetch configuration; define CLI and schema compatibility.

**Test plan:** cover applied, expired/stale, unknown-rule, malformed, duplicate, and path-normalization cases; prove output stability across checkout locations; add one end-to-end CLI test.

**Skills:** CLI/API design, validation, security boundaries, Python. **Estimated scope:** 1–2 days after design approval. **Likely files:** `releasefence.py`, `tests/test_releasefence.py`, `docs/API_STABILITY.md`, `docs/PRIVACY.md`, `README.md`.

## 4. Export SARIF without weakening evidence

**Proposed title:** `Add deterministic SARIF 2.1.0 export for ReleaseFence findings`

**Labels:** `help wanted`, `advanced`, `reporting`

**Rationale:** a standard static-analysis interchange format would help existing review workflows, but only if ReleaseFence rule IDs, severities, locations, and remediation survive the mapping.

**Acceptance criteria:** write SARIF using only the standard library; map every finding field explicitly; keep repository-relative URIs; produce byte-stable output; add `--sarif`; document what SARIF cannot represent; do not add upload behavior.

**Test plan:** golden semantic assertions for green/red fixtures, JSON schema-shape checks, CLI output/atomic-write tests, and determinism across paths/runs.

**Skills:** SARIF, JSON schemas, CLI compatibility, Python. **Estimated scope:** 2–3 days. **Likely files:** `releasefence.py`, `tests/test_releasefence.py`, `docs/API_STABILITY.md`, `README.md`.

## 5. Compare SPDX expressions conservatively

**Proposed title:** `Normalize simple SPDX AND/OR expressions before declaring license conflicts`

**Labels:** `advanced`, `rules`, `compatibility`

**Rationale:** the current string-based comparison can treat equivalent simple expressions as conflicts or miss meaningful structure. A bounded parser can improve accuracy without becoming a legal engine.

**Acceptance criteria:** define and document a deliberately small grammar; normalize case, whitespace, parentheses, AND/OR, and `WITH`; reject unsupported syntax with a visible warning; keep raw evidence; make no compatibility or legal-conclusion claim.

**Test plan:** table-driven normalization/equivalence cases, malformed-expression cases, root/manifest conflict integration, and complexity tests that prevent unbounded recursion.

**Skills:** parsing, SPDX syntax, defensive testing, API stability. **Estimated scope:** 2–4 days. **Likely files:** `releasefence.py`, `tests/test_releasefence.py`, `docs/ARCHITECTURE.md`, `docs/API_STABILITY.md`, `PROVENANCE.md`.
