"""When to ask the user to make Aperture their default player."""

from __future__ import annotations

DEFAULT_PROMPT_INTERVAL_S = 6 * 3600


def should_ask_default(
    now: float, last_asked: float, enabled: bool, is_default: bool | None
) -> bool:
    """Ask only when enabled, known not to be default, and not within the last 6 hours.

    A `last_asked` in the future (clock moved back) does not block asking forever.
    """
    if not enabled or is_default is not False:
        return False
    return not 0 <= now - last_asked < DEFAULT_PROMPT_INTERVAL_S
