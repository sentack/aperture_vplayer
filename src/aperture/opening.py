"""Files opened from outside while a playlist is playing: ask, don't guess.

Exposed to QML as `opening`. The running window shows a choice: add them to the playlist,
or open them in a window of their own. Files that arrive while the question is up join it.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Property, QObject, Signal, Slot

from aperture.core.media import display_name


class OpenChoice(QObject):
    changed = Signal()

    def __init__(
        self,
        add: Callable[[list[str]], None],
        new_window: Callable[[list[str]], None],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._add = add
        self._new_window = new_window
        self._files: list[str] = []

    @Property(bool, notify=changed)
    def pending(self) -> bool:
        return bool(self._files)

    @Property(list, notify=changed)
    def names(self) -> list[str]:
        return [display_name(item) for item in self._files]

    def offer(self, files: list[str]) -> None:
        """Ask about `files`, together with any still waiting for an answer."""
        new = [item for item in files if item not in self._files]
        if new:
            self._files.extend(new)
            self.changed.emit()

    @Slot()
    def addToPlaylist(self) -> None:
        self._answer(self._add)

    @Slot()
    def openInNewWindow(self) -> None:
        self._answer(self._new_window)

    @Slot()
    def dismiss(self) -> None:
        self._answer(None)

    def _answer(self, action: Callable[[list[str]], None] | None) -> None:
        files, self._files = self._files, []
        self.changed.emit()
        if action is not None and files:
            action(files)
