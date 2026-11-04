"""Reopen the main window at the size the user left it, exposed to QML as `windowSize`.

Only a normal size the user resized to counts: maximized, fullscreen, minimized and the mini
player don't replace it, so un-maximizing after the next launch goes back to that size.
Whether the window was maximized is remembered too. Saved when Aperture quits.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, QTimer, Slot
from PySide6.QtGui import QWindow

from aperture.core.window_size import initial_size
from aperture.settings import Settings

# Maximizing can resize the window before it reports being maximized: read the size once
# the changes have settled, not on every step.
SETTLE_MS = 300


class WindowMemory(QObject):
    def __init__(
        self, settings: Settings, available: tuple[int, int], parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        saved = tuple(settings.window_size) if settings.window_size else None
        self._size = initial_size(saved, available)
        self._normal = saved  # None until the user has a size worth keeping
        self._maximized = settings.window_maximized
        self._window: QWindow | None = None
        self._settle = QTimer(self, singleShot=True, interval=SETTLE_MS)
        self._settle.timeout.connect(self._read_size)

    @Property(int, constant=True)
    def width(self) -> int:
        return self._size[0]

    @Property(int, constant=True)
    def height(self) -> int:
        return self._size[1]

    @Property(bool, constant=True)
    def maximized(self) -> bool:
        return self._settings.window_maximized

    def attach(self, window: QWindow) -> None:
        """Follow `window` from now on (call once it is shown at its first size)."""
        self._window = window
        # Not connected to start() directly: the new width would become the timer's interval.
        window.widthChanged.connect(lambda _: self._settle.start())
        window.heightChanged.connect(lambda _: self._settle.start())
        window.visibilityChanged.connect(self._on_visibility)

    def _on_visibility(self, visibility) -> None:
        if self._window is None or self._window.property("mini"):
            return
        if visibility == QWindow.Visibility.Maximized:
            self._maximized = True
        elif visibility == QWindow.Visibility.Windowed:
            self._maximized = False
        # FullScreen and Minimized leave it alone: the window comes back from them as it was.

    def _read_size(self) -> None:
        window = self._window
        if window is None or window.property("mini"):
            return
        if window.visibility() == QWindow.Visibility.Windowed:
            self._normal = (window.width(), window.height())

    @Slot()
    def save(self) -> None:
        if self._settle.isActive():  # a resize just before quitting still counts
            self._settle.stop()
            self._read_size()
        if self._normal is not None:
            self._settings.window_size = [int(v) for v in self._normal]
        self._settings.window_maximized = self._maximized
        self._settings.save()
