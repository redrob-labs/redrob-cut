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

Upstream's `NOTICE` and [`docs/brand/LICENSE-brand.txt`](./docs/brand/LICENSE-brand.txt) state that the
ArtCraft name, wordmark and mark under `docs/brand/` are trademarks of the ArtCraft Team, **not** covered
by MIT OR Apache-2.0, and that forks and modified versions must remove them. `upstream-base.json` lists the
prefix under `proprietaryPrefixes`; `proprietaryReplaced` flips to `true` when the brand pass replaces every
file there with Redrob design-system sources, after which `scripts/check_upstream_boundary.py` fails if any
file is ever byte-identical to upstream's again.

The FilmCraft app icon under `assets/app-icon/` is original artwork licensed like the rest of the code
(see its `LICENSE.txt`); it is replaced in the brand pass for product identity, not for licensing.

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
