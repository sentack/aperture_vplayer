"""Keyboard bindings for QML, exposed as `keymap`.

`keys` is a QQmlPropertyMap (action id -> key sequence) that KeyBindings.qml binds every
Shortcut to, so a rebind in Settings takes effect at once. Settings stores the overrides.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QKeyCombination, QObject, Qt, Signal, Slot
from PySide6.QtGui import QKeySequence
from PySide6.QtQml import QQmlPropertyMap

from aperture.core.keymap import ACTIONS, FIXED, BindingError, Keymap
from aperture.qt_compat import property_map
from aperture.settings import Settings

_MODIFIER_KEYS = {
    Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Meta,
    Qt.Key.Key_AltGr, Qt.Key.Key_CapsLock, Qt.Key.Key_NumLock, Qt.Key.Key_unknown,
}  # fmt: skip
_ARROWS = {"Left": "←", "Right": "→", "Up": "↑", "Down": "↓"}
_MAC_MODIFIERS = (("Ctrl+", "⌘"), ("Alt+", "⌥"), ("Shift+", "⇧"), ("Meta+", "⌃"))


class KeymapController(QObject):
    changed = Signal()
    capturingChanged = Signal()

    def __init__(
        self, settings: Settings, mac: bool = False, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._mac = mac
        self._keymap = Keymap(settings.shortcuts)
        self._capturing = False
        self._keys = property_map(self)
        self._publish()

    @Property(QObject, constant=True)
    def keys(self) -> QQmlPropertyMap:
        """Action id -> key sequence, updated in place on every rebind."""
        return self._keys

    @Property(list, notify=changed)
    def actions(self) -> list[dict[str, str]]:
        return [
            {
                "id": a.id,
                "label": a.label,
                "group": a.group,
                "key": self._keymap.key(a.id),
                "default": a.default,
            }
            for a in ACTIONS
        ]

    @Property(list, constant=True)
    def groups(self) -> list[str]:
        return list(dict.fromkeys(a.group for a in ACTIONS))

    @Property(list, constant=True)
    def fixed(self) -> list[dict[str, str]]:
        return [{"key": key, "label": label} for key, label in FIXED]

    def _get_capturing(self) -> bool:
        return self._capturing

    def _set_capturing(self, value: bool) -> None:
        """True while Settings listens for a new key: every Shortcut stands down meanwhile."""
        if bool(value) != self._capturing:
            self._capturing = bool(value)
            self.capturingChanged.emit()

    capturing = Property(bool, _get_capturing, _set_capturing, notify=capturingChanged)

    @Slot(int, int, result=str)
    def sequenceFor(self, key: int, modifiers: int) -> str:
        """PortableText for a key press; "" for a lone modifier or an unknown key."""
        try:
            qt_key = Qt.Key(key)
        except ValueError:
            return ""
        if qt_key in _MODIFIER_KEYS:
            return ""
        mods = Qt.KeyboardModifier(modifiers) & ~Qt.KeyboardModifier.KeypadModifier
        sequence = QKeySequence(QKeyCombination(mods, qt_key))
        return sequence.toString(QKeySequence.SequenceFormat.PortableText)

    @Slot(str, result=str)
    def display(self, key: str) -> str:
        """How a key reads on screen: arrows as arrows, ⌘ ⌥ ⇧ on macOS."""
        if not key:
            return "Not set"
        for name, arrow in _ARROWS.items():
            key = key.replace(name, arrow)
        if self._mac:
            for name, glyph in _MAC_MODIFIERS:
                key = key.replace(name, glyph)
        return key

    @Slot(str, str, result=str)
    def bind(self, action_id: str, key: str) -> str:
        """Rebind; returns "" on success or the reason it was refused."""
        try:
            self._keymap.bind(action_id, key)
        except BindingError as exc:
            return str(exc)
        self._commit()
        return ""

    @Slot(str)
    def unbind(self, action_id: str) -> None:
        self.bind(action_id, "")

    @Slot()
    def resetShortcuts(self) -> None:
        self._keymap.reset()
        self._commit()

    @Slot()
    def reload(self) -> None:
        """Re-read Settings after a full reset to defaults."""
        self._keymap = Keymap(self._settings.shortcuts)
        self._publish()

    def _commit(self) -> None:
        self._settings.shortcuts = self._keymap.overrides()
        self._settings.save()
        self._publish()

    def _publish(self) -> None:
        for action_id, key in self._keymap.keys().items():
            self._keys.insert(action_id, key)
        self.changed.emit()
