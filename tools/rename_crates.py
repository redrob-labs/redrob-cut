#!/usr/bin/env python3
"""Rename upstream crate names to Redrob's, idempotently.

    filmcraft            -> redrob-film-app        (the desktop shell; its binary is redrob-film)
    filmcraft-<x>        -> redrob-film-<x>        (our fork of storytold/filmcraft, crates/*)
    effectcraft-<x>      -> redrob-effects-<x>     (the storytold/effectcraft subtree, crafts/effectcraft/crates/*)

and the snake_case forms Rust uses in paths (`filmcraft_engine::` -> `redrob_film_engine::`).

What is rewritten: every `[package].name`, dependency key and `-p <crate>` list, every `use`/path
in .rs files, the parked `crafts/effectcraft/Cargo.upstream.toml`, CI, packaging scripts and docs
-- every git-tracked text file except the attribution files (NOTICE, ATTRIBUTION.md, LICENSE-*,
upstream-base.json, *.attribution), UPSTREAM*.md (which documents the rename and names the
upstream crates on purpose) and the two scripts that carry the old names as patterns. Directories
named after a crate (`apps/filmcraft`, `apps/filmcraft-cli`) are `git mv`ed and their paths
rewritten. Cargo.lock follows through `cargo update --workspace --offline` (a lock refresh, not
a build).

The old names are derived from the tree itself: the manifests still carrying an upstream name
(right after a `git subtree pull`) and the reverse of every Redrob name already in place. So the
script is safe to re-run at any time and tools/merge_effectcraft.py runs it after every pull:

    python3 tools/rename_crates.py            # rename in place, print what changed
    python3 tools/rename_crates.py --check    # exit 1 if any upstream crate name is left
    python3 tools/rename_crates.py --no-lock  # skip the Cargo.lock refresh
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APP_OLD, APP_NEW = "filmcraft", "redrob-film-app"
PREFIXES = [("filmcraft-", "redrob-film-"), ("effectcraft-", "redrob-effects-")]

MANIFEST_GLOBS = ["crates/*/Cargo.toml", "apps/*/Cargo.toml", "crafts/effectcraft/crates/*/Cargo.toml"]
UPSTREAM_MANIFEST = ROOT / "crafts" / "effectcraft" / "Cargo.upstream.toml"

# Directories whose name is a crate name.
DIR_MOVES = [("apps/filmcraft-cli", "apps/redrob-film-cli"), ("apps/filmcraft", "apps/redrob-film-app")]

SKIP_FILES = {
    "Cargo.lock",
    "NOTICE",
    "ATTRIBUTION.md",
    "LICENSE-APACHE",
    "LICENSE-MIT",
    "UPSTREAM.md",
    "UPSTREAM.ko.md",
    "upstream-base.json",
    "crafts/effectcraft/NOTICE",
    "crafts/effectcraft/ATTRIBUTION.md",
    "crafts/effectcraft/LICENSE-APACHE",
    "crafts/effectcraft/LICENSE-MIT",
    "tools/rename_crates.py",
    "scripts/check_brand.py",
}
SKIP_SUFFIXES = (
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".icns", ".tiff", ".webp", ".svg", ".ttf", ".otf", ".woff", ".woff2",
    ".mp4", ".mov", ".mkv", ".wav", ".mp3", ".flac", ".bin", ".dat", ".zip", ".gz", ".pdf", ".psd", ".ai",
    ".attribution", ".lock",
)


def to_new(old: str) -> str | None:
    if old == APP_OLD:
        return APP_NEW
    for o, n in PREFIXES:
        if old.startswith(o):
            return n + old[len(o):]
    return None


def to_old(new: str) -> str | None:
    if new == APP_NEW:
        return APP_OLD
    for o, n in PREFIXES:
        if new.startswith(n):
            return o + new[len(n):]
    return None


def crate_names() -> set[str]:
    names: set[str] = set()
    for pat in MANIFEST_GLOBS:
        for m in ROOT.glob(pat):
            try:
                names.add(tomllib.load(m.open("rb"))["package"]["name"])
            except (KeyError, tomllib.TOMLDecodeError):
                pass
    for parked in (UPSTREAM_MANIFEST, UPSTREAM_MANIFEST.with_name("Cargo.toml")):
        if parked.exists():
            try:
                ws = tomllib.load(parked.open("rb")).get("workspace", {})
            except tomllib.TOMLDecodeError:
                continue
            names.update(ws.get("dependencies", {}).keys())
            text = parked.read_text()
            names.update(re.findall(r"\[profile\.[a-z-]+\.package\.([A-Za-z0-9_-]+)\]", text))
    return names


def rename_map() -> dict[str, str]:
    out: dict[str, str] = {}
    for name in crate_names():
        new = to_new(name)
        if new and new != name:
            out[name] = new
        old = to_old(name)
        if old and old != name:
            out[old] = name
    return out


def tracked_text_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    files = []
    for rel in out.decode().split("\0"):
        if not rel or rel in SKIP_FILES or rel.endswith(SKIP_SUFFIXES):
            continue
        p = ROOT / rel
        if p.is_file():
            files.append(p)
    return files


def build_rules(mapping: dict[str, str]) -> list[tuple[re.Pattern, str]]:
    rules: list[tuple[re.Pattern, str]] = []
    # longest first so `filmcraft-tts-text` wins over `filmcraft-tts`
    for old in sorted(mapping, key=len, reverse=True):
        new = mapping[old]
        if old == APP_OLD:
            # the bare word is also a file-format id, a log target and an English word: only the
            # crate contexts are renamed
            rules.append((re.compile(r"(-p|--package)(\s+)filmcraft(?![A-Za-z0-9_.-])"), rf"\1\2{new}"))
            rules.append((re.compile(r'^(name\s*=\s*)"filmcraft"$', re.M), rf'\1"{new}"'))
            rules.append((re.compile(r"^filmcraft(\s*=\s*\{)", re.M), rf"{new}\1"))
            rules.append((re.compile(r"^filmcraft(\.workspace\s*=)", re.M), rf"{new}\1"))
            continue
        rules.append((re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(old)}(?![A-Za-z0-9-])"), new))
        old_s, new_s = old.replace("-", "_"), new.replace("-", "_")
        rules.append((re.compile(rf"(?<![A-Za-z0-9_]){re.escape(old_s)}(?![A-Za-z0-9_])"), new_s))
    for old_dir, new_dir in DIR_MOVES:
        rules.append((re.compile(rf"{re.escape(old_dir)}(?![A-Za-z0-9_-])"), new_dir))
    return rules


def apply(text: str, rules: list[tuple[re.Pattern, str]]) -> str:
    for pat, repl in rules:
        text = pat.sub(repl, text)
    return text


def move_dirs(check: bool) -> list[str]:
    moved = []
    for old, new in DIR_MOVES:
        src, dst = ROOT / old, ROOT / new
        if not src.exists():
            continue
        if dst.exists():
            raise SystemExit(f"both {old} and {new} exist; merge them by hand")
        moved.append(f"{old} -> {new}")
        if not check:
            subprocess.run(["git", "mv", old, new], cwd=ROOT, check=True)
    return moved


def refresh_lock() -> None:
    r = subprocess.run(["cargo", "update", "--workspace", "--offline"], cwd=ROOT)
    if r.returncode != 0:
        print("cargo update --workspace --offline failed; run it by hand once the registry cache is warm", file=sys.stderr)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    mapping = rename_map()
    if not mapping:
        print("rename_crates: no crate names to rename")
        return 0
    rules = build_rules(mapping)
    moved = move_dirs(check)
    changed: list[Path] = []
    for path in tracked_text_files():
        try:
            before = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        after = apply(before, rules)
        if after != before:
            changed.append(path.relative_to(ROOT))
            if not check:
                path.write_text(after, encoding="utf-8")
    verb = "would rename" if check else "renamed"
    for m in moved:
        print(f"{verb} dir {m}")
    for p in changed:
        print(f"{verb} {p}")
    print(f"rename_crates: {len(mapping)} crate name(s) known, {len(changed)} file(s) {verb}, {len(moved)} dir(s)")
    if check:
        return 1 if (changed or moved) else 0
    if changed and "--no-lock" not in argv:
        refresh_lock()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
