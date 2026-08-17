# ReleaseFence

[![CI](https://github.com/akigogikar/releasefence/actions/workflows/ci.yml/badge.svg)](https://github.com/akigogikar/releasefence/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/github/license/akigogikar/releasefence)](LICENSE)

ReleaseFence is an explainable, local-only preflight for repository release boundaries. It produces deterministic JSON and self-contained accessible HTML without uploading the inspected tree.

**Status:** 0.1.0 alpha and private prelaunch. Findings support human review; they are not legal advice, ownership proof, secret discovery, or permission to publish.

## One-command usage

```sh
releasefence scan /path/to/repository --json report.json --html report.html
```

The default `--fail-on error` exits 1 when an error or critical finding exists. Accepted thresholds are `none`, `warning`, `error`, and `critical`; invalid input exits 2. `--json -` writes JSON to stdout. Reports omit timestamps and absolute checkout paths so identical trees produce identical output.

## Install from source

ReleaseFence supports Python 3.10–3.14 and has no runtime dependencies. CI tests every supported Python version on Linux and Python 3.14 on macOS and Windows.

```sh
git clone https://github.com/akigogikar/releasefence.git
cd releasefence
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
releasefence --help
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## Reproducible examples

```sh
python3 releasefence.py scan examples/green --json /tmp/releasefence-green.json --html /tmp/releasefence-green.html
python3 releasefence.py scan examples/amber --json /tmp/releasefence-amber.json --html /tmp/releasefence-amber.html
python3 releasefence.py scan examples/red --json /tmp/releasefence-red.json --html /tmp/releasefence-red.html --fail-on none
```

Expected statuses are green, amber, and red respectively.

## Checks in 0.1

- conflicting root license and supported manifest declarations;
- internal/private-looking URLs, Git remotes, and package registries;
- submodule and symlink lineage requiring independent review;
- binary, large, and Git LFS objects/rules; and
- missing or empty provenance records.

Every finding has a stable ID, severity, local path/line fact, evidence, and remediation.

## Documentation and community

- Design: [architecture](docs/ARCHITECTURE.md), [API stability](docs/API_STABILITY.md), [privacy](docs/PRIVACY.md), and [accessibility](docs/ACCESSIBILITY.md)
- Use: [troubleshooting](docs/TROUBLESHOOTING.md) and [launch kit](docs/LAUNCH_KIT.md)
- Direction: [roadmap](ROADMAP.md), [changelog](CHANGELOG.md), and [governance](GOVERNANCE.md)
- Participate: [contributing](CONTRIBUTING.md), [code of conduct](CODE_OF_CONDUCT.md), and [support](SUPPORT.md)
- Safety: [security policy](SECURITY.md), [scope](SCOPE.md), and [provenance](PROVENANCE.md)
- Related optional projects: [ecosystem](ECOSYSTEM.md)

## Test

```sh
python3 -m unittest discover -s tests -v
```

## Honest limitations

License recognition and URL classification are deliberately bounded heuristics. Text inspection is capped at 2 MB per file; binaries and larger files are flagged rather than decoded. ReleaseFence does not determine copyright ownership, contractual restrictions, patent risk, credential leakage, or remote repository visibility. It makes no network requests and does not replace specialist legal or security review.

Released under the [MIT License](LICENSE).
