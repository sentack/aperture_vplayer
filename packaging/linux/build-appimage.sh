#!/usr/bin/env bash
# Wrap the PyInstaller build (dist/aperture) into a compressed AppImage and tarball.
#
#   packaging/linux/build-appimage.sh 0.5.0
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

# Compression: xz for the AppImage's squashfs (smallest download; the BCJ x86 filter helps
# on the many shared libraries), xz -9 for the tarball. xz costs a little extra time on
# first launch, while the image is mounted.
appimage="$dist/Aperture-$version-x86_64.AppImage"
ARCH=x86_64 "$tool" --no-appstream --comp xz \
    --mksquashfs-opt -Xbcj --mksquashfs-opt x86 \
    "$appdir" "$appimage"
tar -C "$dist" -cf - aperture | xz -9 -T0 > "$dist/Aperture-$version-linux-x64.tar.xz"

# Prove the image really is compressed, and report what it saved.
if command -v unsquashfs >/dev/null; then
    offset="$("$appimage" --appimage-offset)"
    compression="$(unsquashfs -s -o "$offset" "$appimage" | sed -n 's/^Compression //p')"
    [[ "$compression" == xz ]] || { echo "AppImage compression is '$compression', expected xz" >&2; exit 1; }
    echo "AppImage: $(du -sh "$appdir" | cut -f1) unpacked -> $(du -h "$appimage" | cut -f1), $compression"
fi

echo "built $appimage"
