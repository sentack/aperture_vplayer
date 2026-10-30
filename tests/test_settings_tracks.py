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


def test_settings_new_fields_round_trip(tmp_path):
    path = tmp_path / "settings.json"
    settings = Settings(path)
    settings.default_volume = 0.65
    settings.default_rate = "last"
    settings.last_rate = 1.5
    settings.subtitles_auto = False
    settings.subtitle_size = "large"
    settings.save()

    loaded = Settings(path)
    assert loaded.default_volume == 0.65
    assert loaded.start_rate == 1.5
    assert loaded.subtitles_auto is False
    assert loaded.subtitle_scale == 1.25


def test_settings_fixed_rate_ignores_last_used():
    settings = Settings()
    settings.last_rate = 2.0
    settings.default_rate = 1.25
    assert settings.start_rate == 1.25


def test_settings_reads_phase_4_file(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"version": 1, "theme": "dark", "accent": "green"}))
    settings = Settings(path)
    assert (settings.theme_mode, settings.accent) == ("dark", "green")
    assert settings.default_volume == 1.0 and settings.start_rate == 1.0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("default_volume", 1.5),
        ("default_volume", True),
        ("default_rate", 3.0),
        ("default_rate", True),
        ("last_rate", 0.1),
        ("subtitles_auto", "yes"),
        ("subtitle_size", "huge"),
    ],
)
def test_settings_reject_invalid_new_values(field, value):
    with pytest.raises(ValueError):
        setattr(Settings(), field, value)


def test_settings_reset(tmp_path):
    settings = Settings(tmp_path / "s.json")
    settings.theme_mode = "light"
    settings.default_volume = 0.2
    settings.subtitle_size = "small"
    settings.reset()
    assert (settings.theme_mode, settings.default_volume, settings.subtitle_size) == (
        "system",
        1.0,
        "medium",
    )


def test_settings_resume_mode(tmp_path):
    path = tmp_path / "settings.json"
    settings = Settings(path)
    assert settings.resume_mode == "ask"
    settings.resume_mode = "never"
    settings.save()
    assert Settings(path).resume_mode == "never"
    with pytest.raises(ValueError):
        settings.resume_mode = "sometimes"


def test_decoder_choice_sets_software_decoding(monkeypatch):
    import os

    from aperture.app import apply_decoder_choice

    # A private copy: the variables must not leak into the UI tests that run later.
    environ = {k: v for k, v in os.environ.items() if not k.startswith("QT_")}
    monkeypatch.setattr(os, "environ", environ)
    apply_decoder_choice(True)
    assert "QT_FFMPEG_DECODING_HW_DEVICE_TYPES" not in os.environ
    apply_decoder_choice(False)
    assert os.environ["QT_FFMPEG_DECODING_HW_DEVICE_TYPES"] == "none"
    assert os.environ["QT_DISABLE_HW_TEXTURES_CONVERSION"] == "1"


def test_settings_shortcuts_and_hardware(tmp_path):
    path = tmp_path / "settings.json"
    settings = Settings(path)
    assert settings.shortcuts == {} and settings.hardware_decoding is True
    settings.shortcuts = {"mute": "Ctrl+M2"}
    settings.hardware_decoding = False
    settings.save()
    loaded = Settings(path)
    assert loaded.shortcuts == {"mute": "Ctrl+M2"} and loaded.hardware_decoding is False
    with pytest.raises(ValueError):
        settings.shortcuts = {"unknown_action": "X"}
