# Roadmap

This roadmap communicates scope and sequencing, not delivery dates. Accuracy, privacy, deterministic evidence, and maintenance cost outrank feature count.

## Shipped in 0.1

- Deterministic JSON and accessible static HTML.
- Explainable license, provenance, remote, registry, URL, submodule, symlink, binary, large-file, and LFS boundary checks.
- Synthetic green, amber, and red examples plus installable CLI packaging.

## Next: evidence quality for 0.2

- Recognize more supported manifest license forms without pretending to perform legal analysis.
- Make skipped/unreadable file accounting explicit.
- Add a local, versioned exception format whose applied exceptions remain visible in reports.
- Improve SPDX-expression comparison and document its ceiling.

These map directly to [issue seeds 1–3 and 5](docs/ISSUE_SEEDS.md). Small fixture, diagnostic, accessibility, and documentation improvements are welcome now.

## Explore after the evidence model holds

- SARIF export that preserves stable IDs, local facts, and remediation.
- Clear repository-size budgets and skipped-file summaries.
- A migration path for any schema/rule-ID changes informed by public feedback.

See [issue seed 4](docs/ISSUE_SEEDS.md) for the export design boundary. Exploration does not promise inclusion.

## Before 1.0

- Stabilize the JSON schema, rule identifiers, and deprecation policy.
- Complete independent security, accessibility, ownership, and trademark review.
- Publish migrations for every intentional breaking change.

Hosted scanning, credential discovery, automated legal decisions, and repository publication remain out of scope.
