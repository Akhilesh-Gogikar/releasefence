# Launch kit

Use this only after the owner approves public visibility and every launch-day gate below passes. Copy describes 0.1.0 as it exists; do not add adoption, performance, or legal-clearance claims.

## Positioning

**One line:** Know what crosses the boundary before your repository does.

**Short:** ReleaseFence is a local, evidence-first preflight for open-source repository review. It produces deterministic JSON and accessible static HTML without uploading the tree.

**Differentiators:** local-only operation, stable path/line evidence instead of an opaque score, one view across several release boundaries, and synthetic green/amber/red examples anyone can reproduce.

## Three-minute demo script

1. Say: “This is a release-review aid, not legal clearance or a secret scanner.”
2. Install and run the amber fixture:

   ```sh
   python3 -m pip install .
   releasefence scan examples/amber --json /tmp/releasefence.json --html /tmp/releasefence.html
   ```

3. Show `status: "amber"` and the single submodule-lineage finding in JSON.
4. Open the HTML locally; follow the finding permalink and read its path, line, evidence, and remediation.
5. Run `examples/green` and `examples/red --fail-on none` to show the stable status boundary.
6. End with the limitation: ownership, contracts, secrets, patents, and remote visibility still need specialist review.

## Launch copy

### Hacker News

**Title:** Show HN: ReleaseFence – local, explainable checks before open-sourcing a repo

**Text:** I built ReleaseFence because release review often means checking several boundaries in separate places. The 0.1 CLI stays local and produces deterministic JSON plus script-free HTML. Every finding includes a path, line, evidence, severity, and remediation. It checks a deliberately bounded set: license declarations, provenance, internal URLs/registries/remotes, submodules/symlinks, binaries, large files, and LFS. It is not legal clearance or a secret scanner. The repo includes green/amber/red synthetic examples; I would value feedback on false positives and missing evidence.

### Reddit

**Title:** I made a local, evidence-first preflight for reviewing a repo before open-sourcing it

**Body:** ReleaseFence 0.1 runs entirely on a local checkout and creates deterministic JSON and accessible static HTML. It does not upload source or claim a repository is safe to publish. I included three synthetic examples so the behavior is reproducible. I am looking for concrete false-positive cases, report usability feedback, and small contributions to the scoped issue seeds.

### LinkedIn

Before a repository becomes open source, the hard question is often not “did one scanner pass?” but “what exactly crosses the boundary, and can another reviewer reproduce it?” ReleaseFence 0.1 is a local CLI that turns a bounded set of license, provenance, endpoint, lineage, and binary checks into deterministic, evidence-linked reports. No upload, no readiness score, and no legal-clearance claim. The launch includes synthetic demos and a contributor path for rule, fixture, and accessibility improvements.

### X

ReleaseFence 0.1 is a local, evidence-first preflight before open-sourcing a repo: deterministic JSON + script-free HTML, with path/line evidence for every finding. No uploads, opaque score, or legal-clearance claim. Includes reproducible green/amber/red demos.

## FAQ

**Does green mean a repository is safe to publish?** No. It means the implemented heuristics produced no warning-or-higher finding for that tree.

**Does it upload or phone home?** No. The scanner makes no network requests; reports are local files that may still contain sensitive evidence.

**Is it a legal or secret-scanning tool?** No. Those are explicit non-goals.

**Why deterministic output?** It makes review diffs and CI behavior easier to reproduce. Absolute checkout paths and generation timestamps are excluded.

**How should I contribute?** Start with a synthetic reproduction and one of the [issue seeds](ISSUE_SEEDS.md). New rules must define evidence, severity, false-positive controls, and remediation.

## Launch-day checklist

- [ ] Public visibility explicitly approved after ownership, license, trademark, provenance, privacy, and security review.
- [ ] CI green on the documented Python/platform matrix; pinned actions and least-privilege permissions rechecked.
- [ ] Tag, version, changelog, install metadata, and demo output agree on 0.1.0.
- [ ] Green/amber/red JSON and HTML reviewed for accuracy, keyboard use, contrast, and screen-reader structure.
- [ ] Security advisory, issue forms, contributor links, and five issue seeds work from a signed-out view.
- [ ] Run launch copy against README claims; remove any claim not directly demonstrated.
- [ ] Reserve time to answer technical questions and correct documentation without arguing with valid criticism.

## First 30 days

- **Days 1–2:** reproduce every reported bug, label it, acknowledge well-scoped reports, and publish corrections quickly.
- **Days 3–7:** summarize recurring false positives and documentation gaps; prioritize small evidence-quality fixes over new checks.
- **Week 2:** invite contributors into good-first issues, recognize merged work, and close seeds that no longer match the code.
- **Week 3:** review report accessibility and CI friction using actual public feedback; update the 0.2 scope rather than expanding silently.
- **Week 4:** publish a transparent 30-day note covering fixes, open risks, contributor credits, and what was not learned. Do not equate traffic with successful technical validation.

## Social preview and media

- Upload [the 1280 × 640 PNG](assets/social-preview.png) in **Settings → General → Social preview** immediately before the visibility change; GitHub does not read this repository file automatically.
- Keep the adjacent SVG as the editable source and follow the [asset notes](assets/README.md).
- Capture demos with synthetic inputs only. Remove usernames, home paths, tokens, partner names, and unrelated windows.
- Provide captions, a transcript, and descriptive alt text. Verify the README image, generated HTML, and demo at 200% zoom, by keyboard, and with a real screen reader before posting.
- Do not place download, adoption, company, performance, or compatibility counts on an asset unless the source and date are public and reproducible.

## Ethical cross-promotion

Cross-link only the seven related OSS tools named in ECOSYSTEM.md, and only where a link answers the reader's next technical question. Links stay optional, disclosed, and outside runtime output. Commercial products require exact owner-approved names, URLs, relationship wording, and trademark or partner permission before inclusion.
