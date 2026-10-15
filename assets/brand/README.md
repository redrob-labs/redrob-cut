# Brand sources

Verbatim copies of the Redrob design system's shipped files (`redrob-design-system/assets/Favicons/`
and `assets/Logos/`). `SHA256SUMS` pins them; `scripts/check_brand.py` fails if any changes.
`packaging/brand-assets.sh` derives everything under `assets/app-icon/` and the web favicons from
these and nothing else.

| File | Use |
|---|---|
| `favicon-*.png`, `favicon.ico`, `favicon.svg`, `icon-192.png`, `icon-512.png` | the app icon and favicons |
| `redrob-logo-primary-white.png` | the lockup on dark themes (About, Home) |
| `redrob-logo-primary.png` | the lockup on the light theme |

Rules that bind here (design system `10-logo.md`, `assets/Favicons/README.md`, `assets/Logos/README.md`):

- Never redrawn, recolored, re-proportioned, traced, given a shadow, border or second radius. Pick
  the variant that matches the ground; never tint or fade a mark.
- Favicons: a white symbol on a Redrob Blue (`#2B52FF`) tile, one design, no dark-mode variant.
  Where the design system ships a size it is used as is; any other size is the next larger tile
  resized down. Nothing is upscaled.
- The lockup is at least 18 px tall on screen, with its clear space (0.5x above and below, 0.3x left
  and right, x = symbol height). The product name follows it at the UI's 600 weight, never inside
  the lockup's letterforms.

Redrob Film has no product glyph of its own in the design system yet, so the app carries the Redrob
tile. When a Cut glyph is added to `assets/Products/`, replace these sources, update `SHA256SUMS`
and rerun the script; nothing else changes.

Licence: the Redrob name and marks are trademarks of Redrob (McKinley Rice, Inc.), not covered by
this repository's MIT OR Apache-2.0 licence. A fork that is not Redrob's must remove them.
