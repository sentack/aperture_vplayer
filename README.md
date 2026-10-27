<p align="center">
  <img src="packaging/icons/aperture-128.png" width="96" height="96" alt="Aperture icon">
</p>

<h1 align="center">Aperture</h1>

<p align="center">
  A lightweight desktop video player for Windows and Linux — a cleaner, calmer take on the classic players.
</p>

<!-- Screenshot / GIF: add assets/screenshot.png and assets/demo.gif, then reference them here. -->

## Download

Get the latest build from [Releases](https://github.com/sentack/aperture_vplayer/releases).

| Platform | File | How to run |
|---|---|---|
| Windows 10/11 (x64) | `Aperture-<version>-windows-x64-setup.exe` | Run the installer. No admin rights needed; it can add Aperture to "Open with" for video files. |
| Linux (x86-64) | `Aperture-<version>-x86_64.AppImage` | `chmod +x Aperture-*.AppImage` then run it. |
| Linux (x86-64) | `Aperture-<version>-linux-x64.tar.gz` | Extract and run `aperture/aperture`. |

On X11, Qt needs `libxcb-cursor0` (Debian/Ubuntu: `sudo apt install libxcb-cursor0`).

## Features

**Playback**
- MP4, MKV, AVI, MOV, WebM and more through Qt Multimedia's FFmpeg backend
- Play, pause, stop, seek by click or drag, with a frame preview when hovering the seek bar
- Volume and mute, speed from 0.25× to 2×
- Fullscreen, and an always-on-top mini player you can drag anywhere
- Controls fade away while you watch, leaving a thin progress line

**Library**
- Playlist with add, remove, next/previous and auto-advance; drop files or whole folders
- Recent files on the start screen
- Resumes where you left off, per file, and forgets once you finish

**Subtitles and audio**
- Embedded subtitle tracks, plus `.srt` / `.vtt` files — same-name files next to the video load automatically
- Audio track switching for multi-language files

**Look and feel**
- Light, dark or follow-the-system theme, five accent colors
- Friendly messages instead of crashes when a file can't be played

## Keyboard shortcuts

| Key | Action |
|---|---|
| Space, K | Play / pause |
| ← / → | Seek 5 s |
| J / L | Seek 10 s |
| Shift+← / Shift+→ | Seek 30 s |
| Home | Back to start |
| ↑ / ↓ | Volume ±5% |
| M | Mute |
| N / P | Next / previous |
| [ / ] | Slower / faster |
| = | Normal speed |
| C | Subtitles on / off |
| A | Next audio track |
| I | Mini player |
| F, F11 | Fullscreen |
| Esc | Leave fullscreen |
| Ctrl+O | Open files |

## Your data

Aperture keeps three small files in the platform app-data folder — `~/.local/share/Aperture/` on Linux, `%APPDATA%\Aperture\` on Windows:

- `history.json` — recent files and resume points
- `settings.json` — theme and accent
- `aperture.log` — rotating log; attach it to bug reports

Delete any of them to reset that part.

## Build from source

Requires Python 3.11+.

```sh
python -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
aperture [video-or-folder ...]
```

Run the tests (the QML smoke test needs a display, or `QT_QPA_PLATFORM=offscreen`):

```sh
pytest
```

Package locally:

```sh
pip install -e ".[build]"
pyinstaller --noconfirm packaging/aperture.spec             # -> dist/aperture/
iscc /DAppVersion=0.4.0 packaging\windows\aperture.iss      # Windows, needs Inno Setup 6
packaging/linux/build-appimage.sh 0.4.0                     # Linux, needs appimagetool
```

The icon is generated from code: `python packaging/make_icons.py`.

## Releasing

1. Bump `__version__` in `src/aperture/__init__.py`.
2. Tag and push: `git tag v0.4.0 && git push origin v0.4.0`.

The release workflow tests, builds the Windows installer and the Linux AppImage and tarball, and publishes them to a GitHub release.

## Project layout

```
src/aperture/
  core/      pure Python: playlist, history, subtitle parsing, formats — fully unit-tested
  player/    Qt Multimedia: playback controller, track selection, thumbnail decoder
  theme/     design tokens and the live light/dark theme
  ui/qml/    the interface
packaging/   PyInstaller spec, Windows installer, AppImage script, icon generator
```

## Design

- UI spec: [docs/DESIGN_SPEC.md](docs/DESIGN_SPEC.md)
- Mockup: [docs/reference.html](docs/reference.html)
