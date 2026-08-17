# Contributing to ReleaseFence

ReleaseFence is intentionally narrow: local, explainable boundary checks with deterministic output. Contributions should make a finding more accurate or a report easier to act on without turning the project into a legal-clearance or hosted scanning service.

## Before opening a change

1. Search existing issues and read [SCOPE.md](SCOPE.md), [GOVERNANCE.md](GOVERNANCE.md), and [API stability](docs/API_STABILITY.md).
2. For a new rule, describe the local fact it observes, false-positive risks, severity, and remediation.
3. Use only public specifications and synthetic fixtures. Add every new source or fixture to [PROVENANCE.md](PROVENANCE.md).
4. Never submit private repositories, partner material, credentials, incident data, or customer-derived examples.

## Development check

```sh
python3 -m unittest discover -s tests -v
python3 releasefence.py scan examples/green --json /tmp/releasefence.json --html /tmp/releasefence.html
```

Use Python 3.10–3.14 and the standard library for runtime code. Keep JSON deterministic, HTML script-free, and findings linked to a stable local path/line fact. Add one focused test for non-trivial behavior.

## Pull requests

Keep changes small, explain behavior and compatibility impact, list provenance additions, and include the commands you ran. By contributing, you agree that your contribution is provided under the repository's MIT License and that you have the right to submit it.
