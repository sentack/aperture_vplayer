# Aperture 0.3.0

Lyrics, audio files, a rebuilt Settings, and smaller downloads.

## Downloads
- **Windows 10/11 (x64):** `Aperture-0.3.0-windows-x64-setup.exe`
- **macOS 12+ (Apple Silicon):** `Aperture-0.3.0-macos-arm64.dmg`
- **Linux (x86-64):** `Aperture-0.3.0-x86_64.AppImage`, or `Aperture-0.3.0-linux-x64.tar.xz`

## New
- **Audio files:** MP3, FLAC, M4A, Ogg, Opus, WAV and more play alongside video.
- **Synced lyrics:** Spotify-style lyrics that scroll with the song. Click a line to jump to it. Loaded from a `.lrc` / `.txt` next to the track or from the file's tags.
- **Lyrics editor:** write or paste lyrics, tap along to sync each line, then save a `.lrc` and embed it in MP3, FLAC, M4A, Ogg or Opus tags.
- **Settings modal:** General, Playback, Appearance, Subtitles and Keyboard shortcuts pages.
- **Resume prompt:** reopening a file you left partway, including from Recent, asks "Resume from 14:22?" in the bottom-right. Choose Ask, Resume or Start over in Settings → Playback.
- **Default player:** Aperture offers, at most once every 6 hours, to become your default video player. Turn it off in Settings → General.

## Fixed
- Recent files now resume where you stopped. Closing the window used to save position 0.
- Choosing a speed in Settings now changes the speed of what's playing, and it stays across files.
- Playlist: single-click selects, double-click plays.
- Windows installer no longer fails on a corrupted `Qt6WebEngineCore.dll`. Unused Qt add-ons are left out of the build.

## Smaller downloads
- Unused Qt add-ons removed from every build.
- Every release is compressed: LZMA2 ultra for the Windows installer, zstd for the AppImage, xz for the tarball, LZMA for the macOS disk image.

## Known limitations
- macOS builds target Apple Silicon and are ad-hoc signed unless the signing secrets are set.
- On Windows, "Make default" opens Settings → Default apps, where you confirm Aperture. Windows does not let apps set this themselves.
