# Contributing to ReleaseFence

ReleaseFence is intentionally narrow: local, explainable boundary checks with deterministic output. Contributions should make a finding more accurate or a report easier to act on without turning the project into legal clearance, secret discovery, or a hosted service.

## Pick a pathway

1. **First contribution — docs, fixtures, and diagnostics.** Correct a confusing message, add a synthetic edge case, or improve an accessibility assertion. These should fit in one reviewable change.
2. **Rule contributor — bounded scanner behavior.** Propose a local fact, severity, false-positive control, stable evidence, remediation, and focused tests before writing code.
3. **Format steward — JSON, HTML, CLI, or packaging.** Preserve deterministic output, schema/exit-code compatibility, accessibility, and zero runtime dependencies.
4. **Reviewer — sustained project care.** Contributors who repeatedly ship accurate, constructive work may be invited to triage or review. Commit access is never automatic.

The current [issue seeds](docs/ISSUE_SEEDS.md) show concrete work at each level. Comment with your proposed approach before starting a multi-day item; assignment is a coordination signal, not ownership of the idea.

## Before opening a change

1. Search issues and read [SCOPE.md](SCOPE.md), [GOVERNANCE.md](GOVERNANCE.md), and [API stability](docs/API_STABILITY.md).
2. For a new rule, describe the local fact it observes, false-positive risks, severity, and remediation.
3. Use only public specifications and synthetic fixtures. Log every source or fixture in [PROVENANCE.md](PROVENANCE.md).
4. Never submit private repositories, partner material, credentials, incident data, or customer-derived examples.

## Development check

Use Python 3.10–3.14 and standard-library runtime code.

```sh
python3 -m unittest discover -s tests -v
python3 releasefence.py scan examples/green --json /tmp/releasefence.json --html /tmp/releasefence.html
```

Keep JSON deterministic, HTML script-free, and findings linked to a stable path/line fact. Non-trivial behavior needs one focused test.

## Triage and review expectations

- A maintainer aims to acknowledge a well-scoped issue or pull request within seven days; this is a best-effort target, not an SLA.
- `good first issue` means the design is understood and likely localized. `help wanted` means the outcome is scoped but design discussion may remain. `advanced` means schema, security, performance, or compatibility tradeoffs need maintainer agreement first.
- Triage may request a smaller synthetic reproduction, close work outside [SCOPE.md](SCOPE.md), or split unrelated changes.
- If there is no response after seven days, one concise follow-up is welcome. Please do not open duplicate issues or ping unrelated contributors.

## Pull requests and recognition

Keep changes small. Explain behavior and compatibility impact, link the issue, list provenance additions, and include exact validation commands. Review feedback focuses on the code, never the contributor.

Merged contributors are credited in the next release notes unless they opt out. Sustained contributors may be invited to review related areas and will be listed in release acknowledgements for that work. No contribution volume guarantees a role.

By contributing, you agree that your work is provided under the MIT License and that you have the right to submit it.
