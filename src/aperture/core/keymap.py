"""Every keyboard action, its default key, and one-to-one rebinding rules.

Key sequences are Qt PortableText strings ("Ctrl+Shift+L", "Space", "["), which is what the
UI captures; on macOS Qt shows "Ctrl" as ⌘. Each action has at most one key and each key
belongs to at most one action. Users store only their changes from the defaults.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Action:
    id: str
    label: str
    group: str
    default: str


PLAYBACK, SOUND, WINDOW = "Playback", "Sound and tracks", "Playlist and window"

ACTIONS: tuple[Action, ...] = (
    Action("play_pause", "Play / pause", PLAYBACK, "Space"),
    Action("seek_back_5", "Back 5 s", PLAYBACK, "Left"),
    Action("seek_forward_5", "Forward 5 s", PLAYBACK, "Right"),
    Action("seek_back_10", "Back 10 s", PLAYBACK, "Ctrl+Left"),
    Action("seek_forward_10", "Forward 10 s", PLAYBACK, "Ctrl+Right"),
    Action("seek_back_30", "Back 30 s", PLAYBACK, "Shift+Left"),
    Action("seek_forward_30", "Forward 30 s", PLAYBACK, "Shift+Right"),
    Action("seek_start", "Back to start", PLAYBACK, "Home"),
    Action("frame_previous", "Previous frame", PLAYBACK, ","),
    Action("frame_next", "Next frame", PLAYBACK, "."),
    Action("ab_loop", "A–B loop: set A, set B, clear", PLAYBACK, "L"),
    Action("slower", "Slower", PLAYBACK, "["),
    Action("faster", "Faster", PLAYBACK, "]"),
    Action("normal_speed", "Normal speed", PLAYBACK, "="),
    Action("volume_up", "Volume up", SOUND, "Up"),
    Action("volume_down", "Volume down", SOUND, "Down"),
    Action("mute", "Mute", SOUND, "M"),
    Action("subtitles", "Subtitles on / off", SOUND, "C"),
    Action("audio_track", "Next audio track", SOUND, "A"),
    Action("next", "Next in playlist", WINDOW, "N"),
    Action("previous", "Previous in playlist", WINDOW, "P"),
    Action("fullscreen", "Fullscreen", WINDOW, "F"),
    Action("mini_player", "Mini player", WINDOW, "I"),
    Action("screenshot", "Screenshot", WINDOW, "S"),
    Action("open_files", "Open files", WINDOW, "Ctrl+O"),
    Action("open_url", "Open URL", WINDOW, "Ctrl+U"),
    Action("settings", "Settings", WINDOW, "Ctrl+,"),
    Action("context_menu", "Quick options menu", WINDOW, "Shift+F10"),
)
ACTION_IDS = frozenset(action.id for action in ACTIONS)
_BY_ID = {action.id: action for action in ACTIONS}

# Built in, not rebindable: Esc closes dialogs / leaves fullscreen, the Menu key opens the
# quick options menu. Both stay reserved so nothing else can take them.
FIXED: tuple[tuple[str, str], ...] = (
    ("Esc", "Close dialog / leave fullscreen"),
    ("Menu", "Quick options menu"),
)

# Shortcuts the operating system owns. Ctrl means ⌘ on macOS, so Ctrl+Q / Ctrl+H / Ctrl+M are
# Quit / Hide / Minimize there and are blocked everywhere for consistency.
RESERVED = frozenset(
    key.casefold()
    for key in (
        "Esc", "Escape", "Menu", "Alt+F4", "Alt+Tab", "Alt+Shift+Tab", "Alt+Esc", "Alt+Space",
        "Ctrl+Alt+Del", "Ctrl+Alt+Delete", "Ctrl+Shift+Esc", "Ctrl+Esc", "Ctrl+Q", "Ctrl+H",
        "Ctrl+M", "Ctrl+Tab", "Meta+L", "Meta+D", "Meta+E", "Meta+R", "Meta+Tab", "Meta+Space",
    )
)  # fmt: skip
_RESERVED_PREFIXES = ("ctrl+alt+f",)  # Linux virtual-terminal switching: Ctrl+Alt+F1…F12


def _norm(key: str) -> str:
    return key.strip().casefold()


def is_reserved(key: str) -> bool:
    key = _norm(key)
    return key in RESERVED or key.startswith(_RESERVED_PREFIXES)


class BindingError(ValueError):
    """A rejected rebind; the message is written for the user."""


class Keymap:
    def __init__(self, overrides: Mapping[str, str] | None = None) -> None:
        self._keys = {action.id: action.default for action in ACTIONS}
        for action_id, key in (overrides or {}).items():
            try:
                self.bind(action_id, key)
            except BindingError:
                continue  # a stale or conflicting saved override: keep the default

    def key(self, action_id: str) -> str:
        return self._keys[action_id]

    def keys(self) -> dict[str, str]:
        return dict(self._keys)

    def owner(self, key: str) -> str | None:
        """Action currently bound to `key`, if any."""
        wanted = _norm(key)
        return next((a for a, k in self._keys.items() if k and _norm(k) == wanted), None)

    def bind(self, action_id: str, key: str) -> None:
        """Bind `key` to `action_id`, or unbind it when `key` is empty. Never steals a key."""
        if action_id not in ACTION_IDS:
            raise BindingError(f"Unknown action: {action_id}")
        key = key.strip()
        if not key:
            self._keys[action_id] = ""
            return
        if is_reserved(key):
            raise BindingError(f"{key} is reserved by the system. Choose a different combination.")
        owner = self.owner(key)
        if owner is not None and owner != action_id:
            raise BindingError(
                f"{key} is already used for {_BY_ID[owner].label}. "
                "Choose a different combination or unbind it first."
            )
        self._keys[action_id] = key

    def unbind(self, action_id: str) -> None:
        self.bind(action_id, "")

    def reset(self) -> None:
        self._keys = {action.id: action.default for action in ACTIONS}

    def overrides(self) -> dict[str, str]:
        """Only the bindings that differ from the defaults, for storage."""
        return {a.id: self._keys[a.id] for a in ACTIONS if self._keys[a.id] != a.default}
