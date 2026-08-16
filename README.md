# ReleaseFence

> **Private incubation repository. Do not publish or announce yet.**

ReleaseFence is a local OSS release-readiness preflight. It produces stable JSON and a self-contained, evidence-linked HTML report without uploading repository contents.

## Quickstart

Requires Python 3.10+ and no third-party packages.

```sh
cd /path/to/releasefence
python3 releasefence.py scan examples/green --json /tmp/releasefence-green.json --html /tmp/releasefence-green.html
python3 releasefence.py scan examples/amber --json /tmp/releasefence-amber.json --html /tmp/releasefence-amber.html
python3 releasefence.py scan examples/red --json /tmp/releasefence-red.json --html /tmp/releasefence-red.html --fail-on none
```

Scan another local checkout:

```sh
python3 releasefence.py scan /path/to/repository --json report.json --html report.html
```

The default `--fail-on error` exits 1 when an error or critical finding exists. Accepted thresholds are `none`, `warning`, `error`, and `critical`; invalid input exits 2. Use `--json -` (the default) for stdout. The JSON intentionally omits timestamps and absolute paths so identical trees produce identical reports.

## Checks in v0

- conflicting root license and `package.json`, `pyproject.toml`, or `Cargo.toml` declarations;
- internal/private-looking URLs, Git remotes, and package registries;
- submodule lineage requiring independent review;
- binary, large, and Git LFS objects/rules;
- missing or empty `PROVENANCE.md` records.

Every finding has a stable ID, severity, local path/line fact, captured evidence, and remediation. Status is `green` (no warning-or-higher findings), `amber` (warnings only), or `red` (error/critical).

## Test

```sh
python3 -m unittest discover -s tests -v
```

## Limitations and safety

- This is a bounded heuristic preflight, not legal advice or legal clearance.
- It does not determine copyright ownership, contractual restrictions, patent risk, secret leakage, or whether a remote GitHub repository is private.
- License recognition is deliberately small; unknown or complex SPDX expressions require specialist tooling and human review.
- Text inspection is capped at 2 MB per file; binaries and larger files are flagged rather than decoded.
- URL checks can produce false positives and do not make network requests.
- It is not a replacement for ScanCode, ORT, FOSSology, REUSE, TruffleHog, or OpenSSF Scorecard.

See [SCOPE.md](SCOPE.md) and [PROVENANCE.md](PROVENANCE.md). No public license is granted while this repository is private.
