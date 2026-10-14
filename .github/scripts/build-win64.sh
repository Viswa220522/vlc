#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Run in VideoLAN's win64 CI image. Produces a portable ZIP, no host install.
set -euo pipefail

source_root=$(git rev-parse --show-toplevel)
cd "$source_root"
source_revision=$(git rev-parse HEAD)
export VLC_CONTRIB_SHA
VLC_CONTRIB_SHA=$(bash extras/ci/get-contrib-sha.sh win64)
export VLC_PREBUILT_CONTRIBS_URL="https://artifacts.videolan.org/vlc/win64/vlc-contrib-x86_64-w64-mingw32-${VLC_CONTRIB_SHA}.tar.zst"

printf 'Source revision: %s\nContrib revision: %s\n' "$source_revision" "$VLC_CONTRIB_SHA"
x86_64-w64-mingw32-gcc --version
x86_64-w64-mingw32-g++ --version
# Fail clearly if the matching upstream dependencies have not been published.
# Avoid silently compiling every dependency from source in a hosted runner.
curl --fail --location --head --max-time 60 "$VLC_PREBUILT_CONTRIBS_URL"

mkdir -p "$source_root/.build" "$source_root/build-output"
cd "$source_root/.build"
export JOBS=2
"$source_root/extras/package/win32/build.sh" -a x86_64 -p 2>&1 | tee win64-build.log
make -C win64 -j2 package-win32-zip 2>&1 | tee -a win64-build.log

shopt -s nullglob
packages=(win64/vlc-*-win64.zip)
if (( ${#packages[@]} != 1 )); then
    printf 'Expected one Windows ZIP; found %s\n' "${#packages[@]}" >&2
    exit 1
fi
python3 - "${packages[0]}" <<'PY'
import sys
import zipfile

with zipfile.ZipFile(sys.argv[1]) as package:
    names = package.namelist()
    required = ('/vlc.exe', '/libvlc.dll', '/libvlccore.dll', '/plugins/gui/libqt_plugin.dll')
    missing = [suffix for suffix in required if not any(n.endswith(suffix) for n in names)]
    if missing:
        raise SystemExit(f'Portable package is missing required files: {missing}')
print('Portable package includes VLC, core libraries, and the native Qt plugin.')
PY
cp "${packages[0]}" "$source_root/build-output/"
cd "$source_root/build-output"
sha256sum ./*.zip > SHA256SUMS
printf 'source_revision=%s\ncontrib_revision=%s\ncontrib_url=%s\n' \
    "$source_revision" "$VLC_CONTRIB_SHA" "$VLC_PREBUILT_CONTRIBS_URL" > build-receipt.txt
printf 'This package includes the community Qt redesign inspired by Juxtopposed.\nUnzip it and launch vlc.exe; no VLC installer is needed.\nNative runtime and visual checks must still be performed on the resulting package.\n' > TRY-THIS-BUILD.txt
