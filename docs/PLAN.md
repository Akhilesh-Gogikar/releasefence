# Initial plan

## Phase 0 — falsify before building

1. Confirm the first proof gate in SCOPE.md with synthetic or public inputs.
2. Identify the three closest existing OSS projects and document the exact delta.
3. Freeze one machine-checkable invariant for v0.
4. Record public sources and terms in PROVENANCE.md.
5. Stop if the proposed wedge is already covered or crosses an IP exclusion.

## Phase 1 — smallest credible artifact

1. Run local-only repository boundary checks.
2. Detect license/manifest conflicts, private remotes and registries, internal URLs, submodule lineage, binary/LFS blobs, and missing provenance records.
3. Render one evidence-linked HTML report and a machine-readable JSON result.

## Launch prerequisites

- Deterministic fixtures and one-command local demo.
- Explainable failure output and documented limitations.
- Secret, private-domain, provenance, dependency-license, and git-history review.
- Ownership and OSS-license approval.
- No public launch until the repository owner explicitly approves visibility.
