#!/usr/bin/env python3
"""Rehearse the release job's asset directory: manifest script, checksums, and the asset gate."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST_SH = HERE / "launcher-manifest.sh"
CHECK_PY = HERE / "check_release_assets.py"


def check(release_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, CHECK_PY, release_dir], capture_output=True, text=True)


class ReleaseAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="redrob-cut-release-")
        self.addCleanup(self.temp.cleanup)
        self.release = Path(self.temp.name)
        # Stand-ins for what the platform jobs upload as artifacts.
        for name in ("redrob-cut-0.0.0-linux-x86_64.AppImage", "redrob-cut-0.0.0-windows-x86_64.msi"):
            (self.release / name).write_bytes(b"stub installer\n")

    def checksums(self):
        out = subprocess.run(["sha256sum", "--", *sorted(p.name for p in self.release.iterdir())],
                             cwd=self.release, check=True, capture_output=True, text=True).stdout
        (self.release / "SHA256SUMS.txt").write_text(out)

    def test_manifest_content(self):
        subprocess.run(["bash", MANIFEST_SH, self.release], check=True, capture_output=True)
        raw = (self.release / "redrob-launcher.json").read_bytes()
        self.assertEqual(raw, b'{ "schema": 1, "sharedAccount": true }\n')
        data = json.loads(raw)
        self.assertEqual(data["schema"], 1)
        self.assertIs(data["sharedAccount"], True)

    def test_release_layout_rehearsal(self):
        # The release job's order: platform artifacts, manifest, checksums, gate, upload.
        subprocess.run(["bash", MANIFEST_SH, self.release], check=True, capture_output=True)
        self.checksums()
        listed = (self.release / "SHA256SUMS.txt").read_text()
        self.assertIn("  redrob-launcher.json\n", listed)
        result = check(self.release)
        self.assertEqual(result.returncode, 0, result.stderr)
        print("\n" + listed.rstrip())

    def test_missing_manifest_fails(self):
        self.checksums()
        result = check(self.release)
        self.assertEqual(result.returncode, 1)
        self.assertIn("redrob-launcher.json is missing", result.stderr)

    def test_manifest_not_in_checksums_fails(self):
        self.checksums()  # before the manifest: the sums file does not list it
        subprocess.run(["bash", MANIFEST_SH, self.release], check=True, capture_output=True)
        result = check(self.release)
        self.assertEqual(result.returncode, 1)
        self.assertIn("SHA256SUMS.txt does not list redrob-launcher.json", result.stderr)

    def test_bad_content_fails(self):
        cases = {
            b'{ "schema": 2, "sharedAccount": true }\n': "schema must be 1",
            b'{ "schema": 1, "sharedAccount": false }\n': "sharedAccount must be true",
            b'{ "schema": 1, "sharedAccount": 1 }\n': "sharedAccount must be true",
            b'{ "schema": 1, "sharedAccount": true }': "must end in a newline",
            b"not json\n": "not valid JSON",
            b"[]\n": "must be a JSON object",
        }
        for raw, message in cases.items():
            with self.subTest(raw=raw):
                (self.release / "redrob-launcher.json").write_bytes(raw)
                result = check(self.release)
                self.assertEqual(result.returncode, 1, raw)
                self.assertIn(message, result.stderr)

    def test_usage_errors(self):
        self.assertEqual(subprocess.run(["bash", MANIFEST_SH], capture_output=True).returncode, 2)
        self.assertEqual(check(self.release / "nope").returncode, 2)


if __name__ == "__main__":
    unittest.main()
