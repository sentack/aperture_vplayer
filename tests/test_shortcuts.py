"""Settings shows Shortcuts.js; KeyBindings.qml does the binding. Both must list the same keys."""

import re
from pathlib import Path

QML = Path(__file__).resolve().parent.parent / "src" / "aperture" / "ui" / "qml"

# How the reference spells keys that KeyBindings names differently.
DISPLAY = {"←": "Left", "→": "Right", "↑": "Up", "↓": "Down", "Esc": "Escape", "Ctrl+O": "StandardKey.Open"}


def bound_keys() -> set[str]:
    text = (QML / "KeyBindings.qml").read_text(encoding="utf-8")
    keys = set(re.findall(r'\bsequence: "([^"]+)"', text))
    for group in re.findall(r"\bsequences: \[([^\]]+)\]", text):
        keys |= set(re.findall(r'"([^"]+)"', group))
        keys |= {f"StandardKey.{name}" for name in re.findall(r"StandardKey\.(\w+)", group)}
    return keys


def listed_keys() -> set[str]:
    text = (QML / "Shortcuts.js").read_text(encoding="utf-8")
    keys = set()
    for group in re.findall(r'keys: \[((?:"[^"]*"(?:, )?)+)\]', text):
        for key in re.findall(r'"([^"]*)"', group):
            key = DISPLAY.get(key, key)
            for arrow in "←→↑↓":
                key = key.replace(arrow, DISPLAY[arrow])  # Shift+← -> Shift+Left
            keys.add(key)
    return keys


def test_reference_lists_every_binding():
    assert listed_keys() == bound_keys()


def test_settings_shortcut_is_bound():
    assert "Ctrl+," in bound_keys()
