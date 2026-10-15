#!/usr/bin/env bash
# Build and package Redrob Film for Linux x86_64 (the only Linux release target):
#
#   $DIST/redrob-film-<version>-linux-x86_64.tar.gz    plain FHS-style tree (bin/, share/) + install.sh
#   $DIST/redrob-film-<version>-linux-x86_64.deb       Debian, Ubuntu, Mint, Pop!_OS, ...
#
# Usage: packaging/linux/package.sh [--skip-build] [--formats "deb tar"]
#
# Needs: cargo; nfpm for the deb (https://nfpm.goreleaser.com). Build on an old distro (CI: Ubuntu
# 22.04, glibc 2.35) so the binaries run on newer ones. Optional: desktop-file-validate,
# appstreamcli. The tar.gz is what Redrob Launcher and the in-app updater
# (apps/redrob-film-app/src/update.rs) install; both look for exactly these file names.
set -euo pipefail
# shellcheck source=../env.sh
. "$(dirname "${BASH_SOURCE[0]}")/../env.sh"
HERE="$ROOT/packaging/linux"
APP_ID=ai.redrob.film

SKIP_BUILD=0
FORMATS="deb tar"
while [ $# -gt 0 ]; do
  case "$1" in
    --skip-build) SKIP_BUILD=1; shift ;;
    --formats) FORMATS="$2"; shift 2 ;;
    -h | --help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
for fmt in $FORMATS; do
  case "$fmt" in
    deb | tar) ;;
    *) echo "unknown format $fmt (deb, tar)" >&2; exit 2 ;;
  esac
done

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64) DEB_ARCH=amd64 ;;
  *) echo "unsupported architecture $ARCH: the Linux release is x86_64 only" >&2; exit 2 ;;
esac
export REDROB_FILM_MAINTAINER="${REDROB_FILM_MAINTAINER:-Redrob (McKinley Rice, Inc.)}"
BASENAME="redrob-film-$VERSION-linux-$ARCH"

echo "==> Redrob Film $VERSION for Linux $ARCH ($FORMATS)"

if [ "$SKIP_BUILD" = 0 ]; then
  (cd "$ROOT" && cargo build --release --locked -p redrob-film-app -p redrob-film-cli)
fi
BIN="$CARGO_TARGET_DIR/release"
WORK="$CARGO_TARGET_DIR/linux-package"
STAGE="$WORK/root"
rm -rf "$WORK"

# ---- stage an FHS tree (shared by every format) -------------------------------------------------
install -Dm755 "$BIN/redrob-film" "$STAGE/usr/bin/redrob-film"
install -Dm755 "$BIN/redrob-film-cli" "$STAGE/usr/bin/redrob-film-cli"
strip "$STAGE/usr/bin/redrob-film" "$STAGE/usr/bin/redrob-film-cli" 2>/dev/null || true
install -Dm644 "$HERE/$APP_ID.desktop" "$STAGE/usr/share/applications/$APP_ID.desktop"
install -Dm644 "$HERE/$APP_ID.mime.xml" "$STAGE/usr/share/mime/packages/$APP_ID.xml"
mkdir -p "$STAGE/usr/share/metainfo"
sed -e "s/@VERSION@/$VERSION/g" -e "s/@DATE@/$REDROB_FILM_BUILD_DATE/g" \
  "$HERE/$APP_ID.metainfo.xml.in" >"$STAGE/usr/share/metainfo/$APP_ID.metainfo.xml"
mkdir -p "$STAGE/usr/share/icons"
cp -R "$ROOT/assets/app-icon/hicolor" "$STAGE/usr/share/icons/"
mkdir -p "$STAGE/usr/share/doc/redrob-film"
copy_docs "$STAGE/usr/share/doc/redrob-film"

if command -v desktop-file-validate >/dev/null; then
  desktop-file-validate "$STAGE/usr/share/applications/$APP_ID.desktop"
fi
if command -v appstreamcli >/dev/null; then
  appstreamcli validate --no-net --explain "$STAGE/usr/share/metainfo/$APP_ID.metainfo.xml"
fi

has() { case " $FORMATS " in *" $1 "*) return 0 ;; *) return 1 ;; esac; }

# ---- .tar.gz ------------------------------------------------------------------------------------
if has tar; then
  mkdir -p "$WORK/tar"
  cp -R "$STAGE/usr" "$WORK/tar/$BASENAME"
  install -m755 "$HERE/install.sh" "$WORK/tar/$BASENAME/install.sh"
  tar -C "$WORK/tar" -czf "$DIST/$BASENAME.tar.gz" "$BASENAME"
  echo "wrote $DIST/$BASENAME.tar.gz"
fi

# ---- .deb -------------------------------------------------------------------------------------
if has deb; then
  command -v nfpm >/dev/null || { echo "error: nfpm not found (https://nfpm.goreleaser.com/install/)" >&2; exit 1; }
  export VERSION
  export NFPM_ARCH="$DEB_ARCH"
  # nfpm expands env vars in fields like `version` and `arch`, but not in `contents[].src`.
  sed "s|\${STAGE}|$STAGE|g" "$HERE/nfpm.yaml" >"$WORK/nfpm.yaml"
  (cd "$ROOT" && nfpm package -f "$WORK/nfpm.yaml" -p deb -t "$DIST/$BASENAME.deb")
  echo "wrote $DIST/$BASENAME.deb"
fi

"$STAGE/usr/bin/redrob-film-cli" --version
echo "==> done"
ls -lh "$DIST"
