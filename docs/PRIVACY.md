# Privacy

ReleaseFence is local-only. It does not make network requests, send telemetry, load remote assets, or persist a database.

The scanner reads the selected tree, plus a real in-tree `.git/config`, and writes only the requested JSON/HTML paths. It does not follow a symlinked `.git`. URL user information, recognized sensitive query/fragment values, and absolute symlink targets are redacted, but reports can still contain repository-relative filenames, configuration fragments, endpoints, relative symlink targets, and other evidence. Treat reports as at least as sensitive as the inspected repository.

Recommended practice:

- scan only trees you are authorized to inspect;
- write reports outside the repository or to ignored paths;
- inspect and redact reports before sharing;
- do not attach private findings to public issues; and
- delete temporary artifacts according to your own retention policy.

The generated HTML is self-contained and script-free. Opening it does not request remote assets.
