"""Container formats offered in file dialogs. Decoding is left to the backend."""

from __future__ import annotations

from pathlib import Path

VIDEO_EXTENSIONS = frozenset(
    {
        ".3gp", ".avi", ".flv", ".m2ts", ".m4v", ".mkv", ".mov",
        ".mp4", ".mpeg", ".mpg", ".ogv", ".ts", ".webm", ".wmv",
    }
)  # fmt: skip


def is_video(path: Path | str) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS


def dialog_filters() -> list[str]:
    patterns = " ".join(f"*{ext}" for ext in sorted(VIDEO_EXTENSIONS))
    return [f"Video files ({patterns})", "All files (*)"]
