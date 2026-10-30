# Aperture 0.4.0

A right-click menu, precise playback controls, network streams, and shortcuts you can rebind.

## Downloads
- **Windows 10/11 (x64):** `Aperture-0.4.0-windows-x64-setup.exe`
- **macOS 12+ (Apple Silicon):** `Aperture-0.4.0-macos-arm64.dmg`
- **Linux (x86-64):** `Aperture-0.4.0-x86_64.AppImage`, or `Aperture-0.4.0-linux-x64.tar.xz`

## New
- **Quick options menu:** right-click the video, or press Shift+F10 or the Menu key. Play/pause, open a file or URL, A–B loop, screenshot, playback speed, audio and subtitle tracks, fullscreen, settings.
- **A–B loop (L):** first press sets the start, second sets the end and starts looping, third clears. The loop shows on the seek bar.
- **Frame stepping (`.` / `,`):** pause and move one frame at a time.
- **Screenshots (S):** saves the current frame as a PNG in Pictures/Aperture.
- **Open URL (Ctrl+U):** play direct links and streams: http(s), HLS `.m3u8`, RTSP, RTMP and more.
- **Rebindable shortcuts:** Settings → Keyboard shortcuts lists every action. Click a key and press a new one. Each key does exactly one thing: Aperture refuses a key already in use and names the action using it. System shortcuts like Alt+F4 are blocked. Unbind any action, or reset all shortcuts at once.
- **Hardware decoding switch:** Settings → Playback. Turn it off if a video plays sound over a black picture; restart from the same page.

## Fixed
- WebM (VP8/VP9) and other files playing audio over a black picture: switch hardware decoding off for those. Every build is now also checked for the complete FFmpeg decoder set before it is packaged.

## Changed shortcuts
Each action now has one key, so a few defaults moved:
- Seek 10 s is now **Ctrl+← / Ctrl+→**, because L is the A–B loop.
- Play/pause is **Space** only (K removed), fullscreen is **F** only (F11 removed).

Rebind any of them in Settings → Keyboard shortcuts.

## Known limitations
- Frame stepping uses the file's reported frame rate; files that report none step at 30 fps.
- Thumbnails and lyrics are for local files, not streams.
- macOS builds target Apple Silicon and are ad-hoc signed unless the signing secrets are set.
