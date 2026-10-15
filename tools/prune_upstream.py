#!/usr/bin/env python3
"""Remove upstream repository furniture from the effectcraft subtree.

crafts/effectcraft is storytold/effectcraft as a git subtree. Only its crates, the assets and
documents those crates compile in, and the attribution files are part of Redrob Film; the rest
(upstream README, roadmap, packaging, CI, apps, xtask, contributor lists, agent instructions) is
upstream's repository furniture and is removed so no user or contributor meets it here.

KEPT: crates/, assets/fonts/ (compiled into the UI), extensions/ and examples/plugins/ (compiled
into the script engine and its tests), docs/preferences.md and docs/agents.md (include_str! in
tests), LICENSE-APACHE, LICENSE-MIT, NOTICE, ATTRIBUTION.md (the licences require them),
clippy.toml and rustfmt.toml (nearest-config lookup for the subtree crates), Cargo.upstream.toml
(read by tools/merge_effectcraft.py).

Idempotent; tools/merge_effectcraft.py calls it, so it runs again after every subtree pull:

    python3 tools/prune_upstream.py          # delete, print what went
    python3 tools/prune_upstream.py --check  # exit 1 if anything is left to delete
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBTREE = ROOT / "crafts" / "effectcraft"

# Whole directories that nothing in our build references.
REMOVE_DIRS = [
    ".cargo",
    ".github",
    "apps",
    "assets/app-icon",
    "contributors",
    "packaging",
    "xtask",
]
# Files at the subtree root.
REMOVE_FILES = [
    ".gitignore",
    ".mcp.json",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "Cargo.lock",
    "README.md",
    "ROADMAP.md",
]
# Directories pruned down to the entries the crates compile in.
KEEP_WITHIN = {
    "docs": {"preferences.md", "agents.md"},
    "examples": {"plugins"},
}


def targets() -> list[Path]:
    out: list[Path] = []
    for rel in REMOVE_DIRS + REMOVE_FILES:
        p = SUBTREE / rel
        if p.exists() or p.is_symlink():
            out.append(p)
    for rel, keep in KEEP_WITHIN.items():
        d = SUBTREE / rel
        if d.is_dir():
            out.extend(p for p in sorted(d.iterdir()) if p.name not in keep)
    return out


def git_tracked(path: Path) -> bool:
    r = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], cwd=ROOT, capture_output=True)
    return r.returncode == 0


def remove(path: Path) -> None:
    rel = path.relative_to(ROOT)
    if git_tracked(path):
        subprocess.run(["git", "rm", "-r", "-q", "--", str(rel)], cwd=ROOT, check=True)
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()
    print(f"removed {rel}")


def main(argv: list[str]) -> int:
    check = "--check" in argv
    found = targets()
    if check:
        for p in found:
            print(f"would remove {p.relative_to(ROOT)}")
        return 1 if found else 0
    for p in found:
        remove(p)
    print(f"prune_upstream: {len(found)} entr{'y' if len(found) == 1 else 'ies'} removed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
