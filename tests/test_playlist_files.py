"""Playlist files (.aplaylist / .m3u8), the recent-playlists history, and new-window launches."""

from pathlib import Path

from aperture.core.files import expand_paths
from aperture.core.launch import NEW_WINDOW_FLAG, split_new_window
from aperture.core.playlist_file import (
    format_playlist,
    is_playlist,
    keep_missing,
    parse_playlist,
    read_playlist,
    write_playlist,
)
from aperture.core.playlist_history import (
    PLAYLIST_HISTORY_LIMIT,
    PlaylistHistory,
    default_name,
)


def test_is_playlist():
    assert is_playlist("a.aplaylist") and is_playlist("B.M3U8") and is_playlist("c.m3u")
    assert not is_playlist("a.mkv") and not is_playlist("https://example.com/live.m3u8")


def test_entries_inside_the_folder_are_relative(tmp_path):
    inside = tmp_path / "Season 1" / "Episode 1.mkv"
    outside = Path("/elsewhere/Other.mp4").absolute()
    stream = "https://example.com/live.m3u8"
    text = format_playlist([inside, outside, stream], tmp_path, {str(inside): 61_400})
    assert text.splitlines() == [
        "#EXTM3U",
        "#EXTINF:61,Episode 1.mkv",
        "Season 1/Episode 1.mkv",
        "#EXTINF:-1,Other.mp4",
        str(outside),
        "#EXTINF:-1,live.m3u8",
        stream,
    ]
    assert parse_playlist(text, tmp_path) == [inside, outside, stream]


def test_write_and_read_round_trip(tmp_path):
    items = [tmp_path / "a.mp4", tmp_path / "sub" / "b.mkv"]
    path = tmp_path / "Mine.aplaylist"
    write_playlist(path, items)
    assert read_playlist(path) == items
    assert not list(tmp_path.glob(".*.tmp"))  # written atomically, nothing left over


def test_reads_playlists_from_other_players(tmp_path):
    song = tmp_path / "x y.flac"
    text = b"Caf\xe9.mp3\r\n# a comment\r\n\r\n" + song.as_uri().encode() + b"\r\n"
    (tmp_path / "old.m3u").write_bytes(text)  # Latin-1, CRLF, a file:// URL
    assert read_playlist(tmp_path / "old.m3u") == [tmp_path / "Café.mp3", song]
    windows_made = "\ufeff#EXTM3U\nVideos\\clip.mp4\n"  # BOM and backslashes
    assert parse_playlist(windows_made, tmp_path) == [tmp_path / "Videos" / "clip.mp4"]


def test_hls_streams_are_not_playlists(tmp_path):
    hls = "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nseg0.ts\n"
    assert parse_playlist(hls, tmp_path) is None
    (tmp_path / "stream.m3u8").write_text(hls)
    assert expand_paths([tmp_path / "stream.m3u8"]) == [tmp_path / "stream.m3u8"]  # played as is


def test_expand_paths_opens_playlists_and_reports_what_is_gone(tmp_path):
    present = tmp_path / "a.mp4"
    present.touch()
    nested = tmp_path / "inner.aplaylist"
    nested.write_text("#EXTM3U\n")
    playlist = tmp_path / "list.aplaylist"
    playlist.write_text("a.mp4\ngone.mkv\ninner.aplaylist\nhttps://example.com/v.mp4\n")
    gone = []
    assert expand_paths([playlist], gone) == [present, "https://example.com/v.mp4"]
    assert gone == [tmp_path / "gone.mkv", nested]


def test_history_keeps_newest_first_and_merges_repeats(tmp_path):
    history = PlaylistHistory(tmp_path / "playlists.json")
    assert not history.record(["/v/one.mp4"], now=1)  # a single file is not a playlist
    assert history.record(["/v/a.mp4", "/v/b.mp4"], now=1, durations={"/v/a.mp4": 1000})
    assert history.record(["/w/c.mp4", "/w/d.mp4"], now=2)
    history.record(["/v/a.mp4", "/v/b.mp4"], now=3, name="Mine", saved="/v/Mine.aplaylist")
    names = [(e.name, e.used) for e in history.entries]
    assert names == [("Mine", 3), ("w", 2)]
    assert history.entries[0].durations == {"/v/a.mp4": 1000}  # kept across the merge
    history.save()
    loaded = PlaylistHistory(tmp_path / "playlists.json")
    assert loaded.entries == history.entries
    assert loaded.entries[0].saved == "/v/Mine.aplaylist"


def test_history_is_bounded_and_survives_bad_files(tmp_path):
    history = PlaylistHistory()
    for n in range(PLAYLIST_HISTORY_LIMIT + 5):
        history.record([f"/v/{n}a.mp4", f"/v/{n}b.mp4"], now=n)
    assert len(history.entries) == PLAYLIST_HISTORY_LIMIT
    history.remove(0)
    assert history.entries[0].used == PLAYLIST_HISTORY_LIMIT + 3
    bad = tmp_path / "playlists.json"
    bad.write_text('{"playlists": [{"items": []}, {"items": [1]}, "x", {"items": ["/a", "/b"]}]}')
    assert [e.items for e in PlaylistHistory(bad).entries] == [("/a", "/b")]


def test_default_names():
    season = Path("/shows/Season 2")
    assert default_name([season / "e1.mkv", season / "e2.mkv"]) == "Season 2"
    assert default_name([Path("/a/x.mp4"), Path("/b/y.mp4"), Path("/b/z.mp4")]) == "x.mp4 + 2 more"


def test_new_window_flag_is_split_off():
    assert split_new_window([NEW_WINDOW_FLAG, "a.mp4"]) == (True, ["a.mp4"])
    assert split_new_window(["a.mp4"]) == (False, ["a.mp4"])


def test_restart_and_new_windows_start_the_appimage_file(monkeypatch):
    from aperture.app import restart_command

    monkeypatch.setenv("APPIMAGE", "/home/me/Aperture-0.8.0-x86_64.AppImage")
    assert restart_command() == ("/home/me/Aperture-0.8.0-x86_64.AppImage", [])
    monkeypatch.delenv("APPIMAGE")
    program, arguments = restart_command()
    assert arguments == ["-m", "aperture"]  # from source in tests


def test_writing_back_keeps_entries_that_did_not_open():
    a, gone, b, c, later = (Path(f"/v/{n}.mkv") for n in ("a", "gone", "b", "c", "later"))
    entries = [gone, a, b, later]  # as listed in the file; gone and later didn't open
    assert keep_missing(entries, [a, b], [a, b, c]) == [gone, a, b, later, c]
    assert keep_missing(entries, [a, b], [b]) == [gone, b, later]  # a removed by the user
    assert keep_missing(entries, [a, b], [a]) == [gone, a, later]  # b removed: after a
    assert keep_missing(entries, [a, b], [c]) == [gone, later, c]  # both removed
