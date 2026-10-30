# Aperture 0.4.0

A right-click menu, precise playback controls, network streams, and keyboard shortcuts you can make your own.

## Downloads
- **Windows 10/11 (x64):** `Aperture-0.4.0-windows-x64-setup.exe`
- **macOS 12+ (Apple Silicon):** `Aperture-0.4.0-macos-arm64.dmg`
- **Linux (x86-64):** `Aperture-0.4.0-x86_64.AppImage`, or `Aperture-0.4.0-linux-x64.tar.xz`

## New

### Quick options menu
Right-click anywhere on the video, or press **Shift+F10** or the **Menu** key, for the things you reach for most:
- Play / pause
- Open file, open URL
- A–B loop: set start, set end, clear
- Screenshot
- Playback speed
- Audio track and subtitles
- Fullscreen
- Settings

### A–B loop — `L`
Press **L** where the loop should start and again where it should end; playback repeats that section until you press **L** a third time. The looped section is highlighted on the seek bar.

### Frame by frame — `.` and `,`
Pauses and steps one frame forward (`.`) or back (`,`), for finding the exact moment.

### Screenshots — `S`
Saves the frame on screen as a PNG in your **Pictures/Aperture** folder, named after the video and the moment it was taken.

### Open URL — `Ctrl+U`
Play direct video links and live streams, not just local files: http(s), HLS (`.m3u8`), RTSP, RTMP and more. Streams show up in Recent and remember where you stopped, like files do.

### Your own keyboard shortcuts
**Settings → Keyboard shortcuts** now lists every action. Click a key, press the combination you want, and it applies immediately.
- Each key does exactly one thing. If a key is already taken, Aperture says which action uses it instead of quietly moving it.
- System shortcuts such as Alt+F4 or Ctrl+Alt+Del can't be assigned.
- Remove a shortcut with ×, or put them all back with **Reset shortcuts**.

### Hardware decoding switch
**Settings → Playback → Hardware-accelerated decoding.** On by default. Turn it off if a video plays sound over a black picture, then press **Restart now**.

## Fixed
- **WebM and some other videos played sound with a black picture.** Turning off hardware decoding (above) makes these play normally.

## Changed shortcuts
Every action now has a single key, so three defaults moved:
- **Seek 10 seconds** is now **Ctrl+←** / **Ctrl+→** (L is the A–B loop now; J and L no longer seek).
- **Play / pause** is **Space** (K no longer pauses).
- **Fullscreen** is **F** (F11 no longer toggles fullscreen).

You can set any of them back in Settings → Keyboard shortcuts.

## Good to know
- Frame stepping follows the video's own frame rate; videos that don't report one step at 30 frames per second.
- Seek-bar thumbnails and lyrics work for files on your computer, not for streams.
- On macOS, if the app hasn't been notarized, open **System Settings → Privacy & Security** and click **Open Anyway** the first time.
