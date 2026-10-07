# Provenance log

This repository must remain independently developed from public sources and synthetic fixtures.

## Rules

- Record every specification, dataset, fixture, snippet, dependency, and generated asset before it enters the repository.
- Prefer public primary sources and link the exact version or commit.
- Do not copy from private, partner, customer, or unpublished research repositories.
- Public visibility is not a copyright license; record applicable terms.
- Stop and request ownership review when provenance is uncertain.

## Sources

| Date | Source/version | Purpose | License or terms | Notes |
|---|---|---|---|---|
| 2026-08-16 | Project brief derived from public-landscape research | Initial scope only | Owner's personal planning notes (not included) | No implementation or copied source |
| 2026-08-16 | Python 3 standard-library documentation, https://docs.python.org/3/ | CLI, JSON, HTML escaping, URL parsing, filesystem implementation references | PSF License Version 2 | Implementation is original and uses only the standard library |
| 2026-08-16 | SPDX License List, https://spdx.org/licenses/ | Public license-identifier conventions | SPDX legal terms | No license text copied into implementation |
| 2026-08-16 | SPDX MIT license text, https://spdx.org/licenses/MIT.html | Short MIT marker text in synthetic fixtures and tests | SPDX legal terms | Public canonical license excerpt only |
| 2026-08-16 | Git documentation: gitmodules and git-config, https://git-scm.com/docs/ | Public formats for submodule and remote configuration | GPLv2 documentation terms | Parser is an original bounded heuristic |
| 2026-08-16 | Git LFS specification v1, https://github.com/git-lfs/git-lfs/blob/main/docs/spec.md | Recognize the public pointer marker | Repository license/terms | Synthetic pointer contains no real object |
| 2026-08-16 | Original synthetic green/amber/red trees | Tests and demonstration | Original synthetic data | No private, partner, or customer inputs |
| 2026-08-17 | MIT License, https://opensource.org/license/mit | Repository license text and packaging metadata | MIT | Exact standard text with owner-requested copyright line |
| 2026-08-17 | Original project governance, community, workflow, packaging, and documentation text | DevRel launch-readiness baseline | Original work under repository license | Tailored to ReleaseFence scope; no private or partner material |
| 2026-08-17 | Locally authored deterministic social-preview SVG | Repository preview and README identity | Original work under this repository’s MIT License | No external logos, fonts, screenshots, adoption claims, or partner assets; adjacent PNG is rendered from the SVG |
| 2026-10-04 | Owner launch review | Public-release gate in SCOPE.md | Not applicable | Owner confirmed personal ownership with no employer, company, or partner IP claim; MIT license confirmed; full-history secret, provenance, and boundary audit found no blockers; trademark check was a directional web search only |
| 2026-10-05 | PEP 621 (historical), https://peps.python.org/pep-0621/ | Original text/file license-table shape and mutual exclusivity | Public domain or CC0-1.0, as stated in the PEP | AI-assisted bounded heuristic implementation and synthetic tests; this row does not attest to account-owner review |
| 2026-10-05 | RFC 6761 `localhost` names and IANA IPv4/IPv6 special-purpose address registries, https://www.iana.org/assignments/iana-ipv4-special-registry/ | Define the loopback set for `loopback-url` and its synthetic URL test fixture | IETF Trust Legal Provisions; IANA public registry | Classification uses the standard library's `ipaddress`; fixture hosts are reserved or synthetic |
| 2026-10-05 | CommonMark Spec 0.31.2 code spans, https://spec.commonmark.org/0.31.2/#code-spans | Treat the backtick as a URL delimiter and build the backtick-wrapped URL test fixture | CC BY-SA 4.0 | No spec text copied; fixture uses the synthetic `build.internal` host and RFC 1918 address `10.0.0.5` |
| 2026-10-07 | Public maintainer review, https://github.com/Akhilesh-Gogikar/releasefence/pull/11#pullrequestreview-5417816888; living specification, https://packaging.python.org/en/latest/specifications/pyproject-toml/ | Regression examples and current specification context for legacy license forms | Repository MIT terms for original implementation and synthetic tests; linked specification terms apply to its documentation | AI-assisted review revisions; declared paths are not opened; personal-review and provenance checklist requirements remain for the account owner |
