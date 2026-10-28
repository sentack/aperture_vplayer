# Aperture 0.2.0

Settings and customization, and Aperture now runs on macOS.

## Downloads
- **Windows 10/11 (x64):** `Aperture-0.2.0-windows-x64-setup.exe`
- **macOS 12+ (Apple Silicon):** `Aperture-0.2.0-macos-arm64.dmg`. Open it and drag Aperture to Applications.
- **Linux (x86-64):** `Aperture-0.2.0-x86_64.AppImage`, or `Aperture-0.2.0-linux-x64.tar.gz`

## New: Settings
Open it with the gear at the right of the control bar, or Ctrl+, (⌘, on macOS).
- **Theme:** light, dark or follow the system
- **Accent color:** applied live to the seek bar, buttons and active states
- **Starting volume** for new sessions
- **Starting speed:** always a fixed preset, or the last speed you used
- **Subtitles:** on or off by default, and text size from S to XL
- **Keyboard shortcuts:** the full list, read-only
- **Reset to defaults:** one button

## New: macOS
- Native `.app` in a disk image, appears in Finder's "Open With" for video files
- Window controls on the left, as on other Mac apps
- ⌘ shortcuts: ⌘O to open, ⌘, for settings

## Changes
- The accent swatch moved from the control bar into Settings.

## Known limitations
- macOS builds target Apple Silicon. An unsigned build is blocked on first launch: open **System Settings → Privacy & Security** and click **Open Anyway**.
- Subtitle size applies to `.srt` / `.vtt` files; embedded subtitle tracks keep the video's own styling.
- On Wayland, the mini player may not stay on top or open in the corner.
