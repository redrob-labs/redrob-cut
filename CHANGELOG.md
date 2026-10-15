# Changelog

## Unreleased

### Changed

- Upstream identifiers are gone from everything a user or contributor meets. Crates are
  `redrob-film-*` (`redrob-film-app` is the desktop shell, its binary still `redrob-film`) and
  `redrob-effects-*`; `tools/rename_crates.py` performs the rename idempotently and
  `tools/merge_effectcraft.py` runs it, together with the new `tools/prune_upstream.py` (drops the
  effectcraft subtree's README, packaging, CI, apps, xtask and other repository furniture), after
  every subtree pull.
- Projects save as `.rfilm` (effects sidecar `.rfilm.effects.json`); effects projects as `.rfx`,
  XML copies as `.rfxx` with root `<RedrobEffectsProject>`. MIME types are
  `application/x-redrob-film` / `application/x-redrob-effects` (declared for macOS and Linux);
  MCP resources are `redrob-film://…` and `redrob-effects://…`; environment variables are
  `REDROB_FILM_*` / `REDROB_EFFECTS_*`; MKV files carry `WritingApp` `redrob-film`.
- Old files and settings keep working: `.fcproj`, `.ecproj`, `.ecprojx`, `<EffectCraftProject>`
  documents, template archives with `project.ecproj`, pre-rename recovery snapshots and auto-saves,
  the old MCP URIs, and `FILMCRAFT_DATA_DIR`, `FILMCRAFT_CONFIG_DIR`, `FILMCRAFT_CONTROL_PORT`,
  `FILMCRAFT_CPU_COMPOSITE`, `EFFECTCRAFT_CONFIG_DIR`, `EFFECTCRAFT_FONT_DIRS` are read as
  fallbacks. Nothing writes the old spelling.
- `scripts/check_brand.py` now fails on any upstream crate name, extension, env prefix, URI scheme,
  MIME type or XML root outside the attribution files and the `// legacy:`-marked read paths.
