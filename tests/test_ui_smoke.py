"""Load the real QML against the real controllers, offscreen.

Catches what unit tests cannot: QML syntax errors, missing types, bad bindings.
Skipped when PySide6 is not installed.
"""

import os

import pytest

pytest.importorskip("PySide6.QtQuick")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="module")
def app():
    from PySide6.QtGui import QGuiApplication

    return QGuiApplication.instance() or QGuiApplication([])


@pytest.fixture
def ui(app, tmp_path):
    from aperture.app import load_ui

    warnings = []
    engine, player = load_ui(app, tmp_path, on_warnings=lambda errors: warnings.extend(errors))
    app.processEvents()
    yield engine, player, warnings
    for window in engine.rootObjects():
        window.close()
    app.processEvents()
    del engine


def messages(warnings):
    return [w.toString() for w in warnings]


def test_main_window_loads_cleanly(ui):
    engine, _, warnings = ui
    assert engine.rootObjects()
    assert messages(warnings) == []


def test_theme_switch_rebinds_cleanly(ui, app):
    engine, _, warnings = ui
    appearance = engine.rootContext().contextProperty("appearance")
    for mode in ("light", "dark", "system"):
        appearance.setProperty("mode", mode)
        app.processEvents()
    appearance.setProperty("accent", "coral")
    app.processEvents()
    assert messages(warnings) == []
