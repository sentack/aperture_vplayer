"""Rotating log file plus last-resort reporting of uncaught exceptions."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType

LOG_NAME = "aperture.log"
MAX_BYTES = 1_000_000
BACKUPS = 2
FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

log = logging.getLogger("aperture")


def _log_uncaught(
    exc_type: type[BaseException], exc: BaseException, tb: TracebackType | None
) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc, tb)
        return
    log.critical("uncaught exception", exc_info=(exc_type, exc, tb))


def setup_logging(log_dir: Path, level: int = logging.INFO) -> logging.Handler | None:
    """Log to `<log_dir>/aperture.log` (rotated) and warnings to stderr.

    Uncaught exceptions are logged instead of only printed, so a crash in a Qt slot leaves
    a trace users can attach to a bug report. Returns the file handler, or None if the
    folder is not writable (stderr logging still works).
    """
    root = logging.getLogger()
    root.setLevel(level)
    if not any(getattr(h, "_aperture", False) for h in root.handlers):
        console = logging.StreamHandler()
        console.setLevel(logging.WARNING)
        console.setFormatter(logging.Formatter(FORMAT))
        console._aperture = True  # type: ignore[attr-defined]
        root.addHandler(console)
    sys.excepthook = _log_uncaught

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            log_dir / LOG_NAME, maxBytes=MAX_BYTES, backupCount=BACKUPS, encoding="utf-8"
        )
    except OSError:
        log.warning("cannot write logs to %s", log_dir, exc_info=True)
        return None
    handler.setFormatter(logging.Formatter(FORMAT))
    root.addHandler(handler)
    return handler
