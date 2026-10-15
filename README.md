# Redrob Film

Redrob Film is an agentic video editor: describe the cut and let the agent make it. One window, two
modes: **Edit** (the timeline NLE) and **Effects** (motion graphics and compositing), with a shared
AI dock beside whichever one is active.

한국어: [README.ko.md](./README.ko.md)

> **Fork notice.** This repository is a hard fork of [storytold/filmcraft](https://github.com/storytold/filmcraft)
> at tag `v0.6.0`. Where it was cut, what it does not own and how upstream is absorbed are in
> [UPSTREAM.md](./UPSTREAM.md); the machine-readable pin is [`upstream-base.json`](./upstream-base.json).
> Upstream's copyright is retained in [NOTICE](./NOTICE) with ours added below it. Upstream's ArtCraft
> marks are removed; the Redrob marks in `assets/brand/` are Redrob's trademarks.

## What it is

- Edit mode: a non-linear video editor in pure Rust, with its own H.264, HEVC, ProRes and AAC codecs and a GPU
  compositor that works in linear light.
- Effects mode: motion graphics and compositing (layers, keyframes, effects, expressions, text) in the
  same window and the same project bundle.
- Mode menu hand-offs: **Send Selection to Effects** turns the selected clips (or the in/out range, or
  the whole sequence) into a new composition; **Place Composition on Timeline** puts the active
  composition on the timeline as a clip rendered live by the Effects renderer. Edit / Effects switch
  with the top-bar buttons or their shortcuts.
- Every action in the app is a command. The UI, the CLI, the JSON control channel and the MCP server
  call the same commands, so an agent cuts, trims, grades, mixes and exports exactly as a person does.
- **Redrob Code is built in.** The AI dock (the AI button in the top bar, Mode ▸ Show AI, Ctrl+Shift+A)
  is a chat with Redrob Code, which edits the open project through those commands in both modes. Its
  model calls are billed to the Redrob workspace you connect (Help ▸ Connect to Redrob…); editing
  itself is free and never asks for an account. Other agents connect through `redrob-film-cli mcp`
  ([docs/agents.md](./docs/agents.md)).
- Native on macOS, Windows and Linux.

## Download

The easiest way is [Redrob Launcher](https://github.com/redrob-labs/redrob-launcher), which installs
Redrob Film, keeps it up to date and signs every Redrob app in with one workspace. Direct downloads
are on the [releases page](https://github.com/redrob-labs/redrob-film/releases); a copy installed by
hand checks for updates itself (Updates menu in the top bar; `REDROB_FILM_NO_UPDATE_CHECK=1` turns
the automatic check off).

| Platform | Download |
|---|---|
| Linux x86_64 | `redrob-film-<version>-linux-x86_64.tar.gz` (run `./install.sh`, no sudo needed) or `redrob-film-<version>-linux-x86_64.deb` |
| macOS (Apple silicon and Intel) | `redrob-film-<version>-macos-universal.dmg` |
| Windows x64 | `redrob-film-<version>-windows-x64.msi` or `redrob-film-<version>-windows-x64-portable.zip` |

`SHA256SUMS.txt` on the release lists every file. Details: [docs/releasing.md](./docs/releasing.md).

## Getting started

```sh
cargo run --release -p redrob-film-app                     # the desktop app (redrob-film), demo project
cargo run --release -p redrob-film-app -- --control 9876   # with the JSON-lines control server
cargo run --release -p redrob-film-cli -- commands     # every engine command (redrob-film-cli)
cargo run --release -p redrob-film-cli -- mcp          # MCP server (headless)
```

Cargo packages keep upstream's `filmcraft*` names so upstream syncs merge cleanly; the executables,
app id (`ai.redrob.film`), installers and everything a person sees are Redrob Film's.

## Branches and contributing

- Default branch `develop`, release branch `main`. Branch names follow the `feat/ fix/ chore/ docs/
  test/ refactor/ perf/ sync/ hotfix/ release/` prefixes, checked by the shared redrob-labs gitflow workflow (one type list for every repository: `feat fix chore docs test refactor perf ci build sync hotfix release`).
- Upstream syncs land on `sync/upstream-<tag>` branches and merge with a merge commit only.
- Organisation conventions: CONTRIBUTING.md and FORKS.md in [redrob-labs/.github](https://github.com/redrob-labs/.github).
- Gates: `python3 scripts/check_upstream_boundary.py`, `scripts/check_no_upstream_services.py`,
  `scripts/check_brand.py`, and `cargo xtask ci`.

## License

MIT or Apache-2.0, at your option ([LICENSE-MIT](./LICENSE-MIT), [LICENSE-APACHE](./LICENSE-APACHE)).
Copyright notices are in [NOTICE](./NOTICE); ours is added below upstream's:

```
Copyright (c) 2026 ArtCraft Team and the FilmCraft contributors.
Copyright (c) 2026-present Janghoon Lee (Redrob) and contributors
```

The Redrob name and marks are not covered by that license ([assets/brand/README.md](./assets/brand/README.md)).
Per-asset attribution is in [ATTRIBUTION.md](./ATTRIBUTION.md).
