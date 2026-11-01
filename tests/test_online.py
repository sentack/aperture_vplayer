"""Online lyrics (LRCLIB) and subtitle (OpenSubtitles) search: parsing, without a network."""

import pytest

from aperture.core.online import (
    describe_failure,
    guess_title_year,
    lrclib_query,
    opensubtitles_query,
    parse_download_link,
    parse_lrclib,
    parse_subtitle_search,
    subtitle_path,
)

LRCLIB = [
    {
        "id": 1,
        "trackName": "Song",
        "artistName": "Band",
        "albumName": "Live",
        "duration": 300.0,
        "instrumental": False,
        "plainLyrics": "first\nsecond",
        "syncedLyrics": None,
    },
    {
        "id": 2,
        "trackName": "Song",
        "artistName": "Band",
        "albumName": "Studio",
        "duration": 214.0,
        "instrumental": False,
        "plainLyrics": "first\nsecond",
        "syncedLyrics": "[00:01.00]first\n[00:03.00]second",
    },
    {"id": 3, "trackName": "Interlude", "instrumental": True, "plainLyrics": None},
    "not an object",
]


def test_lrclib_query_drops_empty_fields():
    assert lrclib_query(" Song ", "Band", "") == {"track_name": "Song", "artist_name": "Band"}


def test_lrclib_results_put_synced_and_closest_length_first():
    results = parse_lrclib(LRCLIB, duration_s=212)
    assert [(r.album, r.synced) for r in results] == [("Studio", True), ("Live", False)]
    assert results[0].text.startswith("[00:01.00]first")
    assert results[1].text == "first\nsecond"


@pytest.mark.parametrize("data", [None, {}, "x", [{"trackName": "no lyrics"}]])
def test_lrclib_odd_answers_give_no_results(data):
    assert parse_lrclib(data) == []


@pytest.mark.parametrize(
    ("name", "title", "year"),
    [
        ("The.Movie.2014.1080p.BluRay.x264.mkv", "The Movie", "2014"),
        ("[Group] Some Show S01E02 720p.mkv", "Some Show", ""),
        ("Inception (2010).mp4", "Inception", "2010"),
        ("Blade Runner 2049 (2017) 4K HDR.mkv", "Blade Runner 2049", "2017"),
        ("2001.A.Space.Odyssey.1968.720p.mkv", "2001 A Space Odyssey", "1968"),
        ("2012.mkv", "2012", ""),
        ("my_holiday_video.mp4", "my holiday video", ""),
    ],
)
def test_title_and_year_guessed_from_file_names(name, title, year):
    assert guess_title_year(name) == (title, year)


def test_opensubtitles_query():
    assert opensubtitles_query("Movie", "2014", "EN, fr") == {
        "query": "Movie",
        "year": "2014",
        "languages": "en,fr",
    }
    assert opensubtitles_query("Movie", "soon", "") == {"query": "Movie"}


SEARCH = {
    "data": [
        {
            "attributes": {
                "language": "en",
                "release": "Movie.2014.720p",
                "download_count": 10,
                "files": [{"file_id": 11, "file_name": "a.srt"}],
            }
        },
        {
            "attributes": {
                "language": "en",
                "release": "Movie.2014.1080p",
                "download_count": 900,
                "hearing_impaired": True,
                "files": [{"file_id": 22, "file_name": "b.srt"}],
            }
        },
        {"attributes": {"language": "en", "files": []}},  # nothing to download
        {"attributes": {"files": [{"file_id": "33"}]}},  # malformed id
    ]
}


def test_subtitle_results_most_downloaded_first():
    results = parse_subtitle_search(SEARCH)
    assert [(r.file_id, r.downloads, r.hearing_impaired) for r in results] == [
        (22, 900, True),
        (11, 10, False),
    ]
    assert parse_subtitle_search({"data": "x"}) == parse_subtitle_search(None) == []


def test_download_link_must_be_https():
    assert parse_download_link({"link": "https://dl.example/x.srt"}) == "https://dl.example/x.srt"
    assert parse_download_link({"link": "http://dl.example/x.srt"}) is None
    assert parse_download_link([]) is None


def test_subtitle_path_matches_autoload_names_and_never_overwrites(tmp_path):
    video = tmp_path / "Movie.mkv"
    first = subtitle_path(video, "en")
    assert first.name == "Movie.en.srt"
    first.touch()
    assert subtitle_path(video, "en").name == "Movie.en.2.srt"
    assert subtitle_path(video, "../../x").name == "Movie.x.srt"  # no path tricks


@pytest.mark.parametrize(
    ("status", "network", "words"),
    [
        (None, True, "Couldn't reach"),
        (401, True, "API key"),
        (406, True, "download limit"),
        (429, True, "too many"),
        (503, True, "unavailable"),
        (404, True, "didn't answer"),
    ],
)
def test_failures_explain_themselves(status, network, words):
    assert words in describe_failure("OpenSubtitles", status, network)
