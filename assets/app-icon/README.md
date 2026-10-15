# Redrob Film app icon

The Redrob tile: a white symbol on a Redrob Blue (`#2B52FF`) tile, from the Redrob design system.
Every file here is derived from the pinned sources in [`../brand/`](../brand/README.md) by
`packaging/brand-assets.sh` and nothing else; do not edit them by hand.

Redrob Film has no product glyph of its own in the design system yet, so it carries the Redrob tile.
When a Cut glyph is added to the design system's `assets/Products/`, replace the sources in
`assets/brand/`, update `SHA256SUMS` and rerun the script.

## Files

| File | What |
|---|---|
| `hicolor/<size>/apps/ai.redrob.film.png`, `hicolor/scalable/apps/ai.redrob.film.svg` | Linux icon theme, used by `packaging/linux/ai.redrob.film.desktop` |
| `redrob-film-256.png` | runtime window icon on Windows and Linux (embedded by `apps/filmcraft/src/main.rs`) |
| `redrob-film-512.png` | runtime Dock icon on macOS |
| `redrob-film.icns` | macOS bundle icon (`CFBundleIconFile`) |
| `redrob-film.ico` | Windows icon, 16-256 px (embedded in the exe by `apps/filmcraft/build.rs`) |

The web app's `apps/filmcraft-web/web/favicon.png` and `favicon.svg` are the design system's own
64 px and vector tiles.

## Rules

Design system `10-logo.md` and `assets/Favicons/README.md`: one design, no dark-mode variant;
never redrawn, recolored, re-proportioned, given a shadow, border, margin or second radius. Each
size is the design system's own where it ships one; any other size is the next larger tile resized
down, never up.

Licence: [LICENSE.txt](LICENSE.txt).
