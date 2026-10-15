# Upstream: storytold/filmcraft

This repository is a **hard fork** of [storytold/filmcraft](https://github.com/storytold/filmcraft),
carrying upstream's full history up to one of its release tags. It is not a patch stack and it is not a
mirror.

한국어: [UPSTREAM.ko.md](./UPSTREAM.ko.md)

## Where the fork was cut

| | |
|---|---|
| Upstream tag | `v0.6.0` |
| Upstream commit | `2ff3f5e` — 2026-10-10, `Release prep: 0.6.0 and a Linux riscv64 release build (#830)` |
| Upstream default branch | `main` |
| Our long-lived branches | `develop` (default), `main` (release) |

The machine-readable record is [`upstream-base.json`](./upstream-base.json). Because the history is
shared, `git merge-base develop upstream/main` is real, and an upstream sync is an ordinary three-way
merge, not a replay.

## Why a merged tree, not a patch stack

What this fork changes is not surgical: the brand is replaced, a Redrob account layer goes in, our own
agent engine becomes the default, and the UI theme moves to the Redrob design system. That is dozens of
files on the first pass and grows from there. A patch stack is the right shape when the diff is a handful
of files that must apply to a pristine checkout; here it would replay a growing collision surface on every
bump for no gain.

## What this fork does not own

Upstream's `NOTICE` and its `docs/brand/LICENSE-brand.txt` state that the ArtCraft name, wordmark and
mark under `docs/brand/` are trademarks of the ArtCraft Team, **not** covered by MIT OR Apache-2.0, and that
forks and modified versions must remove them. They are removed. `upstream-base.json` keeps the prefix under
`proprietaryPrefixes` with `proprietaryReplaced: true`, so `scripts/check_upstream_boundary.py` fails if any
of those files is ever byte-identical to upstream's again, and `scripts/check_brand.py` fails if any file
under the prefix comes back at all (an upstream sync that re-adds them must delete them in the merge).

The FilmCraft app icon was original artwork licensed like the code; it was replaced for product identity.
Every icon is now derived from the Redrob design system's files in `assets/brand/` (pinned by
`SHA256SUMS`) by `packaging/brand-assets.sh`.

### Renamed, and kept on purpose

What a person sees or installs is Redrob Film's: the name, app id `ai.redrob.film`, the executables
`redrob-film` and `redrob-film-cli`, installers, data folders (`Redrob Film` / `redrob-film`), log files, the
MCP server name, links, icons, the About and Home lockup, and the brand colours (`redrob_tokens`,
generated from redrob-ui). `scripts/check_brand.py` keeps it that way.

Renamed to Redrob's, with the old spelling still READ so existing files and set-ups keep working
(every such read path is marked `// legacy:` in the code; `scripts/check_brand.py` fails on an
unmarked leftover):

- Crate names: `filmcraft` → `redrob-film-app`, `filmcraft-*` → `redrob-film-*`, `effectcraft-*` →
  `redrob-effects-*` (and the `redrob_film_*` / `redrob_effects_*` module paths and log targets).
  `tools/rename_crates.py` does this idempotently and runs from `tools/merge_effectcraft.py`, so an
  upstream sync is followed by the rename rather than conflicting with it.
- Project files: `.fcproj` → `.rfilm` (the effects sidecar is `<name>.rfilm.effects.json`), effects
  projects `.ecproj` → `.rfx` and XML copies `.ecprojx` → `.rfxx`, XML root `<EffectCraftProject>` →
  `<RedrobEffectsProject>`. Old files open from the command line, the open dialogs, recents, the media
  browser, watch folders, import, templates and recovery; auto-save rotation and schema backups keep
  rotating pre-rename files. Nothing writes the old spelling.
- MIME types `application/x-redrob-film` and `application/x-redrob-effects` (macOS UTType, Linux
  shared-mime-info, .desktop); the old extensions are still declared as globs.
- MCP resource URIs `redrob-film://document|commands` and `redrob-effects://…`; the old URIs still read.
- Environment variables `REDROB_FILM_*` / `REDROB_EFFECTS_*`. The user-facing ones fall back to the
  old name: `FILMCRAFT_DATA_DIR`, `FILMCRAFT_CONFIG_DIR`, `FILMCRAFT_CONTROL_PORT`,
  `FILMCRAFT_CPU_COMPOSITE`, `EFFECTCRAFT_CONFIG_DIR`, `EFFECTCRAFT_FONT_DIRS`. Test-only ones
  (`*_BLESS`, `*_UI_SNAPSHOT_DIR`, `*_FUZZ_*`, model paths) were simply renamed.
- MKV `WritingApp` is `redrob-film`.

Kept as upstream's, because they are stored in files and compared on read-back:

- The `filmcraft.*` format ids in project, preset and template files (`"format": "filmcraft.project"`),
  the `filmcraft` OTIO metadata namespace, the renderer names stored in project settings, the AAF
  tag names and the XMP `CreatorTool` marker that interchange reads back. Thread names and temp-file
  prefixes in the lower crates also keep the short `filmcraft-` word; they are not crate names.
- Built-in decoder names (`FilmCraft H.264` and so on), test data and code comments in the lower-layer
  crates. The name the app writes into exported files (MP4 encoder tag, MXF/AAF/OMF identification,
  caption and LUT headers, the project `generator`) and the messages people read are Redrob Film's.
- Upstream's own documentation under `docs/` (except `docs/agents.md`), which describes upstream.

Upstream's `release.yml` was removed rather than kept: it called a reusable workflow in upstream's own
`craft-common-actions` repository with upstream's signing secrets. Our release workflow is written against
this organisation's secrets.

## Absorbing upstream

Follow upstream **tags**. Sync branches are `sync/upstream-<tag>`, opened as a pull request into `develop`,
and **merged as a merge commit, never a squash** — a squash destroys the merge base and the next sync
replays work already taken.

```sh
git fetch upstream --tags
git checkout -b sync/upstream-vX.Y.Z develop
git merge vX.Y.Z          # resolve conflicts by hand; keep ours where we renamed, take theirs around it
cargo build --release && cargo test && python3 scripts/check_upstream_boundary.py
```

Then update `base`, `baseTag`, `baseDate`, `baseSubject` and `lastSyncedUpstream` in
`upstream-base.json` in the same pull request.

## Attribution

Upstream's copyright line in [`NOTICE`](./NOTICE) is retained verbatim, with ours added below it. Both
license texts ([`LICENSE-MIT`](./LICENSE-MIT), [`LICENSE-APACHE`](./LICENSE-APACHE)) are unchanged.
Per-asset attribution continues in [`ATTRIBUTION.md`](./ATTRIBUTION.md).

## effectcraft (Effects mode)

`crafts/effectcraft/` is [storytold/effectcraft](https://github.com/storytold/effectcraft) as a git
subtree, pinned at `0311bdc34d0dc10c2d18ff7875b4f52d483e5e27` (2026-10-15), MIT OR Apache-2.0; its
LICENSE-* and NOTICE stay intact under that directory. Its own `Cargo.toml` is parked as
`Cargo.upstream.toml`; `tools/merge_effectcraft.py` first runs `tools/prune_upstream.py` (deletes
upstream's repository furniture: README, ROADMAP, CONTRIBUTING, AGENTS/CLAUDE, contributors, packaging,
.github, apps, xtask, app icons and all docs/examples the crates do not compile in) and
`tools/rename_crates.py` (`effectcraft-*` → `redrob-effects-*`, its `filmcraft-*` dependencies →
`redrob-film-*`), then folds the crates and dependencies into this workspace (the renamed
`redrob-film-*` git dependencies become this repository's crates). Update:

```bash
git subtree pull --prefix crafts/effectcraft https://github.com/storytold/effectcraft.git <sha> --squash
python3 tools/merge_effectcraft.py      # prune + rename + merge; refreshes Cargo.lock offline
python3 tools/rebrand_crafts.py
python3 scripts/check_brand.py          # upstream names and identifiers all gone?
```

A pull brings back upstream's `.ecproj` spelling in new code; the brand check names each line, and the
fix is the same substitution (`.ecproj` → `.rfx`, `.ecprojx` → `.rfxx`) with a `// legacy:` marker on
any read path that must keep accepting the old one.
