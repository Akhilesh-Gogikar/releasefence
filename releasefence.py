#!/usr/bin/env python3
"""ReleaseFence: deterministic, local-only OSS release boundary checks."""

from __future__ import annotations

import argparse
import hashlib
import html
import ipaddress
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

VERSION = "0.1.0"
SEVERITY = {"info": 0, "warning": 1, "error": 2, "critical": 3}
PUBLIC_REGISTRIES = {"registry.npmjs.org", "pypi.org", "files.pythonhosted.org", "crates.io"}
PUBLIC_GIT_HOSTS = {"github.com", "gitlab.com", "bitbucket.org", "codeberg.org"}
URL_RE = re.compile(r"(?:https?|ssh|git)://[^\s<>\"')\]]+|git@[A-Za-z0-9._-]+:[^\s<>\"')\]]+")


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    title: str
    path: str
    line: int
    evidence: str
    remediation: str

    @property
    def finding_id(self) -> str:
        raw = "\0".join((self.rule, self.path, str(self.line), self.evidence))
        return self.rule + "-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.finding_id,
            "rule": self.rule,
            "severity": self.severity,
            "title": self.title,
            "fact": {"path": self.path, "line": self.line, "evidence": self.evidence},
            "remediation": self.remediation,
        }


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _iter_files(root: Path) -> Iterable[Path]:
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        dirs[:] = sorted(d for d in dirs if d != ".git")
        for name in sorted(files):
            yield current_path / name
    git_config = root / ".git" / "config"
    if git_config.is_file():
        yield git_config


def _read_text(path: Path, limit: int = 2_000_000) -> str | None:
    try:
        if path.stat().st_size > limit:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _host(raw_url: str) -> str:
    if raw_url.startswith("git@"):
        return raw_url[4:].split(":", 1)[0].lower()
    return (urlparse(raw_url).hostname or "").lower()


def _is_internal_host(host: str) -> bool:
    if not host:
        return False
    if host == "localhost" or host.endswith((".internal", ".local", ".corp", ".lan")):
        return True
    if "intranet" in host:
        return True
    try:
        address = ipaddress.ip_address(host.strip("[]"))
        return address.is_private or address.is_loopback or address.is_link_local
    except ValueError:
        return False


def _line_for(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _license_id(text: str) -> str:
    spdx = re.search(r"SPDX-License-Identifier:\s*([A-Za-z0-9.+-]+)", text, re.I)
    if spdx:
        return spdx.group(1).upper()
    lowered = text.lower()
    if "permission is hereby granted, free of charge" in lowered:
        return "MIT"
    if "apache license" in lowered and "version 2.0" in lowered:
        return "APACHE-2.0"
    if "gnu general public license" in lowered and "version 3" in lowered:
        return "GPL-3.0"
    if "redistribution and use in source and binary forms" in lowered:
        return "BSD"
    return "UNKNOWN"


def _manifest_licenses(root: Path, findings: list[Finding]) -> list[tuple[str, str, int]]:
    result: list[tuple[str, str, int]] = []
    package = root / "package.json"
    if package.is_file():
        try:
            data = json.loads(package.read_text(encoding="utf-8"))
            value = data.get("license")
            if isinstance(value, str) and value.strip():
                result.append(("package.json", value.strip().upper(), 1))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            findings.append(Finding("manifest-invalid", "warning", "Manifest could not be parsed", "package.json", 1, type(exc).__name__, "Repair the manifest before release review."))
    for filename in ("pyproject.toml", "Cargo.toml"):
        path = root / filename
        text = _read_text(path) if path.is_file() else None
        if text is None:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            match = re.match(r"\s*license\s*=\s*[\"']([^\"']+)[\"']", line, re.I)
            if match:
                result.append((filename, match.group(1).strip().upper(), number))
                break
    return result


def _check_licenses(root: Path, findings: list[Finding]) -> None:
    declared: list[tuple[str, str, int]] = []
    for path in sorted(root.iterdir(), key=lambda p: p.name):
        if path.is_file() and path.name.upper().startswith(("LICENSE", "COPYING")):
            text = _read_text(path)
            if text is not None:
                declared.append((_rel(root, path), _license_id(text), 1))
    declared.extend(_manifest_licenses(root, findings))
    known = {identifier for _, identifier, _ in declared if identifier != "UNKNOWN"}
    if not declared:
        findings.append(Finding("license-missing", "warning", "No license declaration found", ".", 1, "No LICENSE/COPYING file or supported manifest license", "Record the intended license after ownership review."))
    if any(identifier in {"UNLICENSED", "PROPRIETARY"} for _, identifier, _ in declared):
        path, identifier, line = next(item for item in declared if item[1] in {"UNLICENSED", "PROPRIETARY"})
        findings.append(Finding("license-private", "error", "Manifest declares a non-public license", path, line, identifier, "Resolve the release license and align all manifests."))
    if len(known) > 1:
        evidence = ", ".join(f"{path}={identifier}" for path, identifier, _ in sorted(declared))
        findings.append(Finding("license-conflict", "error", "License declarations conflict", ".", 1, evidence, "Have the owner resolve the declarations; this tool does not provide legal advice."))


def _check_provenance(root: Path, findings: list[Finding]) -> None:
    path = root / "PROVENANCE.md"
    text = _read_text(path) if path.is_file() else None
    if text is None:
        findings.append(Finding("provenance-missing", "error", "Provenance record is missing", "PROVENANCE.md", 1, "File not found", "Create a provenance record for specifications, fixtures, code, and generated assets."))
        return
    rows = [line for line in text.splitlines() if line.startswith("|") and "---" not in line]
    if len(rows) < 2:
        findings.append(Finding("provenance-empty", "warning", "Provenance record has no source rows", "PROVENANCE.md", 1, "No Markdown table data rows found", "Record each source, version, purpose, and applicable terms."))


def _check_urls(root: Path, texts: dict[Path, str], findings: list[Finding]) -> None:
    registry_names = {".npmrc", ".pypirc", "pip.conf", "pip.ini", "config.toml"}
    for path, text in sorted(texts.items(), key=lambda item: _rel(root, item[0])):
        rel = _rel(root, path)
        for match in URL_RE.finditer(text):
            raw = match.group(0).rstrip(".,;")
            host = _host(raw)
            line = _line_for(text, match.start())
            if _is_internal_host(host):
                findings.append(Finding("internal-url", "critical", "Internal URL crosses the release boundary", rel, line, raw, "Remove, redact, or replace the internal endpoint with a public synthetic example."))
            if path.name in registry_names and host and host not in PUBLIC_REGISTRIES:
                findings.append(Finding("private-registry", "error", "Non-public package registry configured", rel, line, raw, "Replace the registry or document a public installation path."))
            if rel == ".git/config" and (raw.startswith(("git@", "ssh://")) or _is_internal_host(host)):
                findings.append(Finding("private-remote", "warning" if host in PUBLIC_GIT_HOSTS else "error", "Remote may require private credentials", rel, line, raw, "Remove local/private remote lineage from the release copy and verify the public origin."))


def _check_submodules(root: Path, findings: list[Finding]) -> None:
    path = root / ".gitmodules"
    text = _read_text(path) if path.is_file() else None
    if text is None:
        return
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r"\s*url\s*=\s*(.+?)\s*$", line)
        if not match:
            continue
        url = match.group(1)
        host = _host(url)
        severity = "critical" if _is_internal_host(host) else "warning"
        findings.append(Finding("submodule-lineage", severity, "Submodule requires independent lineage review", ".gitmodules", number, url, "Verify source, commit, license, public availability, and provenance before release."))


def _check_binary(root: Path, files: list[Path], texts: dict[Path, str], findings: list[Finding]) -> None:
    for path in files:
        rel = _rel(root, path)
        try:
            size = path.stat().st_size
            sample = path.read_bytes()[:8192]
        except OSError:
            continue
        if sample.startswith(b"version https://git-lfs.github.com/spec/v1"):
            findings.append(Finding("lfs-pointer", "warning", "Git LFS object requires provenance review", rel, 1, "Git LFS pointer", "Verify the referenced object is available, redistributable, and recorded in provenance."))
        elif b"\0" in sample or (sample and path not in texts and size <= 2_000_000):
            findings.append(Finding("binary-file", "warning", "Binary file cannot be source-reviewed locally", rel, 1, f"{size} bytes", "Remove it or record its origin, generation method, terms, and reproducible source."))
        if size > 2_000_000:
            findings.append(Finding("large-file", "warning", "Large file skipped by text checks", rel, 1, f"{size} bytes", "Review the file manually and record its provenance."))
    attributes = texts.get(root / ".gitattributes")
    if attributes:
        for number, line in enumerate(attributes.splitlines(), 1):
            if "filter=lfs" in line:
                findings.append(Finding("lfs-rule", "warning", "Git LFS tracking rule present", ".gitattributes", number, line.strip(), "Verify every matched object is present, public, and redistributable."))


def scan_repository(root: Path) -> dict[str, object]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    candidates = list(_iter_files(root))
    files = [path for path in candidates if not path.is_symlink()]
    texts = {path: text for path in files if (text := _read_text(path)) is not None}
    findings: list[Finding] = []
    for path in sorted((path for path in candidates if path.is_symlink()), key=lambda item: _rel(root, item)):
        try:
            target = os.readlink(path)
        except OSError:
            target = "unreadable target"
        findings.append(Finding("symlink-lineage", "warning", "Symbolic link requires boundary review", _rel(root, path), 1, target, "Verify the target stays within the release tree and record its provenance."))
    _check_licenses(root, findings)
    _check_provenance(root, findings)
    _check_urls(root, texts, findings)
    _check_submodules(root, findings)
    _check_binary(root, files, texts, findings)
    findings.sort(key=lambda f: (-SEVERITY[f.severity], f.rule, f.path, f.line, f.evidence))
    counts = {level: sum(f.severity == level for f in findings) for level in ("critical", "error", "warning", "info")}
    status = "red" if counts["critical"] or counts["error"] else "amber" if counts["warning"] else "green"
    return {
        "schema_version": 1,
        "tool": "releasefence",
        "tool_version": VERSION,
        "repository": ".",
        "status": status,
        "summary": {"total": len(findings), **counts},
        "findings": [finding.as_dict() for finding in findings],
    }


def json_text(report: dict[str, object]) -> str:
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def html_text(report: dict[str, object]) -> str:
    rows = []
    for finding in report["findings"]:
        fact = finding["fact"]
        fid = html.escape(str(finding["id"]))
        rows.append(
            f'<article class="finding {html.escape(str(finding["severity"]))}" id="{fid}" aria-labelledby="{fid}-title">'
            f'<h3 id="{fid}-title"><a href="#{fid}">{fid}</a> · {html.escape(str(finding["title"]))}</h3>'
            f'<p><strong>{html.escape(str(finding["severity"]).upper())}</strong> · '
            f'<code>{html.escape(str(fact["path"]))}:{fact["line"]}</code></p>'
            f'<pre><code>{html.escape(str(fact["evidence"]))}</code></pre>'
            f'<p>{html.escape(str(finding["remediation"]))}</p></article>'
        )
    summary = report["summary"]
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ReleaseFence report</title><style>
body{font:16px/1.5 system-ui,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;color:#17202a;background:#fff}code,pre{background:#f1f3f4;padding:.2rem .35rem;overflow:auto}.finding{border-left:.45rem solid #59636e;padding:.5rem 1rem;margin:1rem 0;background:#fafafa}.critical{border-color:#7b241c}.error{border-color:#a93226}.warning{border-color:#8a6d00}.info{border-color:#1f618d}a{color:#174f78}.skip-link{position:absolute;left:-10000px;top:auto}.skip-link:focus{left:1rem;top:1rem;background:#fff;padding:.5rem;z-index:1}a:focus-visible{outline:3px solid #6c3483;outline-offset:3px}@media(forced-colors:active){.finding{border-left-color:CanvasText}}
</style></head><body><a class="skip-link" href="#content">Skip to report content</a><header><h1>ReleaseFence report</h1></header><main id="content">
<p role="status" aria-label="Overall release status"><strong>Status: """ + html.escape(str(report["status"]).upper()) + f"""</strong></p>
<p>{summary['critical']} critical · {summary['error']} error · {summary['warning']} warning · {summary['info']} info</p>
<p>This is an explainable local preflight, not legal advice or legal clearance.</p>
<section aria-labelledby="findings-heading"><h2 id="findings-heading">Findings</h2>""" + ("".join(rows) if rows else "<p>No boundary findings.</p>") + """</section></main></body></html>
"""


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="releasefence", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan", help="scan a local repository")
    scan.add_argument("repository", type=Path)
    scan.add_argument("--json", dest="json_path", help="JSON output path, or - for stdout", default="-")
    scan.add_argument("--html", dest="html_path", help="static HTML output path")
    scan.add_argument("--fail-on", choices=("none", "warning", "error", "critical"), default="error")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = scan_repository(args.repository)
    except (OSError, ValueError) as exc:
        print(f"releasefence: {exc}", file=os.sys.stderr)
        return 2
    output = json_text(report)
    if args.json_path == "-":
        print(output, end="")
    else:
        _write_atomic(Path(args.json_path), output)
    if args.html_path:
        _write_atomic(Path(args.html_path), html_text(report))
    if args.fail_on == "none":
        return 0
    threshold = SEVERITY[args.fail_on]
    return 1 if any(SEVERITY[f["severity"]] >= threshold for f in report["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
