#!/usr/bin/env bash
# Wrap the PyInstaller build (dist/aperture) into an AppImage and a plain tarball.
#
#   packaging/linux/build-appimage.sh 0.2.0
#
# Needs appimagetool on PATH or in $APPIMAGETOOL. Without FUSE (containers, CI),
# export APPIMAGE_EXTRACT_AND_RUN=1 first.
set -euo pipefail

version="${1:?usage: build-appimage.sh VERSION}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
dist="$root/dist"
app_id="io.github.sentack.Aperture"
appdir="$dist/Aperture.AppDir"
tool="${APPIMAGETOOL:-appimagetool}"

[[ -x "$dist/aperture/aperture" ]] || { echo "run pyinstaller packaging/aperture.spec first" >&2; exit 1; }

rm -rf "$appdir"
mkdir -p "$appdir/usr/bin" \
         "$appdir/usr/share/applications" \
         "$appdir/usr/share/icons/hicolor/256x256/apps" \
         "$appdir/usr/share/icons/hicolor/scalable/apps"

cp -a "$dist/aperture/." "$appdir/usr/bin/"
cp "$root/packaging/linux/$app_id.desktop" "$appdir/usr/share/applications/"
cp "$root/packaging/linux/$app_id.desktop" "$appdir/"
cp "$root/packaging/icons/aperture-256.png" "$appdir/usr/share/icons/hicolor/256x256/apps/$app_id.png"
cp "$root/packaging/icons/aperture.svg" "$appdir/usr/share/icons/hicolor/scalable/apps/$app_id.svg"
cp "$root/packaging/icons/aperture-256.png" "$appdir/$app_id.png"
ln -sf "$app_id.png" "$appdir/.DirIcon"

cat > "$appdir/AppRun" <<'EOF'
#!/bin/sh
here="$(dirname "$(readlink -f "$0")")"
exec "$here/usr/bin/aperture" "$@"
EOF
chmod +x "$appdir/AppRun"

ARCH=x86_64 "$tool" --no-appstream "$appdir" "$dist/Aperture-$version-x86_64.AppImage"
tar -C "$dist" -czf "$dist/Aperture-$version-linux-x64.tar.gz" aperture

echo "built $dist/Aperture-$version-x86_64.AppImage"
