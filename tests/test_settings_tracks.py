import json

import pytest

from aperture.core.storage import read_json, write_json
from aperture.core.thumbnails import END_GUARD_MS, MIN_STEP_MS, thumbnail_bucket
from aperture.core.tracks import track_label
from aperture.settings import Settings

HOUR = 3_600_000


@pytest.mark.parametrize(
    ("index", "title", "language", "label"),
    [
        (0, "Commentary", "English", "English · Commentary"),
        (0, None, "English", "English"),
        (1, "Director", None, "Director"),
        (1, "  ", "", "Track 2"),
        (0, "english", "English", "English"),
    ],
)
def test_track_label(index, title, language, label):
    assert track_label(index, title, language) == label


@pytest.mark.parametrize(
    ("position", "duration", "bucket"),
    [
        (0, HOUR, 0),
        (HOUR // 120 * 10 + 1, HOUR, HOUR // 120 * 10),
        (HOUR // 120 * 10 + HOUR // 240 + 1, HOUR, HOUR // 120 * 11),
        (2_900, 60_000, MIN_STEP_MS * 1),
        (3_100, 60_000, MIN_STEP_MS * 2),
        (-50, 60_000, 0),
        (HOUR * 2, HOUR, HOUR - END_GUARD_MS),
        (5_100, 0, 6_000),
    ],
)
def test_thumbnail_bucket(position, duration, bucket):
    assert thumbnail_bucket(position, duration) == bucket


def test_storage_round_trip(tmp_path):
    path = tmp_path / "deep" / "x.json"
    write_json(path, {"a": [1, "é"]})
    assert read_json(path) == {"a": [1, "é"]}
    assert not list(path.parent.glob(".x-*"))


def test_storage_read_missing_and_corrupt(tmp_path):
    assert read_json(tmp_path / "none.json") is None
    bad = tmp_path / "bad.json"
    bad.write_text("[")
    assert read_json(bad) is None


def test_settings_defaults_and_round_trip(tmp_path):
    path = tmp_path / "settings.json"
    settings = Settings(path)
    assert (settings.theme_mode, settings.accent) == ("system", "blue")
    settings.theme_mode = "light"
    settings.accent = "coral"
    settings.save()
    loaded = Settings(path)
    assert (loaded.theme_mode, loaded.accent) == ("light", "coral")


def test_settings_ignore_invalid_stored_values(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"theme": "neon", "accent": "pink"}))
    settings = Settings(path)
    assert (settings.theme_mode, settings.accent) == ("system", "blue")


@pytest.mark.parametrize(("field", "value"), [("theme_mode", "neon"), ("accent", "pink")])
def test_settings_reject_invalid_values(field, value):
    with pytest.raises(ValueError):
        setattr(Settings(), field, value)
