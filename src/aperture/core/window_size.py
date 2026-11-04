"""The main window's size: the one the user last left it at, fitted to this screen."""

from __future__ import annotations

DEFAULT_SIZE = (1440, 900)  # first launch, before there is anything to remember
MIN_SIZE = (720, 450)  # Main.qml's minimumWidth / minimumHeight
FIRST_LAUNCH_SHARE = 0.85  # of the screen, at most, before the user has chosen a size


def initial_size(
    saved: tuple[int, int] | None, available: tuple[int, int]
) -> tuple[int, int]:
    """Size to open at: `saved` (or the default) shrunk to fit the `available` screen area.

    A size saved on a larger monitor still fits a smaller one; the first launch leaves some
    of the screen uncovered.
    """
    if saved is None:
        width = min(DEFAULT_SIZE[0], round(available[0] * FIRST_LAUNCH_SHARE))
        height = min(DEFAULT_SIZE[1], round(available[1] * FIRST_LAUNCH_SHARE))
    else:
        width, height = saved
    return (
        min(max(width, MIN_SIZE[0]), available[0]),
        min(max(height, MIN_SIZE[1]), available[1]),
    )
