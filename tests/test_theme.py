from dataclasses import fields

import pytest

from aperture.theme import ACCENTS, DARK, DEFAULT_ACCENT, LIGHT, qml_color, qml_palette


def test_themes_define_every_token():
    for theme in (DARK, LIGHT):
        assert all(getattr(theme, f.name) for f in fields(theme))


def test_default_accent_exists():
    assert DEFAULT_ACCENT in ACCENTS


def test_accents_are_hex():
    for value in ACCENTS.values():
        assert value.startswith("#") and len(value) == 7
        int(value[1:], 16)


@pytest.mark.parametrize(
    ("css", "qml"),
    [
        ("#3D7FFF", "#3D7FFF"),
        ("rgba(245,245,247,.64)", "#A3F5F5F7"),
        ("rgba(0, 0, 0, 1)", "#FF000000"),
        ("rgba(0,0,0,.045)", "#0B000000"),
    ],
)
def test_qml_color(css, qml):
    assert qml_color(css) == qml


@pytest.mark.parametrize("bad", ["red", "#FFF", "rgb(1,2,3)"])
def test_qml_color_rejects_unknown(bad):
    with pytest.raises(ValueError):
        qml_color(bad)


def test_qml_palette_converts_every_token():
    palette = qml_palette(DARK, ACCENTS[DEFAULT_ACCENT])
    assert "name" not in palette
    assert palette["accent"] == "#3D7FFF"
    assert all(v.startswith("#") and len(v) in (7, 9) for v in palette.values())
