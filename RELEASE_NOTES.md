# Aperture 0.1.0

First public release of Aperture, a lightweight video player for Windows and Linux.

## Downloads
- **Windows 10/11 (x64):** `Aperture-0.1.0-windows-x64-setup.exe`. Installs without admin rights and can add Aperture to "Open with" for video files.
- **Linux (x86-64):** `Aperture-0.1.0-x86_64.AppImage`. Run `chmod +x` on it, then start it. On X11 you may need `libxcb-cursor0`.
- **Linux tarball:** `Aperture-0.1.0-linux-x64.tar.gz`. Extract it and run `aperture/aperture`.

## Highlights
- Plays MP4, MKV, AVI, MOV, WebM and more
- Playlist with drag-and-drop for files and whole folders
- Picks up where you left off; recent files on the start screen
- Subtitles: embedded tracks plus `.srt` / `.vtt`, loaded automatically when they sit next to the video
- Audio track switching for multi-language files
- Speed from 0.25× to 2×
- Frame preview when hovering the seek bar
- Fullscreen and an always-on-top mini player
- Light, dark or system theme with five accent colors
- Keyboard shortcuts for everything (full list in the README)
- Clear messages instead of crashes when a file can't be played

## Known limitations
- On Wayland, the mini player may not stay on top or open in the corner.
- Builds are unsigned, so Windows SmartScreen may warn on first run. Choose **More info → Run anyway**.
