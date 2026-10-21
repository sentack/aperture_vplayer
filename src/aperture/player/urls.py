"""QML hands over file URLs; the core works with paths."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import QUrl


def to_paths(urls: Iterable[object]) -> list[Path]:
    paths = []
    for url in urls:
        url = url if isinstance(url, QUrl) else QUrl(str(url))
        paths.append(Path(url.toLocalFile() if url.isLocalFile() else url.toString()))
    return paths
