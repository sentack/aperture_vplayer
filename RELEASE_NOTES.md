# Aperture 0.5.0

Aperture can now update itself.

## Downloads
- **Windows 10/11 (x64):** `Aperture-0.5.0-windows-x64-setup.exe`
- **macOS 12+ (Apple Silicon):** `Aperture-0.5.0-macos-arm64.dmg`
- **Linux (x86-64):** `Aperture-0.5.0-x86_64.AppImage`, or `Aperture-0.5.0-linux-x64.tar.xz`

## New

### About page
**Settings → About** shows the version you're running and the date it was released.

### Check for updates
Press **Check for updates** on the About page. Aperture asks GitHub once, only when you press it, and tells you either that you're on the latest version or which version is new, when it came out, and what changed.

### Update now
- **Update now** downloads the new version in the background, with progress shown on the About page. Your video keeps playing meanwhile.
- Before anything is installed, the download is checked against the release's published checksums. A damaged or altered download is thrown away.
- When it's ready, choose **Restart and update**, or **Later** to have it installed the next time you open Aperture.
- Your current version is kept until the new one has started once. If the new one fails to start, Aperture puts the old one back.

How it installs depends on how you installed Aperture:
- **Windows:** the new installer runs on its own after Aperture closes, then Aperture reopens.
- **Linux AppImage:** the file is replaced where it is, under the same name, so your menu entry and default-player choice keep working.
- **Linux tarball:** the folder is replaced in place.
- **macOS:** the new disk image opens; drag Aperture into Applications to replace the old copy.

## Good to know
- Copies you run from source, or that a package manager installed, aren't updated from inside the app.
- Updating from 0.4.0 or earlier: install 0.5.0 by hand once. From then on, updates come from inside the app.
