#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Run in VideoLAN's win64 CI image. Produces a portable ZIP, no host install.
set -euo pipefail
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
# The portable validation build can capture its own Qt scene when explicitly
# requested with VLC_QT_UI_TEST_OUTPUT. Ordinary source builds exclude the hook.
export CPPFLAGS="${CPPFLAGS:-} -DVLC_QT_UI_TESTING"

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
# The published bundle's HostData contains a relative prefix concatenated with
# its relocation marker. HostPrefix is relative to the original GitLab layout.
# Use explicit target/native paths for this out-of-tree GitHub checkout.
target_qt_prefix="$source_root/.build/contrib/x86_64-w64-mingw32"
host_qt_prefix=$(qmake6 -query QT_HOST_PREFIX)
cat > "$source_root/.build/relocated-qt.conf" <<EOF
[Paths]
Prefix=$target_qt_prefix
Documentation=doc
Headers=include
Libraries=lib
LibraryExecutables=bin
Binaries=bin
Plugins=plugins
QmlImports=qml
ArchData=.
Data=.
Translations=translations
Examples=examples
Tests=tests
Settings=etc/xdg
HostPrefix=$host_qt_prefix
HostBinaries=bin
HostLibraries=lib
HostLibraryExecutables=libexec
HostData=$target_qt_prefix
Sysroot=
SysrootifyPrefix=false
TargetSpec=win32-g++
HostSpec=
EOF
export CONFIGFLAGS="${CONFIGFLAGS:-} --with-qtconf=$source_root/.build/relocated-qt.conf"
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
python3 - "${packages[0]}" "$source_root" <<'PY'
import sys
import subprocess
from pathlib import Path
import zipfile

with zipfile.ZipFile(sys.argv[1]) as package:
    names = package.namelist()
    required = ('/vlc.exe', '/libvlc.dll', '/libvlccore.dll', '/plugins/gui/libqt_plugin.dll')
    missing = [suffix for suffix in required if not any(n.endswith(suffix) for n in names)]
    if missing:
        raise SystemExit(f'Portable package is missing required files: {missing}')
    roots = {name.split('/')[0] for name in names if name.endswith('/vlc.exe')}
    if len(roots) != 1:
        raise SystemExit(f'Unexpected package roots: {roots}')
    root = roots.pop()
# Some prebuilt contrib archives retain a shared GCC unwind dependency.
# Include the matching target compiler runtime in the portable package.
runtimes = []
for name in ("libgcc_s_seh-1.dll", "libwinpthread-1.dll", "libstdc++-6.dll"):
    result = subprocess.check_output(["x86_64-w64-mingw32-g++", "-print-file-name=" + name], text=True).strip()
    path = Path(result)
    if not path.is_file():
        raise SystemExit(f"Target compiler runtime not found: {name} ({path})")
    runtimes.append(path)
source_root = Path(sys.argv[2])
licenses = {path.name: path.read_bytes() for path in
            (source_root / '.github/licenses/compiler-runtime').iterdir() if path.is_file()}
with zipfile.ZipFile(sys.argv[1], 'a', compression=zipfile.ZIP_DEFLATED) as package:
    existing = set(package.namelist())
    for runtime in runtimes:
        destination = f'{root}/{runtime.name}'
        if destination not in existing:
            package.write(runtime, destination)
    for name, contents in licenses.items():
        package.writestr(f'{root}/gcc-runtime-licenses/{name}', contents)
    for family in ('inter', 'dmmono'):
        package.write(source_root / f'modules/gui/qt/pixmaps/fonts/{family}/OFL.txt',
                      f'{root}/design-font-licenses/{family}-OFL.txt')
    package.write(source_root / 'doc/juxtopposed-redesign.md', f'{root}/JUXTOPPOSED-CREDITS.md')
    # VLC recognizes this directory and keeps configuration with the ZIP build.
    package.writestr(f'{root}/portable/vlc/vlc-qt-interface.ini',
                     '[MainWindow]\ncolor-scheme-index=2\n')
    package.writestr(f'{root}/portable/vlcrc', '[qt]\nqt-pin-controls=1\n')
print('Portable package includes VLC, core libraries, and the native Qt plugin.')
PY
cp "${packages[0]}" "$source_root/build-output/"
cd "$source_root/build-output"
sha256sum ./*.zip > SHA256SUMS
printf 'source_revision=%s\ncontrib_revision=%s\ncontrib_url=%s\n' \
    "$source_revision" "$VLC_CONTRIB_SHA" "$VLC_PREBUILT_CONTRIBS_URL" > build-receipt.txt
printf 'This package includes the community Qt redesign inspired by Juxtopposed.\nUnzip it and launch vlc.exe; no VLC installer is needed.\nNative runtime and visual checks must still be performed on the resulting package.\n' > TRY-THIS-BUILD.txt
