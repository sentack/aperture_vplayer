"""The main window reopens at the size the user left it."""

import pytest

from aperture.core.window_size import DEFAULT_SIZE, MIN_SIZE, initial_size
from aperture.settings import Settings


def test_first_launch_leaves_some_of_the_screen():
    assert initial_size(None, (2560, 1400)) == DEFAULT_SIZE
    assert initial_size(None, (1366, 728)) == (1161, 619)  # 85% of a small laptop screen


def test_saved_size_is_kept_and_fitted_to_this_screen():
    assert initial_size((1000, 640), (1920, 1040)) == (1000, 640)
    assert initial_size((2400, 1300), (1920, 1040)) == (1920, 1040)  # from a bigger monitor
    assert initial_size((100, 100), (1920, 1040)) == MIN_SIZE


def test_settings_keep_the_window_size(tmp_path):
    settings = Settings(tmp_path / "settings.json")
    assert settings.window_size == [] and settings.window_maximized is False
    settings.window_size = [1000, 640]
    settings.window_maximized = True
    settings.save()
    loaded = Settings(tmp_path / "settings.json")
    assert loaded.window_size == [1000, 640] and loaded.window_maximized is True
    loaded.reset()  # not a preference: Reset to defaults keeps it
    assert loaded.window_size == [1000, 640]
    for bad in ([1000], [0, 600], [1000.5, 600], [True, 600], "1000x600"):
        with pytest.raises(ValueError):
            settings.window_size = bad
