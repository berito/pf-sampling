#!/usr/bin/env bash
# Build OpenSLAM gmapping inside the devcontainer.
#
# vendor/openslam_gmapping stays untouched. The source is copied into .build/openslam_gmapping,
# the patch is applied to that copy, and the build happens there.
#
# The upstream build predates modern GNU make and g++, so patches/0001-*.patch fixes three
# things: a space before a tab in a make recipe, a variable redeclaration in gfs2rec.cpp,
# and a stray "<< cout" in gsp_thread.cpp.
#
# The Qt gui subdirectory is dropped because it needs Qt3. gfs_nogui, the headless SLAM
# runner, does not need Qt at all, so it is compiled directly against the built libraries.
#
# Binaries and libraries find each other through a relative library path ($ORIGIN/../lib), so the build
# keeps working wherever the project folder is, inside or outside the container.
set -euo pipefail

PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$PROJECT/vendor/openslam_gmapping"
PATCH="$PROJECT/tools/patches/0001-gmapping-modern-toolchain-fixes.patch"
ROOT="$PROJECT/.build/openslam_gmapping"

echo "==> copying vendor source to $ROOT"
rm -rf "$ROOT"
mkdir -p "$PROJECT/.build"
cp -r "$SRC" "$ROOT"
rm -rf "$ROOT/.git"

echo "==> applying patch"
patch -d "$ROOT" -p1 --quiet < "$PATCH"

cd "$ROOT"

echo "==> configure"
./configure > /dev/null
# configure writes the absolute build path into the linker settings; make it relative instead.
# The makefile passes each command through make, sh and an eval, hence three levels of escaping.
grep -v '^LDFLAGS+= -Xlinker -rpath' global.mk > global.mk.tmp
cat >> global.mk.tmp <<'MAKE'
LDFLAGS+= -Wl,-rpath,\\\$$ORIGIN/../lib
MAKE
mv global.mk.tmp global.mk

echo "==> building libraries and tools"
make -j"$(nproc)" > "$PROJECT/.build/gmapping_make.log" 2>&1 || { tail -30 "$PROJECT/.build/gmapping_make.log"; exit 1; }

echo "==> building headless runner (gfs_nogui)"
cd "$ROOT/gui"
g++ -fPIC -DLINUX -I"$ROOT" -I"$ROOT/sensor" -O3 -c gsp_thread.cpp -o "$PROJECT/.build/gsp_thread.o"
g++ -fPIC -DLINUX -I"$ROOT" -I"$ROOT/sensor" -O3 -c gfs_nogui.cpp  -o "$PROJECT/.build/gfs_nogui.o"
g++ "$PROJECT/.build/gfs_nogui.o" "$PROJECT/.build/gsp_thread.o" -L"$ROOT/lib" \
    -lgridfastslam -lscanmatcher -llog -lsensor_range -lsensor_odometry \
    -lsensor_base -lconfigfile -lutils -lpthread \
    -Wl,-rpath,'$ORIGIN/../lib' -o "$ROOT/bin/gfs_nogui"

echo
echo "libraries: $(ls "$ROOT/lib" | tr '\n' ' ')"
echo "binaries : $(ls "$ROOT/bin" | tr '\n' ' ')"
echo
echo "Run SLAM on a CARMEN log with:"
echo "  $ROOT/bin/gfs_nogui -filename <log.clf> -particles 30 -resampleThreshold 0.5"
echo "Then extract the effective-sample-size trace with:"
echo "  $ROOT/bin/gfs2neff <out.gfs> neff.txt"
