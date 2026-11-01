# Aperture 0.7.0

Fixes for the problems that got in the way every day: dead shortcuts, hidden window buttons, lyrics that scrolled along with the playlist, and one window per file. It also adds repeat and shuffle, online lyrics and subtitle search, and lyrics saved into your music files.

## Downloads
- **Windows 10/11 (x64):** `Aperture-0.7.0-windows-x64-setup.exe`
- **macOS 12+ (Apple Silicon):** `Aperture-0.7.0-macos-arm64.dmg`
- **Linux (x86-64):** `Aperture-0.7.0-x86_64.AppImage`, or `Aperture-0.7.0-linux-x64.tar.xz`

Already on 0.6.0? Open **Settings → About → Check for updates**.

## Fixed

### Keyboard shortcuts no longer stop working
After you changed a shortcut in **Settings → Keyboard shortcuts**, every shortcut (pause, seeking, volume, all of them) stopped responding until Aperture was restarted. The same happened if you clicked a key to change it and then pressed **Reset shortcuts** or **×** instead of a key. Shortcuts now keep working, whatever you do in Settings.

### Window buttons are visible on every video
Minimize, maximize and close could disappear against the video, especially dark buttons on a dark film in the light theme. While a video plays they now sit on a dark, see-through backing with white icons, readable on bright and dark scenes alike, in either theme. The "APERTURE" title and the fade along the top of the window follow the same rule.

### Scrolling stays where your pointer is
Scrolling the playlist no longer scrolls the lyrics behind it once the playlist reaches its end. The same goes for the control bar, the prompt cards and every dialog: scrolling over them never moves anything underneath.

### Opening several files gives one window, not one per file
Selecting several videos in your file manager and opening them used to start a separate Aperture for each file, which happened every time on Windows. Now they open together in one window, as one playlist (see **One window** below).

## New

### One window, one playlist
- Files you open while Aperture is running play in the open window, which comes to the front (on Linux with Wayland, the system may highlight it in the taskbar instead). No second window appears.
- Several files opened together, for example a multi-file selection in Explorer, Finder or your Linux file manager, become **one playlist sorted by name** (Episode 2 before Episode 10). They start with the first.
- A file opened a few seconds later replaces the playlist and plays straight away, just as before.
- Starting Aperture again while it is open brings the existing window to the front.
- **Prefer separate windows?** Turn off **Settings → General → Windows → Open files in the same window**. The change applies immediately, no restart needed.

### Repeat and shuffle — `R` and `Shift+S`
Two new buttons next to Stop in the control bar. Each lights up in your accent colour while it's on.
- **Repeat** cycles **Off → All → One** with each click, or with `R`:
  - **Off:** playback stops after the last item.
  - **All:** the playlist starts over from the top after the last item; Previous on the first item goes to the last.
  - **One:** the current file plays again whenever it reaches its end. Next and Previous still move through the playlist.
- **Shuffle** (`Shift+S`) plays every item once, in random order, starting from the one playing now. Previous retraces the shuffled order. With Repeat All on, each new round is reshuffled. Files you add while shuffling are mixed into what's still to come. Turning shuffle off goes back to the playlist's own order.
- Opening files with shuffle on starts from a random one of them.
- A short message confirms each change ("Repeat one", "Shuffle on").
- Both settings are remembered the next time you open Aperture. **Reset to defaults** turns them off.

### Search for lyrics online
For songs without lyrics, right-click and choose **Search for lyrics online…**, or press **Search online** on the lyrics panel.
- Lyrics come from **LRCLIB**, a free, open lyrics library. No account or key needed.
- The search form starts with the song's **title, artist and album from its tags**, or from a file name like "Artist - Title". Tags are often wrong or missing, so every field can be edited before you search; only the title is required.
- Results show the title, artist, album and length, with a **Synced** or **Plain** badge. Synced lyrics come first, then the versions whose length is closest to your file, so the right recording is usually at the top.
- Pick a result and its lyrics show immediately and are saved into the song (see below). Synced lyrics scroll with the music, as before.

### Lyrics are saved inside your music files
Lyrics now travel with the song instead of living in a separate file next to it. This applies whether you found them online or typed and synced them yourself in the lyrics editor:
- **MP3:** synced lyrics with their timing (ID3 SYLT), plus the plain words (USLT) for players that can't show synced lyrics.
- **FLAC, Ogg and Opus:** a LYRICS tag.
- **M4A:** the standard lyrics tag.
- **WAV and other formats that can't hold lyrics:** a `.lrc` file next to the song, as before.

The lyrics editor's two save buttons ("Save and embed", "Save .lrc only") are now one: **Save to file**.

When a song opens, lyrics stored in the file itself are shown first. If it has none, a `.lrc` or `.txt` next to it is used. Lyrics saved by earlier versions of Aperture still show.

### Search for subtitles online
Right-click a video and choose **Search for subtitles online…**
- Subtitles come from **OpenSubtitles**.
- The form starts with the **title and year guessed from the file name**. For example, `Blade.Runner.2049.2017.2160p.mkv` becomes "Blade Runner 2049" and 2017. Release tags such as 1080p, BluRay or x264 are ignored. The **language** starts as your system's language. All three can be changed; several languages are separated by commas (`en,fr`).
- Results list the release name, language and number of downloads, most downloaded first, and mark subtitles for the hearing impaired.
- Pick one and it is downloaded, saved **next to the video** as `Name.en.srt`, and shown right away. Aperture loads that file automatically the next time you play the video. An existing subtitle file is never overwritten: a number is added instead. If the video's folder can't be written to, the subtitle is kept in Aperture's own data folder and still shown.

**One-time setup:** OpenSubtitles requires a personal API key.
1. Create a free account at opensubtitles.com.
2. In your profile, open **API consumers**, create one and copy its key.
3. In Aperture, open **Settings → Subtitles → Subtitle search**, paste the key and press **Save key**.

Until a key is saved, the search explains this and offers a button that opens the right Settings page. Your key stays on this computer and is sent only to OpenSubtitles. **Reset to defaults** keeps it; **Remove** deletes it.

### When a search doesn't work
Searches depend on outside services, so every outcome gets a plain message in the dialog instead of an error:
- **No results:** "No lyrics found" or "No subtitles found", with a hint to try fewer words or another language.
- **No connection:** "Couldn't reach LRCLIB" or "Couldn't reach OpenSubtitles".
- **The service is down:** "unavailable right now, try again later".
- **Too many searches in a short time:** try again in a minute.
- **A wrong key:** OpenSubtitles refused the API key, check it in Settings.
- **Today's download limit used up:** the free OpenSubtitles tier allows a limited number of downloads per day; try again tomorrow.

A search in progress can be cancelled at any time, and closing the dialog stops it.

### Scrollbars in Settings and the playlist
Long Settings pages, such as Keyboard shortcuts and About, and long playlists now show a slim scrollbar that widens under the pointer, so nothing is cut off at the bottom.

## New shortcuts
- `R`: Repeat (off, all, one)
- `Shift+S`: Shuffle on / off. `S` stays Screenshot.

**If you had set `R` or `Shift+S` for something else yourself:** after updating, that action goes back to its default key, and `R` / `Shift+S` start repeat and shuffle. To keep your own choice, open **Settings → Keyboard shortcuts**, free the key from Repeat or Shuffle with ×, then click your action and press the key again. This will be smoother in a later release.

Every shortcut can be changed in Settings → Keyboard shortcuts.

## Good to know
- Online search needs an internet connection. Only what you typed in the search form is sent (and, to OpenSubtitles, your API key). The files you search for stay on your computer.
- Searching for subtitles is offered for video files, and searching for lyrics for audio files. Neither is offered for network streams, since they have no file to save to.
- Subtitle downloads are `.srt` files, which work with subtitle delay (`G` / `H`) and text size like any other subtitle file.
