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
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

VERSION = "0.1.1"
SEVERITY = {"info": 0, "warning": 1, "error": 2, "critical": 3}
PUBLIC_REGISTRIES = {"registry.npmjs.org", "pypi.org", "files.pythonhosted.org", "crates.io"}
PUBLIC_GIT_HOSTS = {"github.com", "gitlab.com", "bitbucket.org", "codeberg.org"}
URL_RE = re.compile(r"(?:https?|ssh|git)://[^\s<>\"')]+|[A-Za-z0-9._~+-]+@[A-Za-z0-9._-]+:[^\s<>\"')\]]+", re.I)
SENSITIVE_QUERY_RE = re.compile(
    r"(?i)([?&#](?:[^=&#]*(?:token|secret|password|passwd|credential|signature|session)[^=&#]*|api[_-]?key|apikey|key|sig|auth)=)[^&#]*"
)
TEXT_LIMIT = 2_000_000
SAMPLE_LIMIT = 8192


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


def _resolve_path(path: Path, *, strict: bool = False) -> Path:
    try:
        return path.resolve(strict=strict)
    except RuntimeError as exc:
        raise OSError("symlink loop while resolving path") from exc


def _is_git_name(name: str) -> bool:
    return name.casefold() == ".git"


def _inside_git(root: Path, path: Path) -> bool:
    relative = path.relative_to(root)
    return bool(relative.parts and _is_git_name(relative.parts[0]))


def _fingerprint(metadata: os.stat_result) -> tuple[int, int, int, int, int]:
    return (stat.S_IFMT(metadata.st_mode), metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns)


def _inspect_regular_file(
    path: str | Path,
    *,
    dir_fd: int | None = None,
    verify_root: Path | None = None,
) -> tuple[int, bytes, str | None, tuple[int, int, int, int, int]]:
    flags = os.O_RDONLY
    flags |= getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags) if dir_fd is None else os.open(path, flags, dir_fd=dir_fd)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise OSError("not a regular file")
        if verify_root is not None:
            logical_path = Path(path)
            current = logical_path.lstat()
            resolved = _resolve_path(logical_path, strict=True)
            same_identity = (current.st_dev, current.st_ino) == (metadata.st_dev, metadata.st_ino)
            if not same_identity or not resolved.is_relative_to(verify_root) or resolved != logical_path:
                raise OSError("repository boundary changed")
        read_limit = TEXT_LIMIT + 1 if metadata.st_size <= TEXT_LIMIT else SAMPLE_LIMIT
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            raw = handle.read(read_limit)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    size = max(metadata.st_size, len(raw))
    text = None
    if size <= TEXT_LIMIT and len(raw) <= TEXT_LIMIT:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            pass
    return size, raw[:SAMPLE_LIMIT], text, _fingerprint(metadata)


def _file_kind(mode: int) -> str:
    if stat.S_ISFIFO(mode):
        return "FIFO"
    if stat.S_ISSOCK(mode):
        return "socket"
    if stat.S_ISBLK(mode):
        return "block device"
    if stat.S_ISCHR(mode):
        return "character device"
    return "non-regular filesystem entry"


def _symlink_evidence(target: str) -> str:
    # Not os.path.isabs: on Windows, Python 3.13+ no longer treats "/x" or "\x" as absolute.
    if target.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[\\/]", target):
        return "[absolute target redacted]"
    return target.replace("\\", "/")


def _record_symlink(path: Path, target: str, root: Path, findings: list[Finding]) -> None:
    findings.append(
        Finding(
            "symlink-lineage",
            "warning",
            "Symbolic link requires boundary review",
            _rel(root, path),
            1,
            _symlink_evidence(target),
            "Verify the target stays within the release tree and record its provenance.",
        )
    )


def _record_scan_error(path: Path, root: Path, title: str, evidence: str, findings: list[Finding]) -> None:
    findings.append(Finding("scan-incomplete", "error", title, _rel(root, path), 1, evidence, "Restore access, stabilize the tree, and rerun the scan."))


def _cache_regular_file(
    logical_path: Path,
    source: str | Path,
    root: Path,
    findings: list[Finding],
    files: list[Path],
    texts: dict[Path, str],
    sizes: dict[Path, int],
    samples: dict[Path, bytes],
    fingerprints: dict[Path, tuple[int, int, int, int, int]],
    *,
    dir_fd: int | None = None,
    verify_root: Path | None = None,
) -> None:
    try:
        size, sample, text, fingerprint = _inspect_regular_file(source, dir_fd=dir_fd, verify_root=verify_root)
    except OSError as exc:
        _record_scan_error(logical_path, root, "File could not be inspected", type(exc).__name__, findings)
        return
    files.append(logical_path)
    sizes[logical_path] = size
    samples[logical_path] = sample
    fingerprints[logical_path] = fingerprint
    if text is not None:
        texts[logical_path] = text


def _record_walk_error(root: Path, findings: list[Finding], exc: OSError) -> None:
    path = Path(exc.filename) if exc.filename else root
    try:
        relative = _rel(root, path)
    except ValueError:
        relative = "."
    findings.append(Finding("scan-incomplete", "error", "Directory could not be inspected", relative, 1, type(exc).__name__, "Restore read access and rerun the scan before relying on this report."))


def _collect_with_fwalk(
    root: Path,
    findings: list[Finding],
    files: list[Path],
    texts: dict[Path, str],
    sizes: dict[Path, int],
    samples: dict[Path, bytes],
    file_fingerprints: dict[Path, tuple[int, int, int, int, int]],
    directory_fingerprints: dict[Path, tuple[int, int, int, int, int]],
) -> None:
    def onerror(exc: OSError) -> None:
        _record_walk_error(root, findings, exc)

    for current, dirs, names, directory_fd in os.fwalk(root, topdown=True, onerror=onerror, follow_symlinks=False):
        current_path = Path(current)
        directory_fingerprints[current_path] = _fingerprint(os.fstat(directory_fd))
        inside_git = current_path != root and _inside_git(root, current_path)
        if inside_git:
            dirs[:] = []
            names = [name for name in names if name.casefold() == "config"]
        kept_dirs = []
        for name in sorted(dirs):
            path = current_path / name
            try:
                metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError as exc:
                _record_scan_error(path, root, "Filesystem entry could not be inspected", type(exc).__name__, findings)
                continue
            if stat.S_ISLNK(metadata.st_mode):
                try:
                    target = os.readlink(name, dir_fd=directory_fd)
                except OSError:
                    target = "unreadable target"
                _record_symlink(path, target, root, findings)
            elif not stat.S_ISDIR(metadata.st_mode):
                _record_scan_error(path, root, "Directory entry changed during scan", _file_kind(metadata.st_mode), findings)
            elif not _is_git_name(name) or current_path == root:
                kept_dirs.append(name)
        dirs[:] = kept_dirs
        for name in sorted(names):
            path = current_path / name
            try:
                metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError as exc:
                _record_scan_error(path, root, "Filesystem entry could not be inspected", type(exc).__name__, findings)
                continue
            if stat.S_ISLNK(metadata.st_mode):
                try:
                    target = os.readlink(name, dir_fd=directory_fd)
                except OSError:
                    target = "unreadable target"
                _record_symlink(path, target, root, findings)
            elif not stat.S_ISREG(metadata.st_mode):
                findings.append(Finding("special-file", "warning", "Special filesystem entry was not inspected", _rel(root, path), 1, _file_kind(metadata.st_mode), "Replace it with a regular release artifact or document why it is outside the release boundary."))
            else:
                _cache_regular_file(path, name, root, findings, files, texts, sizes, samples, file_fingerprints, dir_fd=directory_fd)


def _is_directory_link(path: Path) -> bool:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode):
        return True
    reparse_point = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if getattr(metadata, "st_file_attributes", 0) & reparse_point:
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def _collect_with_paths(
    root: Path,
    findings: list[Finding],
    files: list[Path],
    texts: dict[Path, str],
    sizes: dict[Path, int],
    samples: dict[Path, bytes],
    file_fingerprints: dict[Path, tuple[int, int, int, int, int]],
    directory_fingerprints: dict[Path, tuple[int, int, int, int, int]],
) -> None:
    def onerror(exc: OSError) -> None:
        _record_walk_error(root, findings, exc)

    for current, dirs, names in os.walk(root, topdown=True, onerror=onerror, followlinks=False):
        current_path = Path(current)
        try:
            resolved_current = _resolve_path(current_path, strict=True)
            metadata = current_path.lstat()
        except OSError as exc:
            _record_scan_error(current_path, root, "Directory could not be inspected", type(exc).__name__, findings)
            dirs[:] = []
            continue
        if not resolved_current.is_relative_to(root) or not stat.S_ISDIR(metadata.st_mode):
            _record_scan_error(current_path, root, "Directory escaped the repository boundary", "link or junction", findings)
            dirs[:] = []
            continue
        directory_fingerprints[current_path] = _fingerprint(metadata)
        inside_git = current_path != root and _inside_git(root, current_path)
        if inside_git:
            dirs[:] = []
            names = [name for name in names if name.casefold() == "config"]
        kept_dirs = []
        for name in sorted(dirs):
            path = current_path / name
            try:
                if _is_directory_link(path):
                    target = os.readlink(path) if path.is_symlink() else "[junction target redacted]"
                    _record_symlink(path, target, root, findings)
                elif not _is_git_name(name) or current_path == root:
                    kept_dirs.append(name)
            except OSError as exc:
                _record_scan_error(path, root, "Filesystem entry could not be inspected", type(exc).__name__, findings)
        dirs[:] = kept_dirs
        for name in sorted(names):
            path = current_path / name
            try:
                metadata = path.lstat()
            except OSError as exc:
                _record_scan_error(path, root, "Filesystem entry could not be inspected", type(exc).__name__, findings)
                continue
            if stat.S_ISLNK(metadata.st_mode):
                try:
                    target = os.readlink(path)
                except OSError:
                    target = "unreadable target"
                _record_symlink(path, target, root, findings)
            elif not stat.S_ISREG(metadata.st_mode):
                findings.append(Finding("special-file", "warning", "Special filesystem entry was not inspected", _rel(root, path), 1, _file_kind(metadata.st_mode), "Replace it with a regular release artifact or document why it is outside the release boundary."))
            else:
                try:
                    resolved = _resolve_path(path, strict=True)
                except OSError as exc:
                    _record_scan_error(path, root, "File could not be inspected", type(exc).__name__, findings)
                    continue
                if not resolved.is_relative_to(root) or resolved != path:
                    _record_scan_error(path, root, "File escaped the repository boundary", "link or junction", findings)
                    continue
                _cache_regular_file(path, path, root, findings, files, texts, sizes, samples, file_fingerprints, verify_root=root)


def _verify_stable_tree(
    root: Path,
    directory_fingerprints: dict[Path, tuple[int, int, int, int, int]],
    file_fingerprints: dict[Path, tuple[int, int, int, int, int]],
    files: list[Path],
    texts: dict[Path, str],
    sizes: dict[Path, int],
    samples: dict[Path, bytes],
    findings: list[Finding],
) -> None:
    def discard(path: Path, *, descendants: bool) -> None:
        # ponytail: mutation handling may scan the cache repeatedly; index by parent only if hostile churn becomes a real workload.
        affected = [item for item in files if item == path or (descendants and path in item.parents)]
        for item in affected:
            texts.pop(item, None)
            sizes.pop(item, None)
            samples.pop(item, None)
        files[:] = [item for item in files if item not in affected]

    changed_directories: list[Path] = []
    for path, expected in sorted(directory_fingerprints.items(), key=lambda item: (len(item[0].parts), item[0].as_posix())):
        if any(path == changed or changed in path.parents for changed in changed_directories):
            continue
        try:
            current = path.lstat()
        except OSError:
            current = None
        if current is None or not stat.S_ISDIR(current.st_mode) or _fingerprint(current) != expected:
            _record_scan_error(path, root, "Repository changed during scan", "directory metadata changed", findings)
            changed_directories.append(path)
            discard(path, descendants=True)
    for path, expected in sorted(file_fingerprints.items(), key=lambda item: item[0].as_posix()):
        if any(changed in path.parents for changed in changed_directories):
            continue
        try:
            current = path.lstat()
        except OSError:
            current = None
        if current is None or not stat.S_ISREG(current.st_mode) or _fingerprint(current) != expected:
            _record_scan_error(path, root, "Repository changed during scan", "file metadata changed", findings)
            discard(path, descendants=False)


def _host(raw_url: str) -> str:
    if "://" not in raw_url and "@" in raw_url:
        return raw_url.split("@", 1)[1].split(":", 1)[0].lower()
    try:
        return (urlparse(raw_url).hostname or "").lower()
    except ValueError:
        return ""


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
        return "." not in host


def _redact_url(raw_url: str) -> str:
    redacted = raw_url
    if "://" not in redacted and "@" in redacted:
        userinfo, location = redacted.split("@", 1)
        if userinfo.lower() not in {"git", "hg", "svn"}:
            redacted = "[redacted]@" + location
    if "://" in redacted:
        scheme, remainder = redacted.split("://", 1)
        boundary = min((position for token in "/?#" if (position := remainder.find(token)) >= 0), default=len(remainder))
        authority, suffix = remainder[:boundary], remainder[boundary:]
        if "@" in authority:
            userinfo, host = authority.rsplit("@", 1)
            if scheme.lower() in {"http", "https"} or ":" in userinfo or userinfo.lower() not in {"git", "hg", "svn"}:
                authority = "[redacted]@" + host
        redacted = f"{scheme}://{authority}{suffix}"
    return SENSITIVE_QUERY_RE.sub(r"\1[redacted]", redacted)


def _has_userinfo(raw_url: str) -> bool:
    if "://" not in raw_url:
        return "@" in raw_url
    remainder = raw_url.split("://", 1)[1]
    boundary = min((position for token in "/?#" if (position := remainder.find(token)) >= 0), default=len(remainder))
    return "@" in remainder[:boundary]


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


def _manifest_licenses(root: Path, texts: dict[Path, str], findings: list[Finding]) -> list[tuple[str, str, int]]:
    result: list[tuple[str, str, int]] = []
    package = root / "package.json"
    if package.is_file():
        try:
            data = json.loads(texts[package])
            value = data.get("license")
            if isinstance(value, str) and value.strip():
                result.append(("package.json", value.strip().upper(), 1))
        except KeyError:
            pass
        except json.JSONDecodeError as exc:
            findings.append(Finding("manifest-invalid", "warning", "Manifest could not be parsed", "package.json", 1, type(exc).__name__, "Repair the manifest before release review."))
    for filename in ("pyproject.toml", "Cargo.toml"):
        path = root / filename
        text = texts.get(path)
        if text is None:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if filename == "pyproject.toml" and re.match(r"\s*license\s*=\s*\{", line, re.I):
                table = re.fullmatch(
                    r"""\s*license\s*=\s*\{\s*(text|file)\s*=\s*("[^"\\]*"|'[^']*')\s*\}\s*(?:#.*)?""",
                    line, re.I,
                )
                if table is None:
                    findings.append(Finding("manifest-invalid", "warning", "License table requires manual review", filename, number, "Unsupported or malformed single-line license table", "Use one text or file key; review multiline and escaped declarations manually."))
                elif table.group(1).lower() == "file":
                    findings.append(Finding("license-unverified", "warning", "File-based license requires manual review", filename, number, "License declared through a file reference (not followed)", "Review the referenced license and its ownership; this scanner does not follow license paths."))
                else:
                    value = table.group(2)[1:-1].strip()
                    identifier = _license_id(value)
                    if identifier == "UNKNOWN" and re.fullmatch(r"[A-Za-z0-9.+-]+", value):
                        identifier = value.upper()
                    if identifier == "UNKNOWN" or not value:
                        findings.append(Finding("license-unverified", "warning", "License text requires manual review", filename, number, "Unrecognized license text", "Review the license text; heuristic recognition is not legal clearance."))
                    else:
                        result.append((filename, identifier, number))
                break
            match = re.match(r"\s*license\s*=\s*[\"']([^\"']+)[\"']", line, re.I)
            if match:
                result.append((filename, match.group(1).strip().upper(), number))
                break
    return result


def _check_licenses(root: Path, texts: dict[Path, str], findings: list[Finding]) -> None:
    declared: list[tuple[str, str, int]] = []
    for path in sorted(root.iterdir(), key=lambda p: p.name):
        if path.is_file() and path.name.upper().startswith(("LICENSE", "COPYING")):
            text = texts.get(path)
            if text is not None:
                declared.append((_rel(root, path), _license_id(text), 1))
    declared.extend(_manifest_licenses(root, texts, findings))
    known = {identifier for _, identifier, _ in declared if identifier != "UNKNOWN"}
    if not declared:
        findings.append(Finding("license-missing", "warning", "No license declaration found", ".", 1, "No LICENSE/COPYING file or supported manifest license", "Record the intended license after ownership review."))
    if any(identifier in {"UNLICENSED", "PROPRIETARY"} for _, identifier, _ in declared):
        path, identifier, line = next(item for item in declared if item[1] in {"UNLICENSED", "PROPRIETARY"})
        findings.append(Finding("license-private", "error", "Manifest declares a non-public license", path, line, identifier, "Resolve the release license and align all manifests."))
    if len(known) > 1:
        evidence = ", ".join(f"{path}={identifier}" for path, identifier, _ in sorted(declared))
        findings.append(Finding("license-conflict", "error", "License declarations conflict", ".", 1, evidence, "Have the owner resolve the declarations; this tool does not provide legal advice."))


def _check_provenance(root: Path, texts: dict[Path, str], findings: list[Finding]) -> None:
    path = root / "PROVENANCE.md"
    text = texts.get(path)
    if text is None:
        findings.append(Finding("provenance-missing", "error", "Provenance record is missing", "PROVENANCE.md", 1, "File not found", "Create a provenance record for specifications, fixtures, code, and generated assets."))
        return
    rows = [line for line in text.splitlines() if line.startswith("|") and "---" not in line]
    if len(rows) < 2:
        findings.append(Finding("provenance-empty", "warning", "Provenance record has no source rows", "PROVENANCE.md", 1, "No Markdown table data rows found", "Record each source, version, purpose, and applicable terms."))


def _check_urls(root: Path, texts: dict[Path, str], findings: list[Finding]) -> None:
    registry_names = {".npmrc", ".pypirc", "pip.conf", "pip.ini"}
    for path, text in sorted(texts.items(), key=lambda item: _rel(root, item[0])):
        rel = _rel(root, path)
        for match in URL_RE.finditer(text):
            raw = match.group(0).rstrip(".,;")
            host = _host(raw)
            line = _line_for(text, match.start())
            evidence = _redact_url(raw)
            if _is_internal_host(host):
                findings.append(Finding("internal-url", "critical", "Internal URL crosses the release boundary", rel, line, evidence, "Remove, redact, or replace the internal endpoint with a public synthetic example."))
            is_registry_config = path.name.casefold() in registry_names or rel.casefold() in {".cargo/config", ".cargo/config.toml"}
            if is_registry_config and host and host not in PUBLIC_REGISTRIES:
                findings.append(Finding("private-registry", "error", "Non-public package registry configured", rel, line, evidence, "Replace the registry or document a public installation path."))
            if rel.casefold() == ".git/config" and (_has_userinfo(raw) or raw.lower().startswith("ssh://") or _is_internal_host(host)):
                findings.append(Finding("private-remote", "warning" if host in PUBLIC_GIT_HOSTS else "error", "Remote may require private credentials", rel, line, evidence, "Remove local/private remote lineage from the release copy and verify the public origin."))


def _check_submodules(root: Path, texts: dict[Path, str], findings: list[Finding]) -> None:
    path = root / ".gitmodules"
    text = texts.get(path)
    if text is None:
        return
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r"\s*url\s*=\s*(.+?)\s*$", line)
        if not match:
            continue
        url = match.group(1)
        host = _host(url)
        severity = "critical" if _is_internal_host(host) else "warning"
        findings.append(Finding("submodule-lineage", severity, "Submodule requires independent lineage review", ".gitmodules", number, _redact_url(url), "Verify source, commit, license, public availability, and provenance before release."))


def _check_binary(
    root: Path,
    files: list[Path],
    texts: dict[Path, str],
    sizes: dict[Path, int],
    samples: dict[Path, bytes],
    findings: list[Finding],
) -> None:
    for path in files:
        rel = _rel(root, path)
        size = sizes[path]
        sample = samples[path]
        if sample.startswith(b"version https://git-lfs.github.com/spec/v1"):
            findings.append(Finding("lfs-pointer", "warning", "Git LFS object requires provenance review", rel, 1, "Git LFS pointer", "Verify the referenced object is available, redistributable, and recorded in provenance."))
        elif b"\0" in sample or (sample and path not in texts and size <= TEXT_LIMIT):
            findings.append(Finding("binary-file", "warning", "Binary file cannot be source-reviewed locally", rel, 1, f"{size} bytes", "Remove it or record its origin, generation method, terms, and reproducible source."))
        if size > TEXT_LIMIT:
            findings.append(Finding("large-file", "warning", "Large file skipped by text checks", rel, 1, f"{size} bytes", "Review the file manually and record its provenance."))
    attributes = texts.get(root / ".gitattributes")
    if attributes:
        for number, line in enumerate(attributes.splitlines(), 1):
            if "filter=lfs" in line:
                findings.append(Finding("lfs-rule", "warning", "Git LFS tracking rule present", ".gitattributes", number, line.strip(), "Verify every matched object is present, public, and redistributable."))


def scan_repository(root: Path) -> dict[str, object]:
    root = _resolve_path(root)
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    findings: list[Finding] = []
    files: list[Path] = []
    texts: dict[Path, str] = {}
    sizes: dict[Path, int] = {}
    samples: dict[Path, bytes] = {}
    file_fingerprints: dict[Path, tuple[int, int, int, int, int]] = {}
    directory_fingerprints: dict[Path, tuple[int, int, int, int, int]] = {}
    supports_fd_walk = (
        hasattr(os, "fwalk")
        and os.open in os.supports_dir_fd
        and os.stat in os.supports_dir_fd
        and os.readlink in os.supports_dir_fd
    )
    collector = _collect_with_fwalk if supports_fd_walk else _collect_with_paths
    collector(root, findings, files, texts, sizes, samples, file_fingerprints, directory_fingerprints)
    _verify_stable_tree(root, directory_fingerprints, file_fingerprints, files, texts, sizes, samples, findings)
    git_marker = next((path for path in texts if path.parent == root and _is_git_name(path.name)), root / ".git")
    marker_text = texts.get(git_marker)
    if marker_text is not None and re.match(r"\s*gitdir\s*:", marker_text, re.I):
        findings.append(Finding("git-metadata-indirect", "warning", "Git metadata is stored outside this worktree", ".git", 1, "gitdir: [local path redacted]", "Review the worktree's effective remotes and Git configuration before release."))
    _check_licenses(root, texts, findings)
    _check_provenance(root, texts, findings)
    _check_urls(root, texts, findings)
    _check_submodules(root, texts, findings)
    _check_binary(root, files, texts, sizes, samples, findings)
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
        title = html.escape(str(finding["title"]))
        rows.append(
            f'<article class="finding {html.escape(str(finding["severity"]))}" id="{fid}" aria-labelledby="{fid}-title">'
            f'<h3 id="{fid}-title"><a href="#{fid}" aria-label="Permalink to finding: {title}">#</a> '
            f'<code>{fid}</code> · {title}</h3>'
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
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        os.replace(temporary, path)
    except BaseException:
        if temporary is not None:
            try:
                temporary.unlink()
            except OSError:
                pass
        raise


def _write_stdout(content: str) -> None:
    encoded = content.encode("utf-8")
    buffer = getattr(os.sys.stdout, "buffer", None)
    if buffer is None:
        os.sys.stdout.write(content)
    else:
        buffer.write(encoded)


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
    try:
        output = json_text(report)
        if args.json_path == "-":
            _write_stdout(output)
        else:
            _write_atomic(Path(args.json_path), output)
        if args.html_path:
            _write_atomic(Path(args.html_path), html_text(report))
    except (OSError, UnicodeError) as exc:
        print(f"releasefence: could not write report: {exc}", file=os.sys.stderr)
        return 2
    if args.fail_on == "none":
        return 0
    threshold = SEVERITY[args.fail_on]
    return 1 if any(SEVERITY[f["severity"]] >= threshold for f in report["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
