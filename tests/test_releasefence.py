import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
