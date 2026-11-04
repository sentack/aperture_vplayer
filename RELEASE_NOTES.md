# Aperture 0.9.0

Audio boost works again, the play button's icon sits in the middle of its circle, the window opens at the size you left it, and changes to a playlist file can be saved back into it, by hand or automatically.

## Downloads
- **Windows 10/11 (x64):** `Aperture-0.9.0-windows-x64-setup.exe`
- **macOS 12+ (Apple Silicon):** `Aperture-0.9.0-macos-arm64.dmg`
- **Linux (x86-64):** `Aperture-0.9.0-x86_64.AppImage`, or `Aperture-0.9.0-linux-x64.tar.xz`

Already on 0.8.0? Open **Settings → About → Check for updates**.

## Fixed

### Audio boost no longer silences the sound
Choosing 125%, 150% or 200% under **Audio boost** while something was playing cut the sound off completely, instead of making it louder. Boost only worked if it was already on before a file started.

Boost now works whenever you turn it on: the sound gets louder straight away, keeps playing into the next file, and goes back to normal at 100%. Loud parts are still rounded off rather than crackling.

### Icons are centered in their buttons
The play and pause icons sat a few pixels right of and below the middle of the round play button. The same small offset affected every icon button in the window: the control bar, the title bar, the playlist and Settings. Every icon is now centered. The play triangle sits a touch to the right of exact center on purpose, so it looks balanced.

## New

### The window opens at the size you left it
Aperture used to open at the same large size every time, covering most of the screen. Now:
- It opens at the size you last resized it to, and keeps that size until you resize it again.
- If you left it maximized, it opens maximized. Un-maximizing goes back to your size.
- Fullscreen and the picture-in-picture window don't change the size it comes back to.
- A size saved on a bigger monitor is shrunk to fit a smaller screen.
- On the very first launch, the window takes up at most 85% of the screen.

**Settings → Reset to defaults** keeps the window size, since it isn't a setting.

### Save changes back to a playlist file
When the playlist came from a file (you opened an `.aplaylist` or `.m3u8`, saved one, or reopened a saved one from **Recent playlists**), the playlist panel shows the file's name under its header.
- Add or remove files and a **Save** button appears next to the name. Press it to write the changes into that same file. It then shows **Saved**.
- **Save playlist as** (the arrow button) still saves to a new file of your choice.
- Files the playlist lists but that aren't there right now, for example on a drive that isn't plugged in, are kept in the file, in their place, when you save. They come back once the drive does.

### Autosave for playlists
Prefer not to press Save? Turn on **Settings → General → Playlists → Save playlist changes automatically**. Adding or removing files then saves them into the playlist file right away, and the playlist shows **Saves automatically**. Adding a whole folder is saved once, not once per file. Turning it on with changes waiting saves them at once.

Autosave is off by default and only ever writes to a playlist file you opened or saved yourself.

## Changed
- **Reopening a saved playlist from Recent playlists** opens its file as it is now, so changes made to it elsewhere show up, and your next changes can be saved back into it.
