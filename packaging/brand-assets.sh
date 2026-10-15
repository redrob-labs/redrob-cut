#!/usr/bin/env bash
# Derive every app icon from the pinned design-system sources in assets/brand/ and nothing else.
# Needs ImageMagick 7 (`magick`), python3 and cargo. The outputs are committed, so builds and
# packaging never need these tools.
#
#   packaging/brand-assets.sh
#
# What is derived, and from what (assets/brand/README.md has the rules):
#   hicolor/{16,32,48,64}            the design system's per-size favicons, as is
#   hicolor/512, redrob-film-512.png  the 512 tile, as is
#   hicolor/{24,128,256}             the next larger tile resized DOWN (32, 192, 512), never up
#   hicolor/scalable                 favicon.svg, as is
#   redrob-film-256.png               the window icon: the 256 above
#   redrob-film.ico                   16, 32, 48, 64 as is + 256 resized down from 512
#   redrob-film.icns                  16, 32, 128, 256, 512
#   apps/filmcraft-web/web/          favicon.png (the 64 tile) and favicon.svg, as is
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
B="$ROOT/assets/brand"
A="$ROOT/assets/app-icon"
ID="ai.redrob.film"
command -v magick >/dev/null || { echo "error: magick (ImageMagick 7) not found" >&2; exit 1; }

(cd "$B" && sha256sum -c --quiet SHA256SUMS)

down() { magick "$1" -filter Lanczos -resize "$2x$2" "PNG32:$3"; }

# Keep the hand-written licence/readme; everything else here is regenerated.
find "$A" -mindepth 1 ! -name LICENSE.txt ! -name README.md -delete
for s in 16 24 32 48 64 128 256 512; do mkdir -p "$A/hicolor/${s}x${s}/apps"; done
mkdir -p "$A/hicolor/scalable/apps"
for s in 16 32 48 64; do cp "$B/favicon-${s}x${s}.png" "$A/hicolor/${s}x${s}/apps/$ID.png"; done
cp "$B/icon-512.png" "$A/hicolor/512x512/apps/$ID.png"
down "$B/favicon-32x32.png" 24 "$A/hicolor/24x24/apps/$ID.png"
down "$B/icon-192.png" 128 "$A/hicolor/128x128/apps/$ID.png"
down "$B/icon-512.png" 256 "$A/hicolor/256x256/apps/$ID.png"
cp "$B/favicon.svg" "$A/hicolor/scalable/apps/$ID.svg"

cp "$A/hicolor/256x256/apps/$ID.png" "$A/redrob-film-256.png"
cp "$B/icon-512.png" "$A/redrob-film-512.png"

(cd "$ROOT" && cargo run -q -p xtask -- ico "$A/redrob-film.ico" \
  "$B/favicon-16x16.png" "$B/favicon-32x32.png" "$B/favicon-48x48.png" "$B/favicon-64x64.png" \
  "$A/redrob-film-256.png")

python3 "$ROOT/packaging/make-icns.py" "$A/redrob-film.icns" \
  16="$B/favicon-16x16.png" 32="$B/favicon-32x32.png" \
  128="$A/hicolor/128x128/apps/$ID.png" 256="$A/redrob-film-256.png" 512="$B/icon-512.png"

W="$ROOT/apps/filmcraft-web/web"
cp "$B/favicon-64x64.png" "$W/favicon.png"
cp "$B/favicon.svg" "$W/favicon.svg"

# Every derived file gets an attribution sidecar (cargo xtask assets).
python3 "$ROOT/packaging/brand-sidecars.py"
echo "brand assets written to $A"
