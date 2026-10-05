import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import releasefence  # noqa: E402


MIT = "MIT License\n\nPermission is hereby granted, free of charge, to any person obtaining a copy.\n"


class ReleaseFenceTests(unittest.TestCase):
    def make_green(self, root: Path) -> None:
        (root / "LICENSE").write_text(MIT, encoding="utf-8")
        (root / "package.json").write_text('{"license":"MIT","name":"synthetic"}\n', encoding="utf-8")
        (root / "PROVENANCE.md").write_text(
            "| Source | Purpose | Terms |\n|---|---|---|\n| Synthetic fixture | Test | Original |\n",
            encoding="utf-8",
        )

    def test_green_report_is_deterministic_across_directories(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            self.make_green(Path(first))
            self.make_green(Path(second))
            one = releasefence.scan_repository(Path(first))
            two = releasefence.scan_repository(Path(second))
            self.assertEqual("green", one["status"])
            self.assertEqual(releasefence.json_text(one), releasefence.json_text(two))

    def test_portable_path_walker_preserves_green_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_green(root)
            with mock.patch.object(releasefence.os, "supports_dir_fd", set()):
                report = releasefence.scan_repository(root)
            self.assertEqual("green", report["status"])

    def test_portable_path_walker_prunes_case_variant_git_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_green(root)
            git_directory = root / ".GIT"
            objects = git_directory / "objects"
            objects.mkdir(parents=True)
            (git_directory / "config").write_text(
                '[remote "origin"]\n url = oauth-secret@github.com:owner/repository.git\n',
                encoding="utf-8",
            )
            (objects / "leak").write_text("http://internal-host/cb?token=hunter2\n", encoding="utf-8")

            with mock.patch.object(releasefence.os, "supports_dir_fd", set()):
                report = releasefence.scan_repository(root)

            private_remote = next(item for item in report["findings"] if item["rule"] == "private-remote")
            self.assertEqual(".GIT/config", private_remote["fact"]["path"])
            self.assertFalse(any(item["fact"]["path"] == ".GIT/objects/leak" for item in report["findings"]))
            self.assertNotIn("hunter2", releasefence.json_text(report))

    def test_red_report_explains_every_boundary_category(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "LICENSE").write_text(MIT, encoding="utf-8")
            (root / "package.json").write_text('{"license":"GPL-3.0"}\n', encoding="utf-8")
            (root / ".npmrc").write_text("registry=https://packages.corp.internal/npm\n", encoding="utf-8")
            (root / ".gitmodules").write_text(
                '[submodule "engine"]\n path = vendor/engine\n url = ssh://git@source.corp.internal/engine.git\n',
                encoding="utf-8",
            )
            (root / "asset.bin").write_bytes(b"\x00\x01\x02")
            report = releasefence.scan_repository(root)
            rules = {finding["rule"] for finding in report["findings"]}
            self.assertEqual("red", report["status"])
            self.assertTrue(
                {"license-conflict", "private-registry", "internal-url", "submodule-lineage", "binary-file", "provenance-missing"}.issubset(rules)
            )
            rendered = releasefence.html_text(report)
            self.assertIn('class="skip-link"', rendered)
            self.assertIn('<main id="content">', rendered)
            self.assertIn('aria-label="Permalink to finding:', rendered)
            self.assertNotIn("<script", rendered.lower())
            for finding in report["findings"]:
                self.assertIn(f'id="{finding["id"]}"', rendered)
                self.assertIn(f'href="#{finding["id"]}"', rendered)

    def test_cli_writes_json_and_html(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            self.make_green(repo)
            json_path, html_path = root / "report.json", root / "report.html"
            result = subprocess.run(
                [sys.executable, str(ROOT / "releasefence.py"), "scan", str(repo), "--json", str(json_path), "--html", str(html_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("green", json.loads(json_path.read_text(encoding="utf-8"))["status"])
            self.assertIn("ReleaseFence report", html_path.read_text(encoding="utf-8"))

    def test_large_and_special_files_are_bounded_and_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_green(root)
            (root / "large.txt").write_bytes(b"x" * (releasefence.TEXT_LIMIT + 1))
            if hasattr(os, "mkfifo"):
                os.mkfifo(root / "events.pipe")
            report = releasefence.scan_repository(root)
            rules = {finding["rule"] for finding in report["findings"]}
            self.assertIn("large-file", rules)
            if hasattr(os, "mkfifo"):
                self.assertIn("special-file", rules)
            self.assertEqual("amber", report["status"])

    def test_directory_symlink_and_worktree_metadata_are_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_green(root)
            target = root / "target"
            target.mkdir()
            (target / "note.txt").write_text("synthetic\n", encoding="utf-8")
            try:
                (root / "linked").symlink_to(target, target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("directory symlinks are unavailable")
            (root / ".git").write_text("gitdir: /synthetic/local/worktree\n", encoding="utf-8")
            report = releasefence.scan_repository(root)
            by_rule = {finding["rule"]: finding for finding in report["findings"]}
            self.assertEqual("linked", by_rule["symlink-lineage"]["fact"]["path"])
            self.assertEqual("gitdir: [local path redacted]", by_rule["git-metadata-indirect"]["fact"]["evidence"])

    def test_read_failures_cannot_produce_a_green_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_green(root)
            blocked = root / "blocked.txt"
            blocked.write_text("synthetic\n", encoding="utf-8")
            original = releasefence._inspect_regular_file

            def inspect(path, **kwargs):
                if Path(path).name == blocked.name:
                    raise PermissionError("synthetic")
                return original(path, **kwargs)

            with mock.patch.object(releasefence, "_inspect_regular_file", side_effect=inspect):
                report = releasefence.scan_repository(root)
            finding = next(item for item in report["findings"] if item["rule"] == "scan-incomplete")
            self.assertEqual("red", report["status"])
            self.assertEqual("PermissionError", finding["fact"]["evidence"])

    def test_url_rules_are_scoped_and_sensitive_evidence_is_redacted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_green(root)
            (root / "config.toml").write_text("docs = 'https://example.com/docs'\n", encoding="utf-8")
            (root / "service.txt").write_text("endpoint=http://jenkins:8080/job?token=hunter2\n", encoding="utf-8")
            report = releasefence.scan_repository(root)
            self.assertNotIn("private-registry", {item["rule"] for item in report["findings"]})
            finding = next(item for item in report["findings"] if item["rule"] == "internal-url")
            self.assertIn("[redacted]", finding["fact"]["evidence"])
            self.assertNotIn("hunter2", releasefence.json_text(report))

    def test_registry_config_matching_is_case_insensitive_and_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_green(root)
            cargo = root / ".CARGO"
            cargo.mkdir()
            registry = "registry=https://packages.example.test/npm\n"
            for path in (root / ".NPMRC", root / "PIP.INI", cargo / "CONFIG"):
                path.write_text(registry, encoding="utf-8")
            (root / "ordinary.txt").write_text(registry, encoding="utf-8")

            report = releasefence.scan_repository(root)

            registry_paths = {item["fact"]["path"] for item in report["findings"] if item["rule"] == "private-registry"}
            self.assertEqual({".NPMRC", "PIP.INI", ".CARGO/CONFIG"}, registry_paths)
            self.assertNotIn("ordinary.txt", registry_paths)

    def test_ipv6_and_fragment_credentials_are_handled_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_green(root)
            (root / "service.txt").write_text(
                "ipv6=http://[::1]/callback#access_token=hunter2\nmalformed=http://[broken\n",
                encoding="utf-8",
            )
            report = releasefence.scan_repository(root)
            finding = next(item for item in report["findings"] if item["rule"] == "internal-url")
            self.assertIn("http://[::1]/callback#access_token=[redacted]", finding["fact"]["evidence"])
            self.assertNotIn("hunter2", releasefence.json_text(report))
            self.assertEqual("git://[redacted]@example.com/repo", releasefence._redact_url("git://oauth-token@example.com/repo"))

    def test_scp_style_git_credentials_are_redacted_and_classified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_green(root)
            (root / ".gitmodules").write_text(
                '[submodule "engine"]\n path = engine\n url = oauth-secret@source.internal:team/private.git\n',
                encoding="utf-8",
            )
            report = releasefence.scan_repository(root)
            rules = {item["rule"] for item in report["findings"]}
            rendered = releasefence.json_text(report)
            self.assertIn("internal-url", rules)
            self.assertIn("submodule-lineage", rules)
            self.assertIn("[redacted]@source.internal", rendered)
            self.assertNotIn("oauth-secret", rendered)

    def test_scp_style_public_remote_is_still_visible_for_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_green(root)
            git_directory = root / ".git"
            git_directory.mkdir()
            (git_directory / "config").write_text(
                "[remote \"origin\"]\n url = oauth-secret@github.com:owner/repository.git\n",
                encoding="utf-8",
            )
            report = releasefence.scan_repository(root)
            finding = next(item for item in report["findings"] if item["rule"] == "private-remote")
            self.assertEqual("warning", finding["severity"])
            self.assertIn("[redacted]@github.com", finding["fact"]["evidence"])
            self.assertNotIn("oauth-secret", releasefence.json_text(report))

    def test_https_public_remote_with_userinfo_is_visible_for_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_green(root)
            git_directory = root / ".git"
            git_directory.mkdir()
            (git_directory / "config").write_text(
                "[remote \"origin\"]\n url = https://oauth-secret@github.com/owner/repository.git\n",
                encoding="utf-8",
            )
            report = releasefence.scan_repository(root)
            finding = next(item for item in report["findings"] if item["rule"] == "private-remote")
            self.assertEqual("warning", finding["severity"])
            self.assertIn("https://[redacted]@github.com", finding["fact"]["evidence"])
            self.assertNotIn("oauth-secret", releasefence.json_text(report))

    def test_url_schemes_are_case_insensitive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_green(root)
            (root / "service.txt").write_text("HTTP://jenkins.internal/cb?token=hunter2\n", encoding="utf-8")
            git_directory = root / ".git"
            git_directory.mkdir()
            (git_directory / "config").write_text(
                "[remote \"origin\"]\n url = SSH://git@github.com/owner/repository.git\n",
                encoding="utf-8",
            )
            report = releasefence.scan_repository(root)
            rules = {item["rule"] for item in report["findings"]}
            rendered = releasefence.json_text(report)
            self.assertIn("internal-url", rules)
            self.assertIn("private-remote", rules)
            self.assertIn("token=[redacted]", rendered)
            self.assertNotIn("hunter2", rendered)

    def test_git_directory_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, outside = root / "repo", root / "outside"
            repo.mkdir()
            outside.mkdir()
            self.make_green(repo)
            (outside / "config").write_text("url = ssh://git@source.corp.internal/repo\n", encoding="utf-8")
            try:
                (repo / ".git").symlink_to(outside, target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("directory symlinks are unavailable")
            report = releasefence.scan_repository(repo)
            self.assertIn("symlink-lineage", {item["rule"] for item in report["findings"]})
            self.assertNotIn("internal-url", {item["rule"] for item in report["findings"]})
            self.assertNotIn(".git/config", releasefence.json_text(report))

    @unittest.skipUnless(
        hasattr(os, "fwalk") and os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd,
        "descriptor-relative traversal is unavailable",
    )
    def test_directory_swap_cannot_redirect_a_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, outside = root / "repo", root / "outside"
            repo.mkdir()
            outside.mkdir()
            self.make_green(repo)
            source = repo / "source"
            source.mkdir()
            (source / "victim.txt").write_text("public synthetic text\n", encoding="utf-8")
            (outside / "victim.txt").write_text("http://internal-host/cb?token=hunter2\n", encoding="utf-8")
            moved = repo / "source-original"
            original = releasefence._inspect_regular_file
            swapped = False

            def inspect(path, **kwargs):
                nonlocal swapped
                if Path(path).name == "victim.txt" and not swapped:
                    swapped = True
                    source.rename(moved)
                    source.symlink_to(outside, target_is_directory=True)
                return original(path, **kwargs)

            with mock.patch.object(releasefence, "_inspect_regular_file", side_effect=inspect):
                report = releasefence.scan_repository(repo)
            self.assertTrue(swapped)
            self.assertIn("scan-incomplete", {item["rule"] for item in report["findings"]})
            self.assertNotIn("hunter2", releasefence.json_text(report))
            self.assertNotIn("internal-url", {item["rule"] for item in report["findings"]})

    def test_portable_walker_validates_the_open_handle_before_reading(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, outside = root / "repo", root / "outside"
            repo.mkdir()
            outside.mkdir()
            self.make_green(repo)
            source = repo / "source"
            source.mkdir()
            (source / "victim.txt").write_text("public synthetic text\n", encoding="utf-8")
            outside_file = outside / "victim.txt"
            outside_file.write_text("http://internal-host/cb?token=hunter2\n", encoding="utf-8")
            outside_identity = (outside_file.stat().st_dev, outside_file.stat().st_ino)
            moved = repo / "source-original"
            original_inspect = releasefence._inspect_regular_file
            original_fdopen = os.fdopen
            swapped = False
            outside_read = False

            def inspect(path, **kwargs):
                nonlocal swapped
                if Path(path).name == "victim.txt" and not swapped:
                    swapped = True
                    source.rename(moved)
                    source.symlink_to(outside, target_is_directory=True)
                return original_inspect(path, **kwargs)

            def tracking_fdopen(descriptor, *args, **kwargs):
                nonlocal outside_read
                metadata = os.fstat(descriptor)
                if (metadata.st_dev, metadata.st_ino) == outside_identity:
                    outside_read = True
                return original_fdopen(descriptor, *args, **kwargs)

            with (
                mock.patch.object(releasefence.os, "supports_dir_fd", set()),
                mock.patch.object(releasefence, "_inspect_regular_file", side_effect=inspect),
                mock.patch.object(releasefence.os, "fdopen", side_effect=tracking_fdopen),
            ):
                report = releasefence.scan_repository(repo)
            self.assertTrue(swapped)
            self.assertFalse(outside_read)
            self.assertIn("scan-incomplete", {item["rule"] for item in report["findings"]})
            self.assertNotIn("hunter2", releasefence.json_text(report))

    def test_absolute_symlink_evidence_is_redacted_and_deterministic(self):
        reports = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.make_green(root)
                target = root / "target"
                target.mkdir()
                try:
                    (root / "linked").symlink_to(target, target_is_directory=True)
                except (NotImplementedError, OSError):
                    self.skipTest("directory symlinks are unavailable")
                reports.append(releasefence.json_text(releasefence.scan_repository(root)))
        self.assertEqual(reports[0], reports[1])
        self.assertIn("[absolute target redacted]", reports[0])

    def test_cross_platform_absolute_targets_and_reparse_points_are_redacted(self):
        for target in (r"C:\Users\alice\secret", r"\\server\share\secret", "/Users/alice/secret", r"\Users\alice\secret"):
            self.assertEqual("[absolute target redacted]", releasefence._symlink_evidence(target))
        path = mock.Mock()
        path.lstat.return_value = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        self.assertTrue(releasefence._is_directory_link(path))

    def test_failed_atomic_write_removes_the_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            temporary = root / "partial"

            class FailingFile:
                name = str(temporary)

                def __enter__(self):
                    temporary.write_text("partial", encoding="utf-8")
                    return self

                def __exit__(self, *_args):
                    return False

                def write(self, _content):
                    raise OSError("synthetic disk failure")

            with mock.patch.object(releasefence.tempfile, "NamedTemporaryFile", return_value=FailingFile()):
                with self.assertRaises(OSError):
                    releasefence._write_atomic(root / "report.json", "{}\n")
            self.assertFalse(temporary.exists())

    def test_cli_reports_output_errors_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            self.make_green(repo)
            result = subprocess.run(
                [sys.executable, str(ROOT / "releasefence.py"), "scan", str(repo), "--json", str(root)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, result.returncode)
            self.assertIn("could not write report", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_cli_reports_symlink_loop_root_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second = root / "first", root / "second"
            try:
                first.symlink_to(second, target_is_directory=True)
                second.symlink_to(first, target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("directory symlinks are unavailable")

            result = subprocess.run(
                [sys.executable, str(ROOT / "releasefence.py"), "scan", str(first)],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(2, result.returncode)
            self.assertIn("releasefence:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_stdout_report_is_utf8_with_lf_newlines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_green(root)
            (root / "unicodé.bin").write_bytes(b"\x00\x01")
            result = subprocess.run(
                [sys.executable, str(ROOT / "releasefence.py"), "scan", str(root), "--json", "-"],
                check=False,
                capture_output=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertNotIn(b"\r\n", result.stdout)
            decoded = result.stdout.decode("utf-8")
            self.assertIn("unicodé.bin", decoded)
            self.assertEqual("amber", json.loads(decoded)["status"])

    def test_top_level_version_does_not_require_a_subcommand(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "releasefence.py"), "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("releasefence 0.1.1\n", result.stdout)


if __name__ == "__main__":
    unittest.main()
