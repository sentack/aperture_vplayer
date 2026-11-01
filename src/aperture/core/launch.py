"""Files handed to Aperture by separate launches, merged into one playlist. No Qt.

Opening several selected files from a file manager can start one process per file (Windows
Explorer always does). The first process stays; the others pass it their arguments. This
module decides how those arrivals combine: what one launch asks for, and when a later launch
joins the playlist instead of replacing it.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import url2pathname

from aperture.core.files import natural_key
from aperture.core.media import is_url

# Launches arriving within this long of the previous one belong to the same selection.
# Short enough that double-clicking another video a moment later still switches to it.
APPEND_WINDOW_S = 1.5
MAX_MESSAGE_BYTES = 1 << 20  # thousands of paths; anything longer is not from Aperture


def absolute_args(args: Iterable[str], cwd: str | Path) -> list[str]:
    """Arguments as the running instance can use them: paths absolute, file:// URLs as paths.

    The running instance has its own working directory, so relative paths are resolved here,
    in the launch that received them. Stream URLs pass through.
    """
    result = []
    for arg in args:
        if not arg:
            continue
        if is_url(arg):
            result.append(arg)
            continue
        if arg.lower().startswith("file://"):
            arg = url2pathname(urlsplit(arg).path)  # decodes %20 and the like
        path = Path(arg)
        result.append(str(path if path.is_absolute() else Path(cwd) / path))
    return result


def encode_message(args: Sequence[str]) -> bytes:
    """One launch's arguments as a single line for the local socket."""
    return json.dumps({"args": list(args)}).encode("utf-8") + b"\n"


def decode_message(data: bytes) -> list[str] | None:
    """The arguments in a message, or None if it is not a well-formed Aperture message."""
    if len(data) > MAX_MESSAGE_BYTES:
        return None
    try:
        message = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    args = message.get("args") if isinstance(message, dict) else None
    if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
        return None
    return args


def merge_launches(launches: Sequence[Sequence[str]]) -> list[str]:
    """One playlist from launches that arrived together.

    A single launch keeps its own order (a file manager or command line chose it). Several
    launches raced each other, so their arrival order means nothing: files are sorted by
    name, the order a folder lists them in. Duplicates are dropped.
    """
    if len(launches) == 1:
        return list(dict.fromkeys(launches[0]))
    flat = [arg for launch in launches for arg in launch]
    files = sorted((a for a in flat if not is_url(a)), key=lambda a: natural_key(Path(a)))
    streams = [a for a in flat if is_url(a)]
    return list(dict.fromkeys(files + streams))


def joins_previous(now: float, last_open: float | None) -> bool:
    """Whether files arriving `now` extend the playlist opened at `last_open`."""
    return last_open is not None and 0 <= now - last_open < APPEND_WINDOW_S
