#!/usr/bin/env python3
"""Write the `<file>.attribution` sidecars for the Redrob brand files (`cargo xtask assets`).

Run by packaging/brand-assets.sh after it derives the icons. The sources in assets/brand/ are
verbatim design-system files; everything under assets/app-icon/ and the web favicons is derived
from them by that script. Rows for ATTRIBUTION.md are printed with --rows.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ADDED = "2026-10-12 for Janghoon Lee (Redrob)"
LICENSE = "Redrob trademark; not covered by the repository's MIT OR Apache-2.0 licence (assets/brand/README.md)"
AUTHOR = "Redrob (McKinley Rice, Inc.)"

SOURCES = {
    "favicon-16x16.png": "Redrob favicon, 16 px tile",
    "favicon-32x32.png": "Redrob favicon, 32 px tile",
    "favicon-48x48.png": "Redrob favicon, 48 px tile",
    "favicon-64x64.png": "Redrob favicon, 64 px tile",
    "favicon.ico": "Redrob favicon, .ico (16, 32, 48)",
    "favicon.svg": "Redrob favicon, vector tile",
    "icon-192.png": "Redrob app icon, 192 px tile",
    "icon-512.png": "Redrob app icon, 512 px tile",
    "redrob-logo-primary.png": "Redrob primary lockup, for light grounds",
    "redrob-logo-primary-white.png": "Redrob primary lockup, white wordmark for dark grounds",
}
DS_PATH = {n: ("assets/Logos/" if n.startswith("redrob-logo") else "assets/Favicons/") + n for n in SOURCES}


def derived():
    out = []
    a = ROOT / "assets/app-icon"
    for p in sorted(a.rglob("*")):
        if p.is_file() and p.name not in ("LICENSE.txt", "README.md") and not p.name.endswith(".attribution"):
            out.append((p, f"Redrob Cut app icon ({p.relative_to(a)}), derived from the Redrob tile"))
    w = ROOT / "apps/filmcraft-web/web"
    out.append((w / "favicon.png", "Redrob Cut web favicon (the 64 px Redrob tile)"))
    out.append((w / "favicon.svg", "Redrob Cut web favicon (the vector Redrob tile)"))
    return out


def sidecar(path: pathlib.Path, title: str, source: str, notes: str) -> None:
    text = (
        f"asset:        {path.name}\n"
        f"title:        {title}\n"
        f"author:       {AUTHOR}\n"
        f"source:       {source}\n"
        f"license:      {LICENSE}\n"
        f"added:        {ADDED}\n"
        f"notes:        {notes}\n"
    )
    pathlib.Path(str(path) + ".attribution").write_text(text)


def main() -> None:
    rows = []
    for name, title in SOURCES.items():
        p = ROOT / "assets/brand" / name
        sidecar(p, title, f"Redrob design system, {DS_PATH[name]}, copied verbatim", "Pinned by assets/brand/SHA256SUMS. Never redrawn or recolored.")
        rows.append((p, title))
    for p, title in derived():
        sidecar(p, title, "derived by packaging/brand-assets.sh from assets/brand/ (copied as is, or resized down)", "Regenerate with packaging/brand-assets.sh; do not edit by hand.")
        rows.append((p, title))
    if "--rows" in sys.argv:
        for p, title in rows:
            print(f"| `{p.relative_to(ROOT)}` | {AUTHOR} | {title} | Redrob trademark (`assets/brand/README.md`) |")


if __name__ == "__main__":
    main()
