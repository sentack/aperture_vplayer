import struct

import pytest

from aperture.core.lyrics import (
    LyricLine,
    LyricsTrack,
    find_lyrics,
    format_lrc,
    format_stamp,
    parse_lyrics,
)

LRC = """[ar:Someone]
[ti:A Song]
[offset:+250]
[00:12.00]First line
[00:15.50][01:02.5]Chorus
[00:20.123]
[00:18]Third
"""


def test_parse_synced_lrc():
    lines = parse_lyrics(LRC)
    assert lines == [
        LyricLine(11_750, "First line"),
        LyricLine(15_250, "Chorus"),
        LyricLine(17_750, "Third"),
        LyricLine(19_873, ""),
        LyricLine(62_250, "Chorus"),
    ]


def test_parse_plain_lyrics_keeps_order():
    assert parse_lyrics("Line one\n\n  Line two \n") == [
        LyricLine(None, "Line one"),
        LyricLine(None, "Line two"),
    ]


def test_negative_offset_never_goes_below_zero():
    assert parse_lyrics("[offset:-500]\n[00:00.20]a\n[00:01.00]b")[0] == LyricLine(700, "a")
    assert parse_lyrics("[offset:900]\n[00:00.20]a")[0].time_ms == 0


@pytest.mark.parametrize(
    ("ms", "stamp"), [(0, "[00:00.00]"), (62_250, "[01:02.25]"), (6_000_999, "[100:00.99]")]
)
def test_format_stamp(ms, stamp):
    assert format_stamp(ms) == stamp


def test_format_round_trip():
    # LRC stores centiseconds, so start from centisecond stamps.
    lines = parse_lyrics(LRC.replace("[offset:+250]\n", "").replace("20.123", "20.12"))
    text = format_lrc(lines, {"ti": "A Song", "ar": ""})
    assert text.startswith("[ti:A Song]\n[00:12.00]First line\n")
    assert parse_lyrics(text) == lines


def test_format_unsynced():
    assert format_lrc([LyricLine(None, "a"), LyricLine(None, "b")]) == "a\nb\n"


def test_find_lyrics_prefers_lrc(tmp_path):
    audio = tmp_path / "Song.mp3"
    for name in ("Song.mp3", "song.TXT", "Song.lrc", "Other.lrc"):
        (tmp_path / name).touch()
    assert find_lyrics(audio).name == "Song.lrc"
    (tmp_path / "Song.lrc").unlink()
    assert find_lyrics(audio).name == "song.TXT"
    assert find_lyrics(tmp_path / "Nothing.mp3") is None


def test_track_index():
    track = LyricsTrack(parse_lyrics("[00:01.00]a\n[00:03.00]b\n[00:05.00]c"))
    assert track.synced
    assert [track.index_at(t) for t in (0, 999, 1000, 4000, 9000)] == [-1, -1, 0, 1, 2]


def test_unsynced_track_has_no_current_line():
    track = LyricsTrack(parse_lyrics("a\nb"))
    assert not track.synced and track.index_at(10_000) == -1


# --- embedded tags --------------------------------------------------------------------------

mutagen = pytest.importorskip("mutagen")


def minimal_flac(path):
    """fLaC marker plus a single STREAMINFO block: enough for tag editors."""
    packed = (44_100 << 44) | (1 << 41) | (15 << 36)  # 44.1 kHz, stereo, 16-bit, 0 samples
    info = struct.pack(">HH", 4096, 4096) + bytes(6) + packed.to_bytes(8, "big") + bytes(16)
    path.write_bytes(b"fLaC" + bytes([0x80, 0, 0, len(info)]) + info)


def test_embed_and_read_mp3(tmp_path):
    from aperture.core.lyrics_tags import embed, read_embedded

    path = tmp_path / "a.mp3"
    path.write_bytes(bytes(512))
    assert read_embedded(path) is None
    embed(path, "[00:01.00]hello")
    embed(path, "[00:01.00]again")
    assert read_embedded(path) == "[00:01.00]again"


def test_embed_and_read_flac(tmp_path):
    from aperture.core.lyrics_tags import embed, read_embedded

    path = tmp_path / "a.flac"
    minimal_flac(path)
    embed(path, "plain words")
    assert read_embedded(path) == "plain words"


def test_embed_rejects_unsupported(tmp_path):
    from aperture.core.lyrics_tags import LyricsTagError, embed

    path = tmp_path / "a.wav"
    path.write_bytes(bytes(64))
    with pytest.raises(LyricsTagError):
        embed(path, "x")
    with pytest.raises(LyricsTagError):
        embed(tmp_path / "broken.flac", "x")
