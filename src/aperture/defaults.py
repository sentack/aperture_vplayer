"""The "make Aperture your default player?" question, exposed to QML as `defaults`.

Checked shortly after start and every 30 minutes; shown at most once every 6 hours, only
when Aperture can actually claim the role and does not have it yet.
"""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from aperture import __version__
from aperture.core.schedule import should_ask_default
from aperture.settings import Settings
from aperture.system import default_player

CHECK_INTERVAL_MS = 30 * 60 * 1000
FIRST_CHECK_MS = 8_000  # let the window settle, and any resume question go first


class DefaultPlayerController(QObject):
    changed = Signal()
    noticed = Signal(str)

    def __init__(
        self,
        settings: Settings,
        icon_svg: Path,
        parent: QObject | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._icon = icon_svg
        self._clock = clock
        self._status: bool | None = None
        self._can_claim = False
        self._prompt = False

        self._timer = QTimer(self)
        self._timer.setInterval(CHECK_INTERVAL_MS)
        self._timer.timeout.connect(self.check)
        self._timer.start()
        QTimer.singleShot(FIRST_CHECK_MS, self.check)

    @Property(str, notify=changed)
    def status(self) -> str:
        """"default", "other" or "unknown"."""
        return {True: "default", False: "other"}.get(self._status, "unknown")

    @Property(bool, notify=changed)
    def canClaim(self) -> bool:
        return self._can_claim

    @Property(bool, notify=changed)
    def promptVisible(self) -> bool:
        return self._prompt

    def _get_ask(self) -> bool:
        return self._settings.ask_default

    def _set_ask(self, value: bool) -> None:
        if bool(value) != self._settings.ask_default:
            self._settings.ask_default = bool(value)
            self._settings.save()
            if not value:
                self._prompt = False
            self.changed.emit()

    askEnabled = Property(bool, _get_ask, _set_ask, notify=changed)

    @Slot()
    def check(self) -> None:
        self._refresh_appimage()
        self._status = default_player.status()
        self._can_claim = default_player.can_claim()
        now = self._clock()
        settings = self._settings
        due = should_ask_default(now, settings.ask_default_last, settings.ask_default, self._status)
        if due and self._can_claim and not self._prompt:
            self._prompt = True
            self._settings.ask_default_last = now
            self._settings.save()
        self.changed.emit()

    def _refresh_appimage(self) -> None:
        """Keep the default player on the newest AppImage, not the first one installed."""
        appimage = os.environ.get("APPIMAGE")
        if not sys.platform.startswith("linux") or not appimage:
            return
        replaced = default_player.refresh_default_appimage(Path(appimage), __version__, self._icon)
        if replaced is not None:
            self.noticed.emit(f"Videos now open in Aperture {__version__}, not {replaced.name}")

    @Slot()
    def claim(self) -> None:
        self._prompt = False
        result = default_player.claim(self._icon)
        if result == default_player.DONE:
            self.noticed.emit("Aperture is now your default video player")
        elif result == default_player.OPENED_SETTINGS:
            self.noticed.emit("Choose Aperture in Default apps to finish")
        else:
            self.noticed.emit("Couldn't change the default player")
        self._status = default_player.status()
        self.changed.emit()

    @Slot()
    def dismiss(self) -> None:
        self._prompt = False
        self.changed.emit()

    @Slot()
    def neverAsk(self) -> None:
        self._set_ask(False)
