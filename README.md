<p align="center">
  <img src="packaging/icons/aperture-128.png" width="96" height="96" alt="Aperture icon">
</p>

<h1 align="center">Aperture</h1>

<p align="center">
  A lightweight desktop video player for Windows, macOS and Linux — a cleaner, calmer take on the classic players.
</p>

<!-- Screenshot / GIF: add assets/screenshot.png and assets/demo.gif, then reference them here. -->

## Download

Get the latest build from [Releases](https://github.com/sentack/aperture_vplayer/releases).

| Platform | File | How to run |
|---|---|---|
| Windows 10/11 (x64) | `Aperture-<version>-windows-x64-setup.exe` | Run the installer. No admin rights needed; it can add Aperture to "Open with" for video files. |
| Linux (x86-64) | `Aperture-<version>-x86_64.AppImage` | `chmod +x Aperture-*.AppImage` then run it. |
| Linux (x86-64) | `Aperture-<version>-linux-x64.tar.xz` | Extract and run `aperture/aperture`. |
| macOS 12+ (Apple Silicon) | `Aperture-<version>-macos-arm64.dmg` | Open the disk image and drag Aperture to Applications. |

On X11, Qt needs `libxcb-cursor0` (Debian/Ubuntu: `sudo apt install libxcb-cursor0`).

Keep the AppImage at one place under one name, such as `~/Applications/Aperture.AppImage`. In-app updates replace that file where it is, so menu entries and "default player" settings that point at it keep working.

If a macOS build is not notarized, Gatekeeper blocks its first launch. Open **System Settings → Privacy & Security** and click **Open Anyway**, or run `xattr -dr com.apple.quarantine /Applications/Aperture.app`.

## Features

**Playback**
- MP4, MKV, AVI, MOV, WebM and more through Qt Multimedia's FFmpeg backend: H.264, HEVC (H.265), VP8, VP9 and AV1 video (AV1 where the graphics hardware decodes it), with Opus, AAC, MP3, FLAC and Vorbis audio
- Play, pause, stop, seek by click or drag, with a frame preview when hovering the seek bar
- Volume and mute, speed from 0.25× to 2×
- Fullscreen, and an always-on-top picture-in-picture window (Ctrl+P) sized to the video
- Chapters in MKV, WebM and MP4 files: ticks on the seek bar, Ctrl+. / Ctrl+, to jump, a Chapters menu
- Audio boost up to 200%, with a limiter so loud parts don't crackle
- Controls fade away while you watch, leaving a thin progress line

**Library**
- Playlist with add, remove, next/previous and auto-advance; drop files or whole folders; double-click a row to play it
- Recent files on the start screen
- Resumes where you left off, per file, and forgets once you finish

**Subtitles and audio**
- Embedded subtitle tracks, plus `.srt` / `.vtt` files — same-name files next to the video load automatically
- Subtitle delay (G / H) to fix out-of-sync subtitle files
- Audio track switching for multi-language files

**Look and feel**
- Light, dark or follow-the-system theme, five accent colors
- Friendly messages instead of crashes when a file can't be played

**Audio and lyrics**
- Plays MP3, FLAC, M4A, Ogg, Opus, WAV and more
- Synced lyrics that scroll with the song, Spotify-style; click a line to jump there
- Lyrics come from a `.lrc` / `.txt` file next to the track, or from the file's own tags
- Write lyrics, tap along to sync them, then save a `.lrc` and embed it in MP3, FLAC, M4A, Ogg or Opus tags

**Settings** (gear at the right of the control bar, or Ctrl+, / ⌘,)
- **General:** make Aperture the default player, reset everything to defaults
- **Playback:** starting volume and speed, and whether to ask, resume or start over on files you left partway
- **Appearance:** theme and accent color, applied live
- **Subtitles:** on or off by default, text size
- **Keyboard shortcuts:** the full list

**Quick options and precise control**
- Right-click the video (or Shift+F10 / the Menu key) for play, open file or URL, A–B loop, screenshot, speed, audio and subtitle tracks, fullscreen and settings
- A–B loop: press L at the start, again at the end, a third time to stop looping
- Step one frame at a time with `.` and `,`
- Screenshots (S) go to your Pictures folder, under Aperture
- Open network streams and direct links: http(s), HLS `.m3u8`, RTSP, RTMP…

**Updates** (Settings → About)
- See your version and its release date, and check GitHub for a newer one
- **Update now** downloads in the background and verifies it against the release's checksums before anything is installed
- Restart to update now, or choose Later and it installs the next time you open Aperture
- The previous version is kept until the new one has started once; if it doesn't start, the old one comes back
- On macOS the new disk image opens for you to drag into Applications

**Picking up where you left off**
- Reopening a file you stopped partway through, including from Recent, asks "Resume from 14:22?" in the corner
- Aperture offers, at most once every 6 hours, to become your default video player

## Keyboard shortcuts

| Key | Action |
|---|---|
| `Space` | Play / pause |
| `Left` | Back 5 s |
| `Right` | Forward 5 s |
| `Ctrl+Left` | Back 10 s |
| `Ctrl+Right` | Forward 10 s |
| `Shift+Left` | Back 30 s |
| `Shift+Right` | Forward 30 s |
| `Home` | Back to start |
| `,` | Previous frame |
| `.` | Next frame |
| `L` | A–B loop: set A, set B, clear |
| `Ctrl+.` | Next chapter |
| `Ctrl+,` | Previous chapter |
| `[` | Slower |
| `]` | Faster |
| `=` | Normal speed |
| `Up` | Volume up |
| `Down` | Volume down |
| `M` | Mute |
| `C` | Subtitles on / off |
| `A` | Next audio track |
| `G` | Subtitles earlier (−100 ms) |
| `H` | Subtitles later (+100 ms) |
| `N` | Next in playlist |
| `P` | Previous in playlist |
| `F` | Fullscreen |
| `Ctrl+P` | Picture-in-picture |
| `S` | Screenshot |
| `Ctrl+O` | Open files |
| `Ctrl+U` | Open URL |
| `Ctrl+Alt+S` | Settings |
| `Shift+F10` | Quick options menu |
| `Esc` | Close dialog / leave fullscreen (fixed) |
| `Menu` | Quick options menu (fixed) |

Every key except the fixed ones can be changed in **Settings → Keyboard shortcuts**: click a key, press the new combination. Each key does one thing; system shortcuts such as Alt+F4 are refused.

On macOS, Ctrl means ⌘.

## Your data

Aperture keeps three small files in the platform app-data folder — `~/.local/share/Aperture/` on Linux, `%APPDATA%\Aperture\` on Windows, `~/Library/Application Support/Aperture/` on macOS:

- `history.json` — recent files and resume points
- `settings.json` — everything in Settings
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
pyinstaller --noconfirm packaging/aperture.spec             # -> dist/aperture/ (+ dist/Aperture.app on macOS)
iscc /DAppVersion=0.6.0 packaging\windows\aperture.iss      # Windows, needs Inno Setup 6
packaging/linux/build-appimage.sh 0.6.0                     # Linux, needs appimagetool
packaging/macos/build-dmg.sh 0.6.0                          # macOS, needs Xcode command-line tools
```

`build-dmg.sh` ad-hoc signs by default. Set `MACOS_SIGN_IDENTITY` to sign with a Developer ID certificate, and `APPLE_ID`, `APPLE_TEAM_ID`, `APPLE_APP_PASSWORD` to notarize.

The icon is generated from code: `python packaging/make_icons.py`.

## Releasing

1. Bump `__version__` in `src/aperture/__init__.py`.
2. Tag and push: `git tag v0.6.0 && git push origin v0.6.0`.

The release workflow tests, builds the Windows installer, the Linux AppImage and tarball, and the macOS disk image, then publishes them to a GitHub release.

### macOS signing secrets

Without these the `.dmg` is ad-hoc signed. Add them under **Settings → Secrets and variables → Actions**:

| Secret | Value |
|---|---|
| `MACOS_CERTIFICATE` | Developer ID Application certificate exported as `.p12`, base64-encoded |
| `MACOS_CERTIFICATE_PASSWORD` | Password of that `.p12` |
| `MACOS_SIGN_IDENTITY` | e.g. `Developer ID Application: Your Name (TEAMID)` |
| `APPLE_ID`, `APPLE_TEAM_ID`, `APPLE_APP_PASSWORD` | Apple account, team ID, and an app-specific password for notarization |

## Project layout

```
src/aperture/
  core/      pure Python: playlist, history, subtitle parsing, formats — fully unit-tested
  player/    Qt Multimedia: playback controller, track selection, thumbnail decoder
  theme/     design tokens and the live light/dark theme
  ui/qml/    the interface
packaging/   PyInstaller spec, Windows installer, AppImage and dmg scripts, icon generator
```
