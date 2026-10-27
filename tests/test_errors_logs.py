import logging
import sys

import pytest

from aperture.core.errors import ERROR_KINDS, describe_error
from aperture.logs import LOG_NAME, setup_logging


@pytest.mark.parametrize("kind", ERROR_KINDS)
def test_every_kind_names_the_file(kind):
    error = describe_error(kind, "movie.mkv")
    assert error.title
    assert "“movie.mkv”" in error.message


def test_unknown_kind_falls_back():
    assert describe_error("weird", "a.mp4") == describe_error("other", "a.mp4")


def test_format_error_wording():
    assert describe_error("format", "a.avi").title == "Unsupported format"


@pytest.fixture
def isolated_logging():
    root = logging.getLogger()
    handlers, level, hook = list(root.handlers), root.level, sys.excepthook
    yield
    for handler in root.handlers[:]:
        if handler not in handlers:
            root.removeHandler(handler)
            handler.close()
    root.setLevel(level)
    sys.excepthook = hook


def test_setup_logging_writes_file_and_uncaught(tmp_path, isolated_logging):
    handler = setup_logging(tmp_path / "logs")
    assert handler is not None

    logging.getLogger("aperture.test").info("hello")
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        sys.excepthook(*sys.exc_info())
    handler.flush()

    text = (tmp_path / "logs" / LOG_NAME).read_text(encoding="utf-8")
    assert "aperture.test: hello" in text
    assert "uncaught exception" in text and "RuntimeError: boom" in text


def test_setup_logging_adds_console_once(tmp_path, isolated_logging):
    setup_logging(tmp_path)
    setup_logging(tmp_path)
    consoles = [h for h in logging.getLogger().handlers if getattr(h, "_aperture", False)]
    assert len(consoles) == 1


def test_setup_logging_unwritable_dir(tmp_path, isolated_logging):
    blocker = tmp_path / "file"
    blocker.write_text("")
    assert setup_logging(blocker / "logs") is None
