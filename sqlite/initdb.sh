#!/bin/sh
set -eu

temp_dir=$(mktemp -d)
trap 'rm -rf "$temp_dir"' EXIT

archive="$temp_dir/archive.tar.zst"
download_url=${ASSET_DOWNLOAD_URL:-https://dl.vndb.org/dump/vndb-db-latest.tar.zst}
asset_url=$(curl -fL --retry 3 -w '%{url_effective}' -o "$archive" -- "$download_url")

python3 "$(dirname "$0")/build.py" "$archive" "$@"

if [ -n "${VNDB_SOURCE_NAME_FILE:-}" ]; then
    asset_path=${asset_url%%\?*}
    asset_path=${asset_path%%\#*}
    printf '%s\n' "${asset_path##*/}" > "$VNDB_SOURCE_NAME_FILE"
fi
