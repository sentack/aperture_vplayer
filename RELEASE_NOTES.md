# Aperture 0.8.0

Playlists you can keep. Save a playlist and open it again later, pick up any of your recent playlists with one click, and see how long every item is. Aperture also stops guessing when you open more files while something is playing: it asks.

## Downloads
- **Windows 10/11 (x64):** `Aperture-0.8.0-windows-x64-setup.exe`
- **macOS 12+ (Apple Silicon):** `Aperture-0.8.0-macos-arm64.dmg`
- **Linux (x86-64):** `Aperture-0.8.0-x86_64.AppImage`, or `Aperture-0.8.0-linux-x64.tar.xz`

Already on 0.7.0? Open **Settings → About → Check for updates**.

## New

### Save and open playlists
The playlist panel has two new buttons, **Open playlist** and **Save playlist**, next to Add.
- **Save playlist** writes the current playlist to a file. Two formats are offered:
  - **Aperture playlist (`.aplaylist`)**, the default. Double-click it later and it opens in Aperture.
  - **M3U playlist (`.m3u8`)**, for playing the same list in other players such as VLC, mpv or foobar2000.
- Files in the same folder as the playlist, or in folders inside it, are saved by their place relative to the playlist. Move or copy the whole folder, to another drive or another computer, and the playlist still finds them. Files elsewhere are saved with their full path, and network streams as their address.
- **Open playlist** loads a saved playlist in place of the current one. It opens `.aplaylist` files, and `.m3u` / `.m3u8` playlists made by other players, including ones saved on Windows and older playlists in other text encodings.
- Playlist files can also be opened from your file manager, dropped onto the window, or added with **Add**, which appends their items to the playlist instead of replacing it.
- Files a playlist lists that no longer exist are skipped, and a message says how many: "Not found: 3 files from the playlist". The rest play as usual.
- Live-stream `.m3u8` links (HLS) are not playlists: they still play as streams, as before.

### `.aplaylist` opens in Aperture
Aperture playlists get their own file type, so double-clicking one opens it in Aperture on every platform:
- **Windows:** the installer registers `.aplaylist`. This happens whether or not you chose to associate video files.
- **macOS:** Aperture declares `.aplaylist` as its own type, so Finder opens it in Aperture.
- **Linux:** Aperture registers the type with your desktop the first time it starts, if it has a desktop entry. Running the AppImage without one? The first time you save a playlist, Aperture adds its desktop entry and registers the type then.

Aperture only claims `.aplaylist`. Which app opens your `.m3u` files is left unchanged.

### Recent playlists
Your playlists are remembered, so you can go back to one without saving it first.
- Press the **clock button** in the playlist panel to see them, newest first. Each shows its name, number of items, total length and when you last used it, for example **Season 2**, "10 items · 7:24:10 · Yesterday". Saved ones are marked **saved**.
- Click one to open it again. Hover it and press **×** to remove it from the list, or use the trash button to clear the whole list.
- A playlist is remembered when you save it or open a playlist file, and whenever a playlist of two or more items is replaced, cleared or still open when you quit Aperture.
- Unsaved playlists are named after the folder their files share ("Season 2"), or after their first file ("Intro.mp4 + 4 more").
- Up to 12 are kept. When the playlist is empty, the recent playlists show in the panel by themselves.

### Each item's length
Every row of the playlist now shows how long it is (`3:42`), and the panel's header shows the number of items and the total length of the whole playlist (`12 · 48:10`). Hovering a row shows its × remove button in place of the length.

Lengths are read in the background, so a long playlist opens just as fast as before and its lengths fill in a moment later. Network streams, and files that can't be read, show no length. The total appears once every length is known.

### Opening files while something is playing
Before, opening a file from your file manager while Aperture was playing replaced the whole playlist. Now Aperture asks what you meant:
- **Add to current playlist** appends the files to the end, and what's playing carries on.
- **Open in new window** starts a separate Aperture window for them, with its own playlist. Files you open after that still go to your first window.
- **Cancel** opens nothing.

The question lists the files you opened. Several files from one selection are asked about together, once. This applies to files coming from outside Aperture, such as your file manager, **Open with**, or Finder. Inside Aperture, **Open file** still replaces the playlist and **Add** still appends to it.

If you turned off **Settings → General → Windows → Open files in the same window**, nothing changes: every file you open gets its own window, without a question.

## Fixed
- **Linux AppImage: restarting from Settings.** A setting that needs a restart could fail to start Aperture again when running the AppImage. It now restarts the AppImage you started it from.

## Good to know
- An `.aplaylist` file is plain text, in the same format as an `.m3u8` playlist. It can be opened in a text editor, or renamed to `.m3u8` to use it in another player.
- Saving a playlist never moves or changes the files in it.
- Recent playlists are stored on this computer only, in Aperture's data folder, with the rest of your settings.
