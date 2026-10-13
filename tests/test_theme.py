from dataclasses import fields

from aperture.theme import ACCENTS, DARK, DEFAULT_ACCENT, LIGHT


def test_themes_define_every_token():
    for theme in (DARK, LIGHT):
        assert all(getattr(theme, f.name) for f in fields(theme))


def test_default_accent_exists():
    assert DEFAULT_ACCENT in ACCENTS


def test_accents_are_hex():
    for value in ACCENTS.values():
        assert value.startswith("#") and len(value) == 7
        int(value[1:], 16)
