"""Live appearance for QML: system/dark/light mode plus accent.

`palette` is a QQmlPropertyMap exposed as `theme`, so every `theme.<token>` binding
updates in place when the mode, the accent or the OS color scheme changes.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Qt, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlPropertyMap

from aperture.settings import THEME_MODES, Settings
from aperture.theme.qml import qml_palette
from aperture.theme.tokens import ACCENTS, DARK, LIGHT


class ThemeController(QObject):
    changed = Signal()

    def __init__(self, settings: Settings, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.palette = QQmlPropertyMap(self)
        QGuiApplication.styleHints().colorSchemeChanged.connect(lambda _: self._apply())
        self._apply()

    @Property(bool, notify=changed)
    def dark(self) -> bool:
        mode = self._settings.theme_mode
        if mode == "system":
            # Unknown schemes (common on Linux) keep the player's native dark look.
            return QGuiApplication.styleHints().colorScheme() != Qt.ColorScheme.Light
        return mode == "dark"

    def _get_mode(self) -> str:
        return self._settings.theme_mode

    def _set_mode(self, value: str) -> None:
        if value in THEME_MODES and value != self._settings.theme_mode:
            self._settings.theme_mode = value
            self._settings.save()
            self._apply()

    mode = Property(str, _get_mode, _set_mode, notify=changed)

    def _get_accent(self) -> str:
        return self._settings.accent

    def _set_accent(self, value: str) -> None:
        if value in ACCENTS and value != self._settings.accent:
            self._settings.accent = value
            self._settings.save()
            self._apply()

    accent = Property(str, _get_accent, _set_accent, notify=changed)

    @Property(list, constant=True)
    def modes(self) -> list[str]:
        return list(THEME_MODES)

    @Property(list, constant=True)
    def accents(self) -> list[dict[str, str]]:
        return [{"name": name, "color": color} for name, color in ACCENTS.items()]

    @Slot()
    def reload(self) -> None:
        """Re-read Settings after something else changed them (reset to defaults)."""
        self._apply()

    def _apply(self) -> None:
        palette = qml_palette(DARK if self.dark else LIGHT, ACCENTS[self._settings.accent])
        for key, value in palette.items():
            self.palette.insert(key, value)
        self.changed.emit()
