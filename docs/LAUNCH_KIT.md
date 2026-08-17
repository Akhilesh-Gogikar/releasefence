# Launch kit

Use this only after the repository owner approves public visibility.

## Positioning

**Short:** Explainable local boundary checks before an OSS release.

**Long:** ReleaseFence inspects a local repository for release-boundary risks and produces deterministic JSON plus an accessible, evidence-linked HTML report. It is a preflight for human review, not legal clearance.

## Reproducible demo

```sh
python3 -m pip install .
releasefence scan examples/amber --json /tmp/releasefence.json --html /tmp/releasefence.html
```

Expected result: exit 0 with amber status, one submodule-lineage warning, and no network access.

## Launch checklist

- Ownership, MIT license, trademark, provenance, and security review recorded.
- CI green on every supported Python/platform combination.
- `v0.1.0` tag points at the reviewed commit; changelog and docs match it.
- Generated green/amber/red reports reviewed for accuracy and accessibility.
- Security advisory and issue templates tested while the repository is private.
- README claims checked against the exact demo above.

Do not describe ReleaseFence as legal advice, a secret scanner, or proof that a repository is safe to publish.
