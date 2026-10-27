from pathlib import Path

import pytest

from aperture.core.files import expand_paths, natural_key
from aperture.core.rate import RATES, format_rate, step_rate


@pytest.mark.parametrize(
    ("current", "steps", "expected"),
    [
        (1.0, 1, 1.25),
        (1.0, -1, 0.75),
        (1.0, 3, 1.75),
        (1.0, 0, 1.0),
        (2.0, 1, 2.0),
        (0.25, -1, 0.25),
        (1.0, 99, 2.0),
        (1.0, -99, 0.25),
        (1.1, 1, 1.25),
        (1.1, -1, 1.0),
        (3.0, -1, 2.0),
        (0.1, 1, 0.25),
    ],
)
def test_step_rate(current, steps, expected):
    assert step_rate(current, steps) == expected


def test_rates_include_normal_speed():
    assert 1.0 in RATES and list(RATES) == sorted(RATES)


@pytest.mark.parametrize(("rate", "text"), [(1.0, "1×"), (1.5, "1.5×"), (0.25, "0.25×")])
def test_format_rate(rate, text):
    assert format_rate(rate) == text


def test_natural_key_orders_numbers_numerically():
    names = ["Ep 10.mkv", "ep 2.mkv", "Ep 1.mkv"]
    assert sorted(names, key=lambda n: natural_key(Path(n))) == ["Ep 1.mkv", "ep 2.mkv", "Ep 10.mkv"]


def test_expand_paths(tmp_path):
    show = tmp_path / "show"
    show.mkdir()
    for name in ("Ep 10.mkv", "Ep 2.mp4", "notes.txt", "Ep 1.AVI"):
        (show / name).touch()
    (show / "extras").mkdir()
    (show / "extras" / "bonus.mp4").touch()
    loose = tmp_path / "loose.srt"
    loose.touch()

    result = expand_paths([loose, show, tmp_path / "missing.mp4"])

    assert [p.name for p in result] == ["loose.srt", "Ep 1.AVI", "Ep 2.mp4", "Ep 10.mkv"]
