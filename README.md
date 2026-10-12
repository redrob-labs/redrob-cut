# Redrob Cut

Redrob Cut is an agentic video editor: describe the cut and let the agent make it.

한국어: [README.ko.md](./README.ko.md)

> **Fork notice.** This repository is a hard fork of [storytold/filmcraft](https://github.com/storytold/filmcraft)
> at tag `v0.6.0`. Where it was cut, what it does not own and how upstream is absorbed are in
> [UPSTREAM.md](./UPSTREAM.md); the machine-readable pin is [`upstream-base.json`](./upstream-base.json).
> Upstream's copyright is retained in [NOTICE](./NOTICE) with ours added below it. Upstream's ArtCraft
> marks are removed; the Redrob marks in `assets/brand/` are Redrob's trademarks.

## What it is

- A non-linear video editor in pure Rust, with its own H.264, HEVC, ProRes and AAC codecs and a GPU
  compositor that works in linear light.
- Every action in the app is a command. The UI, the CLI, the JSON control channel and the MCP server
  call the same commands, so an agent cuts, trims, grades, mixes and exports exactly as a person does.
- **Redrob Code is built in.** The Agent panel is a chat with Redrob Code, which edits the open project
  through those commands. Its model calls are billed to the Redrob workspace you connect (Help ▸
  Connect to Redrob…); editing itself is free and never asks for an account. Other agents connect
  through `redrob-cut-cli mcp` ([docs/agents.md](./docs/agents.md)).
- Native on macOS, Windows and Linux; WebAssembly in the browser.

## Getting started

```sh
cargo run --release -p filmcraft                     # the desktop app (redrob-cut), demo project
cargo run --release -p filmcraft -- --control 9876   # with the JSON-lines control server
cargo run --release -p filmcraft-cli -- commands     # every engine command (redrob-cut-cli)
cargo run --release -p filmcraft-cli -- mcp          # MCP server (headless)
```

Cargo packages keep upstream's `filmcraft*` names so upstream syncs merge cleanly; the executables,
app id (`ai.redrob.cut`), installers and everything a person sees are Redrob Cut's.

## Branches and contributing

- Default branch `develop`, release branch `main`. Branch names follow the `feat/ fix/ chore/ docs/
  test/ refactor/ perf/ sync/ hotfix/ release/` prefixes, checked by `.github/workflows/gitflow.yml`.
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
