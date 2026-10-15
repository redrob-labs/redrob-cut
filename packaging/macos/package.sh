#!/usr/bin/env bash
# Build, sign and (optionally) notarize the macOS release artifacts:
#
#   $DIST/redrob-film-<version>-macos-<arch>.dmg          Redrob Film.app on a drag-to-Applications DMG
#   $DIST/redrob-film-cli-<version>-macos-<arch>.zip      the headless CLI
#
# Usage: packaging/macos/package.sh [--arch universal|aarch64|x86_64] [--skip-build]
#
# Signing (env):
#   MACOS_SIGN_IDENTITY   codesign identity (name or SHA-1). Default "-" = ad-hoc (local testing;
#                         Gatekeeper will reject the result on other Macs). In CI, import-cert.sh sets it.
#   MACOS_KEYCHAIN        keychain holding the identity (optional)
# Notarization (env; needs a real identity and one complete set):
#   APPLE_NOTARY_API_KEY_P8_BASE64, APPLE_NOTARY_API_KEY_ID, APPLE_NOTARY_API_ISSUER_ID (API key), or
#   APPLE_ID, APPLE_PASSWORD (app-specific password), APPLE_TEAM_ID
set -euo pipefail
# shellcheck source=../env.sh
. "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
HERE="$ROOT/packaging/macos"

ARCH=universal
SKIP_BUILD=0
while [ $# -gt 0 ]; do
  case "$1" in
    --arch) ARCH="$2"; shift 2 ;;
    --skip-build) SKIP_BUILD=1; shift ;;
    -h | --help) sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
case "$ARCH" in
  universal) TARGETS=(aarch64-apple-darwin x86_64-apple-darwin) ;;
  aarch64) TARGETS=(aarch64-apple-darwin) ;;
  x86_64) TARGETS=(x86_64-apple-darwin) ;;
  *) echo "unknown --arch $ARCH" >&2; exit 2 ;;
esac

# Keep in sync with LSMinimumSystemVersion in Info.plist.in.
export MACOSX_DEPLOYMENT_TARGET=11.0
IDENTITY="${MACOS_SIGN_IDENTITY:--}"
SHORT_VERSION="${VERSION%%-*}"
WORK="$CARGO_TARGET_DIR/macos-package"
APP="$WORK/Redrob Film.app"
DMG="$DIST/redrob-film-$VERSION-macos-$ARCH.dmg"
CLI_ZIP="$DIST/redrob-film-cli-$VERSION-macos-$ARCH.zip"

NOTARIZE=0
NOTARY_AUTH=()
if [ "$IDENTITY" = "-" ]; then
  warn "macOS: ad-hoc signing (no MACOS_SIGN_IDENTITY); artifacts are not notarized"
elif [ -n "${APPLE_NOTARY_API_KEY_P8_BASE64:-}" ] && [ -n "${APPLE_NOTARY_API_KEY_ID:-}" ] &&
  [ -n "${APPLE_NOTARY_API_ISSUER_ID:-}" ]; then
  # App Store Connect API key (the redrob-labs organization secrets). Written 0600 to the
  # runner's temp dir and removed on exit.
  NOTARY_KEY="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/AuthKey_$APPLE_NOTARY_API_KEY_ID.p8"
  (umask 077 && printf '%s' "$APPLE_NOTARY_API_KEY_P8_BASE64" | base64 --decode >"$NOTARY_KEY")
  trap 'rm -f "$NOTARY_KEY"' EXIT
  NOTARY_AUTH=(--key "$NOTARY_KEY" --key-id "$APPLE_NOTARY_API_KEY_ID" --issuer "$APPLE_NOTARY_API_ISSUER_ID")
  NOTARIZE=1
elif [ -n "${APPLE_ID:-}" ] && [ -n "${APPLE_PASSWORD:-}" ] && [ -n "${APPLE_TEAM_ID:-}" ]; then
  NOTARY_AUTH=(--apple-id "$APPLE_ID" --password "$APPLE_PASSWORD" --team-id "$APPLE_TEAM_ID")
  NOTARIZE=1
else
  warn "macOS: no notarization credentials (APPLE_NOTARY_API_KEY_* or APPLE_ID/APPLE_PASSWORD/APPLE_TEAM_ID); signed but not notarized"
fi

echo "==> Redrob Film $VERSION for macOS ($ARCH), identity: $IDENTITY, notarize: $NOTARIZE"

# ---- build -------------------------------------------------------------------------------------
if [ "$SKIP_BUILD" = 0 ]; then
  args=()
  for t in "${TARGETS[@]}"; do args+=(--target "$t"); done
  (cd "$ROOT" && cargo build --release --locked -p redrob-film-app -p redrob-film-cli "${args[@]}")
fi

rm -rf "$WORK"
mkdir -p "$WORK/bin"
for bin in redrob-film redrob-film-cli; do
  inputs=()
  for t in "${TARGETS[@]}"; do inputs+=("$CARGO_TARGET_DIR/$t/release/$bin"); done
  lipo -create -output "$WORK/bin/$bin" "${inputs[@]}"
  lipo -info "$WORK/bin/$bin"
done

# ---- signing helpers ---------------------------------------------------------------------------
sign() {
  # Hardened runtime + secure timestamp for a real identity; ad-hoc can't be timestamped.
  local ts=(--timestamp)
  [ "$IDENTITY" = "-" ] && ts=(--timestamp=none)
  local kc=()
  [ -n "${MACOS_KEYCHAIN:-}" ] && kc=(--keychain "$MACOS_KEYCHAIN")
  codesign --force --sign "$IDENTITY" ${kc[@]+"${kc[@]}"} "${ts[@]}" "$@"
}

notarize() {
  local file="$1" out id status
  echo "==> notarizing $(basename "$file") (this can take a few minutes)"
  out="$(xcrun notarytool submit "$file" "${NOTARY_AUTH[@]}" \
    --wait --timeout 1h --output-format json)" || true
  echo "$out"
  id="$(printf '%s' "$out" | plutil -extract id raw -o - - 2>/dev/null || true)"
  status="$(printf '%s' "$out" | plutil -extract status raw -o - - 2>/dev/null || true)"
  if [ "$status" != "Accepted" ]; then
    if [ -n "$id" ]; then
      xcrun notarytool log "$id" "${NOTARY_AUTH[@]}" || true
    fi
    echo "error: notarization of $(basename "$file") failed (status: ${status:-unknown})" >&2
    exit 1
  fi
}

# ---- Redrob Film.app ----------------------------------------------------------------------------
echo "==> assembling $APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
# Executable and icon carry the display name (CFBundleExecutable / CFBundleIconFile).
cp "$WORK/bin/redrob-film" "$APP/Contents/MacOS/Redrob Film"
cp "$ROOT/assets/app-icon/redrob-film.icns" "$APP/Contents/Resources/Redrob Film.icns"
sed -e "s/@VERSION@/$VERSION/g" -e "s/@SHORT_VERSION@/$SHORT_VERSION/g" \
  -e "s/@BUILD_SHA@/${REDROB_FILM_BUILD_SHA:-unknown}/g" \
  "$HERE/Info.plist.in" >"$APP/Contents/Info.plist"
plutil -lint "$APP/Contents/Info.plist"
printf 'APPL????' >"$APP/Contents/PkgInfo"
# licences of the embedded craft-fonts fonts (builds with CRAFT_FONTS_DIR)
copy_font_licences "$APP/Contents/Resources"

# Sign inside-out: nested code first, then the bundle itself (no --deep on the final signature).
# Today the only nested code is the main executable; frameworks/helpers would be signed here too.
sign --options runtime --entitlements "$HERE/entitlements.plist" "$APP/Contents/MacOS/Redrob Film"
sign --options runtime --entitlements "$HERE/entitlements.plist" "$APP"
codesign --verify --strict --deep --verbose=2 "$APP"

if [ "$NOTARIZE" = 1 ]; then
  ditto -c -k --keepParent "$APP" "$WORK/RedrobFilm-notarize.zip"
  notarize "$WORK/RedrobFilm-notarize.zip"
  xcrun stapler staple "$APP"
  xcrun stapler validate "$APP"
  spctl --assess --type execute -vvv "$APP"
fi

# ---- DMG ---------------------------------------------------------------------------------------
echo "==> building $DMG"
STAGE="$WORK/dmg"
mkdir -p "$STAGE"
ditto "$APP" "$STAGE/Redrob Film.app"
ln -s /Applications "$STAGE/Applications"
# Finder window layout: background, icon size and positions (packaging/macos/dmg/README.md).
mkdir -p "$STAGE/.background"
cp "$HERE/dmg/background.tiff" "$STAGE/.background/background.tiff"
cp "$HERE/dmg/dmg-layout.DS_Store" "$STAGE/.DS_Store"
rm -f "$DMG" "$WORK/raw.dmg"
# makehybrid + convert builds the image without attaching a device, unlike `create -srcfolder`,
# which is flaky on CI runners ("Resource busy") and hangs in sandboxed sessions.
# The volume name has no version: .DS_Store finds the background through an alias that includes it.
hdiutil makehybrid -hfs -hfs-volume-name "Redrob Film" -hfs-openfolder "$STAGE" -o "$WORK/raw.dmg" "$STAGE"
hdiutil convert "$WORK/raw.dmg" -format UDZO -imagekey zlib-level=9 -o "$DMG"
rm -f "$WORK/raw.dmg"
sign "$DMG"
codesign --verify --strict --verbose=2 "$DMG"
if [ "$NOTARIZE" = 1 ]; then
  notarize "$DMG"
  xcrun stapler staple "$DMG"
  xcrun stapler validate "$DMG"
  spctl --assess --type open --context context:primary-signature -vvv "$DMG"
fi

# ---- CLI ---------------------------------------------------------------------------------------
echo "==> building $CLI_ZIP"
CLI_DIR="$WORK/redrob-film-cli-$VERSION-macos-$ARCH"
mkdir -p "$CLI_DIR"
cp "$WORK/bin/redrob-film-cli" "$CLI_DIR/"
copy_docs "$CLI_DIR"
sign --options runtime "$CLI_DIR/redrob-film-cli"
codesign --verify --strict --verbose=2 "$CLI_DIR/redrob-film-cli"
rm -f "$CLI_ZIP"
ditto -c -k --keepParent "$CLI_DIR" "$CLI_ZIP"
# A bare Mach-O can't carry a stapled ticket; Gatekeeper looks the notarization up online.
if [ "$NOTARIZE" = 1 ]; then notarize "$CLI_ZIP"; fi

"$WORK/bin/redrob-film-cli" --version
echo "==> done"
ls -lh "$DMG" "$CLI_ZIP"
