import tempfile
import unittest
from pathlib import Path

import releasefence

MIT = "MIT License\nPermission is hereby granted, free of charge, to any person obtaining a copy.\n"


class LicenseReviewRegressionTests(unittest.TestCase):
    def scan(self, declaration, *, root_license=True):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            if root_license:
                (root / "LICENSE").write_text(MIT, encoding="utf-8")
            (root / "PROVENANCE.md").write_text(
                "| Source | Purpose | Terms |\n|---|---|---|\n| Synthetic | Test | Original |\n",
                encoding="utf-8",
            )
            (root / "pyproject.toml").write_text(declaration, encoding="utf-8")
            return releasefence.scan_repository(root)

    def test_table_does_not_hide_first_string_conflict(self):
        for prefix in (
            '[project]\nlicense = {text = "MIT"}\n',
            '[tool.synthetic]\nlicense = {text = "MIT"}\n',
            '[project]\ndescription = """\nlicense = {text = "MIT"}\n"""\n',
            '[project]\nlicense = {file = "../outside-LICENSE"}\n',
        ):
            with self.subTest(prefix=prefix):
                report = self.scan(prefix + '\n[tool.poetry]\nlicense = "GPL-3.0-only"\n')
                self.assertIn("license-conflict", {f["rule"] for f in report["findings"]})
                self.assertEqual(report["status"], "red")

    def test_alternative_table_forms_require_manual_review(self):
        for declaration in (
            '[project]\nlicense.text = "Apache-2.0"\n',
            '[project]\nlicense.file = "../outside-LICENSE"\n',
            '[project.license]\ntext = "Apache-2.0"\n',
            '[project.license] # legacy table\nfile = "../outside-LICENSE"\n',
        ):
            with self.subTest(declaration=declaration):
                report = self.scan(declaration)
                self.assertIn("license-unverified", {f["rule"] for f in report["findings"]})

    def test_file_declaration_is_unverified_not_missing(self):
        report = self.scan('[project]\nlicense = {file = "../outside-LICENSE"}\n', root_license=False)
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("license-unverified", rules)
        self.assertNotIn("license-missing", rules)

    def test_string_declarations_remain_first_wins(self):
        report = self.scan('[project]\nlicense = "MIT"\n[tool.poetry]\nlicense = "GPL-3.0-only"\n')
        self.assertNotIn("license-conflict", {f["rule"] for f in report["findings"]})
