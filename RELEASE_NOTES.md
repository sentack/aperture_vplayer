# Aperture 0.6.0

Picture-in-picture, chapters, subtitle timing, audio boost, and a smaller Linux download.

## Downloads
- **Windows 10/11 (x64):** `Aperture-0.6.0-windows-x64-setup.exe`
- **macOS 12+ (Apple Silicon):** `Aperture-0.6.0-macos-arm64.dmg`
- **Linux (x86-64):** `Aperture-0.6.0-x86_64.AppImage`, or `Aperture-0.6.0-linux-x64.tar.xz`

Already on 0.5.0? Open **Settings → About → Check for updates**.

## New

### Picture-in-picture — `Ctrl+P`
A small floating window that stays on top while you work in other apps. It now takes the shape of the video, so there are no black bars around it. Drag it anywhere; double-click or press the restore button to return to the full window.

### Chapters — `Ctrl+.` and `Ctrl+,`
Movies, lectures and long videos with chapters (MKV, WebM, MP4) show each chapter as a tick on the seek bar, and hovering the bar shows the chapter's name. Jump to the next chapter, or back to the start of the current one (press again for the one before). A **Chapters** list is in the right-click menu.

### Subtitle delay — `G` and `H`
Subtitles out of sync? Press **G** to show them earlier or **H** to show them later, 0.1 s at a time. The options menu shows the current delay and resets it. Each new file starts at no delay.

### Audio boost
For quiet recordings: the options menu offers **125%, 150% or 200%**. Loud passages are smoothed instead of clipping, so a boost doesn't crackle.

### Smaller Linux download
The AppImage is now compressed with xz, so it downloads faster, including through in-app updates. The first launch can take a moment longer while it unpacks.

## Codecs
H.264, HEVC (H.265), VP8 and VP9 video are confirmed to play before every release. **AV1** plays when your graphics hardware decodes AV1 (most graphics cards and Apple chips from roughly 2021 onward). On older hardware, AV1 videos may not show a picture.

## Changed shortcuts
- **Picture-in-picture** (formerly Mini player) is now **Ctrl+P**; `I` no longer opens it.
- **Settings** moved to **Ctrl+Alt+S**, because `Ctrl+,` is now Previous chapter.

Change any of them in Settings → Keyboard shortcuts.

## Good to know
- Subtitle delay adjusts subtitle files (`.srt`, `.vtt`). Subtitles built into the video keep their own timing.
- Chapters are read from the chapter list most tools write. Some audiobooks store chapters differently and won't show them yet.
