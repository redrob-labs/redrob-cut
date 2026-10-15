#!/usr/bin/env python3
"""Rebrand upstream product names on Redrob Film's user-visible surfaces.

Runs over the UI crate (including the i18n catalogs), the desktop app, the engine and the
automation crate. Only STRING LITERAL contents in Rust and the message columns of the
translation catalogs are touched: identifiers such as `FilmcraftApp` or `filmcraft_engine`,
crate names, `FILMCRAFT_*` environment variables, the `.fcproj` format and the MIME type keep
their spelling and are never matched. Values that are written into project files and read back
(the renderer names, the XMP CreatorTool) are kept on purpose; they are listed in KEEP here and
in scripts/check_brand.py. Re-run after every upstream sync.

Upstream attribution is unaffected: NOTICE, ATTRIBUTION.md, LICENSE-*, UPSTREAM*.md and
upstream-base.json are outside the scanned trees and keep the upstream copyright lines
verbatim, as the MIT and Apache-2.0 licences require.

    python3 tools/rebrand_crafts.py          # rewrite in place, print the files changed
    python3 tools/rebrand_crafts.py --check  # exit 1 if anything would change
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN = ["crates/ui-egui/src", "apps/filmcraft/src", "crates/engine", "crates/automation", "crafts/effectcraft/crates"]

HOME = "https://redrob.ai"
REPO = "https://github.com/redrob-labs/redrob-film"
ISSUES = REPO + "/issues"

# Ordered: URLs first (they contain product names), then names. There is no Discord and no
# Discussions for Redrob Film: community links point at the issue tracker.
REPLACEMENTS = [
    (r"https?://(www\.)?getartcraft\.com[^\s\"'<>)]*", HOME),
    (r"https?://discord\.gg/[^\s\"'<>)]*", ISSUES),
    (r"https?://discord\.com/[^\s\"'<>)]*", ISSUES),
    (r"https?://github\.com/storytold/filmcraft/(issues|discussions)[^\s\"'<>)]*", ISSUES),
    (r"https?://github\.com/storytold/filmcraft[^\s\"'<>)]*", REPO),
    (r"Join the ArtCraft Discord", "Redrob community"),
    (r"Join the ArtCraft community", "Redrob community"),
    (r"ArtCraft Discord", "Redrob community"),
    (r"More ArtCraft apps", "More Redrob apps"),
    (r"ArtCraft App Page", "Redrob apps"),
    (r"ArtCraft Website", "Redrob website"),
    (r"Part of the ArtCraft suite of open creative tools\.", "Part of the Redrob suite of agentic apps."),
    (r"ArtCraft Team", "Redrob"),
    (r"ArtCraft", "Redrob"),
    (r"getartcraft\.com", "redrob.ai"),
    (r"https?://github\.com/storytold/effectcraft[^\s\"')]*", "https://github.com/redrob-labs/redrob-film"),
    (r"FilmCraft", "Redrob Film"),
    (r"EffectCraft", "Redrob Film"),
]

# Stored in files or compared on read-back; changing them breaks existing projects.
KEEP = re.compile(
    r"GPU Acceleration \(wgpu\)|Software Only \(CPU\)|CreatorTool|FILMCRAFT_|filmcraft_|filmcraft-"
    r"|FilmCraft(Version|BuildCommit)\b|the FilmCraft contributors|the EffectCraft contributors|EFFECTCRAFT_|effectcraft_|effectcraft-|EffectCraftProject"
)

STRING_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def rebrand_text(text: str) -> str:
    if KEEP.search(text):
        return text
    for pattern, repl in REPLACEMENTS:
        text = re.sub(pattern, repl, text)
    return text


def rebrand_rust(source: str) -> str:
    def sub(m: re.Match) -> str:
        return '"' + rebrand_text(m.group(1)) + '"'

    source = STRING_RE.sub(sub, source)
    # A URL constant interpolated by format!() or concat!() loses its placeholder once the
    # host changes; collapse the leftovers the rewrite produces.
    source = source.replace(f'format!("{REPO}")', f'String::from("{REPO}")')
    source = source.replace(f'format!("{ISSUES}")', f'String::from("{ISSUES}")')
    source = source.replace(f'format!("{HOME}")', f'String::from("{HOME}")')
    return source


def rebrand_tsv(text: str) -> str:
    out = []
    for line in text.split("\n"):
        if line.startswith("#") or not line.strip():
            out.append(line)
            continue
        key, sep, rest = line.partition("\t")
        out.append(key + sep + rebrand_text(rest) if sep else rebrand_text(line))
    return "\n".join(out)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    changed: list[Path] = []
    for rel in SCAN:
        for path in sorted((ROOT / rel).rglob("*")):
            if not path.is_file():
                continue
            if path.suffix == ".rs":
                before = path.read_text(encoding="utf-8")
                after = rebrand_rust(before)
            elif path.suffix == ".tsv":
                before = path.read_text(encoding="utf-8")
                after = rebrand_tsv(before)
            else:
                continue
            if after != before:
                changed.append(path.relative_to(ROOT))
                if not check:
                    path.write_text(after, encoding="utf-8")
    for p in changed:
        print(f"{'would change' if check else 'rebranded'} {p}")
    print(f"{len(changed)} file(s) {'would change' if check else 'changed'}")
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
