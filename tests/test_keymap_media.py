from datetime import datetime
from pathlib import Path

import pytest

from aperture.core.keymap import ACTIONS, Action, BindingError, Keymap, is_reserved
from aperture.core.media import (
    display_name,
    display_stem,
    folder_label,
    frame_ms,
    is_url,
    kind_label,
    parse_stream_url,
    screenshot_name,
)

# --- keymap -------------------------------------------------------------------------------


def test_defaults_are_one_to_one_and_allowed():
    keys = [a.default.casefold() for a in ACTIONS]
    assert len(keys) == len(set(keys))
    assert len({a.id for a in ACTIONS}) == len(ACTIONS)
    assert not any(is_reserved(a.default) for a in ACTIONS)


def test_phase_8_defaults():
    keymap = Keymap()
    assert keymap.key("ab_loop") == "L"
    assert keymap.key("frame_next") == "." and keymap.key("frame_previous") == ","
    assert keymap.key("screenshot") == "S" and keymap.key("open_url") == "Ctrl+U"


def test_rebind_rejects_duplicate_with_clear_message():
    keymap = Keymap()
    with pytest.raises(BindingError) as error:
        keymap.bind("mute", "Ctrl+U")
    assert str(error.value) == (
        "Ctrl+U is already used for Open URL. Choose a different combination or unbind it first."
    )
    assert keymap.key("mute") == "M" and keymap.key("open_url") == "Ctrl+U"  # nothing stolen


def test_duplicate_check_ignores_case():
    with pytest.raises(BindingError):
        Keymap().bind("mute", "ctrl+u")


def test_rebind_after_unbinding_the_owner():
    keymap = Keymap()
    keymap.unbind("open_url")
    keymap.bind("mute", "Ctrl+U")
    assert keymap.key("mute") == "Ctrl+U" and keymap.key("open_url") == ""
    assert keymap.owner("Ctrl+U") == "mute"


def test_rebinding_to_own_key_is_fine():
    keymap = Keymap()
    keymap.bind("mute", "M")
    assert keymap.overrides() == {}


@pytest.mark.parametrize("key", ["Alt+F4", "ctrl+alt+del", "Ctrl+Alt+F3", "Esc", "Menu", "Ctrl+Q"])
def test_reserved_keys_are_rejected(key):
    with pytest.raises(BindingError, match="reserved"):
        Keymap().bind("mute", key)


def test_unknown_action():
    with pytest.raises(BindingError):
        Keymap().bind("launch_rockets", "R")


def test_overrides_round_trip_and_reset():
    keymap = Keymap()
    keymap.bind("screenshot", "Ctrl+Shift+S")
    keymap.unbind("mini_player")
    saved = keymap.overrides()
    assert saved == {"mini_player": "", "screenshot": "Ctrl+Shift+S"}
    assert Keymap(saved).keys() == keymap.keys()
    keymap.reset()
    assert keymap.overrides() == {}


def test_bad_saved_overrides_fall_back_to_defaults():
    keymap = Keymap({"mute": "Ctrl+U", "nope": "X", "screenshot": "Alt+F4", "slower": "Ctrl+["})
    assert keymap.key("mute") == "M"
    assert keymap.key("screenshot") == "S"
    assert keymap.key("slower") == "Ctrl+["


def test_action_is_frozen():
    with pytest.raises(AttributeError):
        ACTIONS[0].default = "X"  # type: ignore[misc]
    assert isinstance(ACTIONS[0], Action)


# --- media sources ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "url"),
    [
        ("https://example.com/a.mp4", "https://example.com/a.mp4"),
        ("  example.com/live/stream.m3u8 ", "https://example.com/live/stream.m3u8"),
        ("rtsp://10.0.0.5:554/cam", "rtsp://10.0.0.5:554/cam"),
        ("http://localhost:8080/x", "http://localhost:8080/x"),
        ("file:///etc/passwd", None),
        ("javascript:alert(1)", None),
        ("not a url", None),
        ("hello", None),
        ("", None),
    ],
)
def test_parse_stream_url(text, url):
    assert parse_stream_url(text) == url


def test_is_url():
    assert is_url("https://example.com/a.mp4")
    assert not is_url(Path("/videos/a.mp4")) and not is_url("/videos/a.mp4")


def test_display_helpers():
    url = "https://cdn.example.com/shows/My%20Show.mkv?token=1"
    assert display_name(url) == "My Show.mkv"
    assert display_stem(url) == "My Show"
    assert kind_label(url) == "MKV"
    assert folder_label(url) == "cdn.example.com"
    assert display_name("https://example.com/") == "example.com"
    assert kind_label("rtsp://cam.local/live") == "STREAM"
    assert display_stem(Path("/v/Movie.mp4")) == "Movie"
    assert folder_label(Path("/v/Movie.mp4")) == "v"


def test_screenshot_name_is_safe_and_sortable():
    name = screenshot_name('Bad: "name"/x?', 3_723_456, datetime(2026, 10, 30, 21, 14, 5))
    assert name == "Bad_ _name_x 01-02-03.456 (2026-10-30 21-14-05).png"
    assert screenshot_name("   ", 0, datetime(2026, 1, 1)).startswith("Aperture 00-00-00.000")


@pytest.mark.parametrize(
    ("rate", "ms"), [(25, 40.0), (50, 20.0), (None, 1000 / 30), (0, 1000 / 30), (5000, 1000 / 30)]
)
def test_frame_ms(rate, ms):
    assert frame_ms(rate) == pytest.approx(ms)
