"""Small workarounds for PySide6 quirks."""

from __future__ import annotations

import warnings

from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlPropertyMap


def property_map(parent: QObject) -> QQmlPropertyMap:
    """A QQmlPropertyMap owned by `parent`.

    PySide6 reports QQmlPropertyMap's constructor as deprecated, with or without a parent,
    yet offers no replacement; the warning is noise, so it is silenced here.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        mapping = QQmlPropertyMap()
    mapping.setParent(parent)
    return mapping
