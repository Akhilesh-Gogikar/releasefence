# Troubleshooting

## The command is not found

Run `python3 -m pip install .` from the checkout, activate the same virtual environment, then run `releasefence --help`. Without installation, use `python3 releasefence.py --help`.

## CI exits 1 but a report exists

That is expected when a finding meets the `--fail-on` threshold. `error` is the default. Use `--fail-on none` only for report generation; do not treat it as clearance.

## A report changes between machines

Compare the repository bytes, symlink targets, `.git/config`, and Python versions. Absolute checkout paths and timestamps are intentionally absent. File contents or local Git configuration can legitimately differ.

## A URL or registry is a false positive

The v0 detector is conservative. Confirm the exact path/line evidence, replace examples with reserved public domains where possible, and open an issue with a synthetic reproduction. Do not paste the private URL.

## A binary is flagged

ReleaseFence does not decode binaries. Record its origin and generation method or replace it with reproducible source. Git LFS pointers also require the referenced object to be reviewed independently.
