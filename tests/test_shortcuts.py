"""KeyBindings.qml must bind every keymap action exactly once, and hard-code only fixed keys."""

import re
from pathlib import Path

from aperture.core.keymap import ACTIONS

QML = Path(__file__).resolve().parent.parent / "src" / "aperture" / "ui" / "qml"


def bindings() -> str:
    return (QML / "KeyBindings.qml").read_text(encoding="utf-8")


def test_every_action_is_bound_once():
    bound = re.findall(r'Bound \{ action: "(\w+)"', bindings())
    assert sorted(bound) == sorted(a.id for a in ACTIONS)


def test_only_fixed_keys_are_hard_coded():
    assert sorted(re.findall(r'sequence: "([^"]+)"', bindings())) == ["Escape", "Menu"]


def test_readme_lists_every_default():
    readme = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
    for action in ACTIONS:
        assert f"| `{action.default}` | {action.label} |" in readme
