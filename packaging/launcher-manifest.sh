#!/usr/bin/env bash
# Write the Redrob Launcher release manifest, `redrob-launcher.json`, into a release asset
# directory. The launcher reads this one small file beside the installers of every GitHub Release
# to learn what the release can do; `sharedAccount: true` says this build reads the launcher's
# shared account file, so signing in to the launcher is all a user needs (shipped in v0.0.1).
#
# Usage: packaging/launcher-manifest.sh <release-asset-dir>
#
# Run it before the checksums, so the file is listed in SHA256SUMS.txt like every other asset;
# packaging/check_release_assets.py refuses a release directory that lacks it.
set -euo pipefail

if [ $# -ne 1 ] || [ ! -d "$1" ]; then
  echo "usage: $0 <release-asset-dir>" >&2
  exit 2
fi

printf '{ "schema": 1, "sharedAccount": true }\n' >"$1/redrob-launcher.json"
echo "wrote $1/redrob-launcher.json"
