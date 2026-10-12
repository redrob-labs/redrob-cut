#!/usr/bin/env python3
"""No upstream service, store or community endpoint may remain in shipped code or packaging.

Redrob Cut is free and talks to no third-party service of upstream's: no community chat, no
upstream website, no upstream store manifest, no upstream repository in a link the product opens.
This scans the code and packaging trees (not the Markdown documents, where upstream is attributed
on purpose: UPSTREAM.md, NOTICE, ATTRIBUTION.md).

Usage: python3 scripts/check_no_upstream_services.py   (exit 0 = clean)
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_PREFIXES = ("apps/", "crates/", "xtask/", "packaging/", ".github/", ".mcp.json", "Cargo.toml")
SKIP_SUFFIXES = (".md", ".attribution", ".png", ".jpg", ".svg", ".icns", ".ico", ".ttf", ".wav", ".mp4", ".mov", ".mkv")
FORBIDDEN = [
    (re.compile(r"getartcraft\.com"), "upstream website"),
    (re.compile(r"discord\.gg/"), "third-party community chat"),
    (re.compile(r"\bstorytold/"), "upstream organisation as a product or update endpoint"),
    (re.compile(r"storytold/craft-common-actions"), "upstream shared CI"),
    (re.compile(r"\bomastore\b"), "upstream store manifest"),
]
# Lines where upstream's name is a quoted attribution, or the optional craft-fonts build input (OFL
# fonts read from a local checkout; nothing is fetched), rather than a live endpoint.
ALLOW_LINE = re.compile(r"(?i)(upstream|attribution|originally|follows|craft-fonts)")


def main() -> int:
    files = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.split("\0")
    hits: list[str] = []
    for rel in files:
        if not rel or not rel.startswith(SCAN_PREFIXES) or rel.endswith(SKIP_SUFFIXES):
            continue
        try:
            text = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(text.split("\n"), 1):
            for pat, why in FORBIDDEN:
                if pat.search(line) and not ALLOW_LINE.search(line):
                    hits.append(f"{rel}:{n}: {why}: {line.strip()[:120]}")
    if os.path.exists(os.path.join(ROOT, "omastore.toml")):
        hits.append("omastore.toml: upstream store manifest is present")
    for h in hits:
        print(f"error: {h}", file=sys.stderr)
    if hits:
        return 1
    print("no upstream services: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
