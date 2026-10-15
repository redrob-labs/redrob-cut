#!/usr/bin/env python3
"""Brand gate: Redrob Film shows Redrob's name and marks, and nothing of upstream's.

1. No file under a proprietary upstream prefix (upstream-base.json `proprietaryPrefixes`).
2. The brand sources in assets/brand/ match assets/brand/SHA256SUMS byte for byte, and every app
   icon is one the brand script makes (no stray upstream icon left behind).
3. No upstream product name, company, app id or community link on a user-facing surface: string
   literals in the UI, the apps and the engine's messages, the translation catalogs, the packaging
   and the CI that builds it. Comments are not surfaces. What is kept on purpose (stored in files,
   or read back as an identifier) is listed in KEEP and in UPSTREAM.md.

    python3 scripts/check_brand.py
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# The product names as people read them. Lowercase `filmcraft` is upstream's crate and identifier
# namespace (thread names, file-format ids, log targets) and stays; the installable names are
# checked through the packaging patterns below.
FORBIDDEN = re.compile(
    r"FilmCraft|Filmcraft|ArtCraft|EffectCraft|artcraft-mark|getartcraft|storytold/effectcraft|[Ss]toryteller|Learning Machines|(?i:discord)|(?:Exec|TryExec)=filmcraft|<binary>filmcraft|^command: filmcraft"
    # the product's former name (Redrob Cut, renamed to Redrob Film)
    r"|Redrob Cut|redrob-cut|redrob_cut|ai\.redrob\.cut|REDROB_CUT|RedrobCut"
)
SURFACES = (
    "crates/ui-egui/src/", "apps/filmcraft/src/", "apps/filmcraft-cli/src/",
    "crates/engine/src/", "crates/automation/src/", "packaging/", ".github/workflows/",
    "crafts/effectcraft/crates/",
)
# Kept on purpose: written into or read back from files, so changing them breaks existing projects
# and interchange round trips. UPSTREAM.md lists them.
KEEP = re.compile(
    r"GPU Acceleration \(wgpu\)|Software Only \(CPU\)|CreatorTool|\"generator\"|application/x-filmcraft"
    r"|FILMCRAFT_|filmcraft_|filmcraft-(target|install-|sign-|signing|logging-|web|speech|engine|ui-egui)"
    r"|-p filmcraft|apps/filmcraft|filmcraft\*=|name: filmcraft$|/run/build/filmcraft/|FilmcraftApp|Filmcraft(Icon|Files|App|Exe|Cli|CliExe|Output)\b"
    # internal plist keys; the copyright credit upstream's licence requires; a negative test
    r"|FilmCraft(Version|BuildCommit)\b|the (FilmCraft|EffectCraft) contributors|desktop_file_exec_is_ours|EFFECTCRAFT_|effectcraft_|effectcraft-|EffectCraftProject"
)
COMMENT = re.compile(r"^\s*(//|#|<!--|\*|/\*|;|REM\b)")


def files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    return [f for f in out if (ROOT / f).exists()]


def main() -> int:
    errors = []
    base = json.loads((ROOT / "upstream-base.json").read_text())
    tracked = files()
    for prefix in base.get("proprietaryPrefixes", []):
        for f in tracked:
            if f.startswith(prefix):
                errors.append(f"{f}: under the proprietary upstream prefix {prefix} (must be removed)")

    sums = (ROOT / "assets/brand/SHA256SUMS").read_text().split("\n")
    pinned = {}
    for line in filter(None, sums):
        digest, name = line.split(None, 1)
        pinned[name.strip()] = digest
    for name, digest in pinned.items():
        p = ROOT / "assets/brand" / name
        if not p.exists():
            errors.append(f"assets/brand/{name}: pinned but missing")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            errors.append(f"assets/brand/{name}: differs from SHA256SUMS (brand files are never edited)")
    for f in tracked:
        if f.startswith("assets/app-icon/") and not f.endswith((".attribution", "LICENSE.txt", "README.md")):
            name = pathlib.Path(f).name
            if not (name.startswith("redrob-film") or name.startswith("ai.redrob.film")):
                errors.append(f"{f}: not an icon packaging/brand-assets.sh makes")

    for f in tracked:
        if not f.startswith(SURFACES) or f.endswith((".png", ".tiff", ".ico", ".icns", ".DS_Store", ".attribution")):
            continue
        if f.startswith("packaging/macos/dmg/background"):
            continue  # outlined paths and the embedded lockup, not text
        try:
            text = (ROOT / f).read_text()
        except UnicodeDecodeError:
            continue
        tsv = f.endswith(".tsv")
        for n, line in enumerate(text.split("\n"), 1):
            if not FORBIDDEN.search(line) or KEEP.search(line) or COMMENT.match(line):
                continue
            if f.endswith(".rs"):
                # only string literals are surfaces in Rust; strip trailing comments first
                code = line.split("//", 1)[0] if '"' not in line.split("//", 1)[0][-1:] else line
                if not any(FORBIDDEN.search(s) for s in re.findall(r'"((?:[^"\\]|\\.)*)"', code)):
                    continue
            if tsv and line.startswith("#"):
                continue
            errors.append(f"{f}:{n}: upstream brand on a user-facing surface: {line.strip()[:120]}")

    if errors:
        print("\n".join(errors))
        print(f"brand: {len(errors)} problem(s)", file=sys.stderr)
        return 1
    print(f"brand: ok ({len(pinned)} pinned brand sources)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
