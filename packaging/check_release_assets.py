#!/usr/bin/env python3
"""Release asset gate: a release directory is complete only with the launcher manifest.

Checks, for the directory the release job is about to upload:

1. `redrob-launcher.json` exists, is valid JSON, has `schema` 1 and `sharedAccount` true, and ends
   in a newline (the contract in Redrob Launcher's docs/release-manifest.md).
2. If `SHA256SUMS.txt` exists, it lists `redrob-launcher.json`, so the launcher's quota-free path
   (which reads the sums file to learn the asset names) sees the manifest too.

    python3 packaging/check_release_assets.py <release-asset-dir>

Exit status 0 when the directory passes, 1 with one `error:` line per defect otherwise.
"""
import json
import sys
from pathlib import Path

MANIFEST = "redrob-launcher.json"
SUMS = "SHA256SUMS.txt"
EXPECTED = {"schema": 1, "sharedAccount": True}


def check(release_dir: Path) -> list[str]:
    errors = []
    manifest = release_dir / MANIFEST
    if not manifest.is_file():
        return [f"{MANIFEST} is missing from {release_dir}; run packaging/launcher-manifest.sh first"]
    raw = manifest.read_bytes()
    if not raw.endswith(b"\n"):
        errors.append(f"{MANIFEST} must end in a newline")
    try:
        data = json.loads(raw)
    except ValueError as e:
        return errors + [f"{MANIFEST} is not valid JSON: {e}"]
    if not isinstance(data, dict):
        return errors + [f"{MANIFEST} must be a JSON object, got {type(data).__name__}"]
    for key, want in EXPECTED.items():
        got = data.get(key)
        # bool is an int subclass: 1 must not pass for true, nor True for 1.
        if type(got) is not type(want) or got != want:
            errors.append(f"{MANIFEST}: {key} must be {json.dumps(want)}, got {json.dumps(got)}")
    sums = release_dir / SUMS
    if sums.is_file():
        listed = {line.split(maxsplit=1)[1].lstrip("*") for line in sums.read_text().splitlines() if line.strip()}
        if MANIFEST not in listed:
            errors.append(f"{SUMS} does not list {MANIFEST}; write the manifest before the checksums")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <release-asset-dir>", file=sys.stderr)
        return 2
    release_dir = Path(argv[1])
    if not release_dir.is_dir():
        print(f"error: {release_dir} is not a directory", file=sys.stderr)
        return 2
    errors = check(release_dir)
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    if not errors:
        print(f"ok: {release_dir / MANIFEST} is complete")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
