import codecs

import pytest

from aperture.core.subtitles import Cue, CueTrack, decode, find_sidecars, load_cues, parse_cues

SRT = """1
00:00:01,000 --> 00:00:04,000
Hello <i>there</i>

2
00:00:05,500 --> 00:00:07,250
Two lines
<font color="red">& colour</font>

3
00:00:09,000 --> 00:00:08,000
Bad timing
"""

VTT = """WEBVTT
Kind: captions

NOTE this block is ignored

STYLE
::cue { color: yellow }

intro
00:01.000 --> 00:04.000 align:start position:10%
<v Narrator>Spoken <b.loud>line</b>

01:02:03.004 --> 01:02:05.000
<c.yellow>Late</c> <00:00:01.500>cue
"""


def test_parse_srt():
    cues = parse_cues(SRT)
    assert cues == [
        Cue(1000, 4000, "Hello <i>there</i>"),
        Cue(5500, 7250, "Two lines<br>&amp; colour"),
    ]


def test_parse_vtt():
    cues = parse_cues(VTT)
    assert cues == [
        Cue(1000, 4000, "Spoken <b>line</b>"),
        Cue(3_723_004, 3_725_000, "Late cue"),
    ]


def test_parse_handles_crlf_and_ass_overrides():
    cues = parse_cues("1\r\n00:00:01,000 --> 00:00:02,000\r\n{\\an8}Top <b>text</b>\r\n")
    assert cues == [Cue(1000, 2000, "Top <b>text</b>")]


def test_parse_escapes_stray_angle_brackets():
    cues = parse_cues("00:00:01.000 --> 00:00:02.000\n1 < 2 > 0\n")
    assert cues[0].text == "1 &lt; 2 &gt; 0"


def test_parse_skips_empty_cues_and_sorts():
    text = (
        "00:00:05.000 --> 00:00:06.000\nB\n\n"
        "00:00:01.000 --> 00:00:02.000\n<i></i>\n\n"
        "00:00:03.000 --> 00:00:04.000\nA\n"
    )
    assert [c.text for c in parse_cues(text)] == ["A", "B"]


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ("café".encode(), "café"),
        (codecs.BOM_UTF8 + "café".encode(), "café"),
        ("café".encode("utf-16"), "café"),
        ("café".encode("cp1252"), "café"),
    ],
)
def test_decode(data, expected):
    assert decode(data) == expected


def test_load_cues(tmp_path):
    path = tmp_path / "a.srt"
    path.write_bytes(SRT.encode("cp1252"))
    assert len(load_cues(path)) == 2


def test_find_sidecars(tmp_path):
    video = tmp_path / "Movie.mkv"
    names = ("Movie.mkv", "movie.srt", "Movie.en.srt", "Movie.fr.vtt", "Movie 2.srt", "Other.srt", "a.txt")
    for name in names:
        (tmp_path / name).touch()
    found = [p.name for p in find_sidecars(video)]
    assert found == ["movie.srt", "Movie.en.srt", "Movie.fr.vtt"]


def test_find_sidecars_missing_folder(tmp_path):
    assert find_sidecars(tmp_path / "gone" / "x.mp4") == []


class TestCueTrack:
    track = CueTrack(
        [
            Cue(1000, 3000, "a"),
            Cue(2000, 2500, "b"),
            Cue(10_000, 60_000, "long"),
            Cue(20_000, 21_000, "c"),
        ]
    )

    @pytest.mark.parametrize(
        ("position", "text"),
        [
            (0, ""),
            (1000, "a"),
            (2200, "a<br>b"),
            (2500, "a"),
            (3000, ""),
            (20_500, "long<br>c"),
            (59_999, "long"),
            (60_000, ""),
        ],
    )
    def test_text_at(self, position, text):
        assert self.track.text_at(position) == text

    def test_empty(self):
        assert CueTrack([]).text_at(1000) == ""
        assert len(CueTrack([])) == 0
