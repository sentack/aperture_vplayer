"""Fail the build if the PyInstaller output cannot play video.

Aperture decodes through Qt Multimedia's FFmpeg backend: the `ffmpegmediaplugin` plugin plus
FFmpeg's own libraries, which carry the VP8/VP9 (WebM), H.264, HEVC, AV1, Opus and Vorbis
decoders. A bundle missing any of them plays some files as sound over a black picture, or
not at all, so check before packaging rather than after a user reports it.

    python packaging/check_bundle.py dist/aperture
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# (what, pattern over paths relative to the bundle, using forward slashes)
REQUIRED = (
    ("FFmpeg multimedia backend", r"(^|/)multimedia/[^/]*ffmpegmediaplugin[^/]*$"),
    ("libavcodec (decoders)", r"(^|/)(lib)?avcodec[^/]*\.(dll|dylib|so[.\d]*)$"),
    ("libavformat (containers)", r"(^|/)(lib)?avformat[^/]*\.(dll|dylib|so[.\d]*)$"),
    ("libavutil", r"(^|/)(lib)?avutil[^/]*\.(dll|dylib|so[.\d]*)$"),
    ("libswresample (audio)", r"(^|/)(lib)?swresample[^/]*\.(dll|dylib|so[.\d]*)$"),
    ("libswscale (pixel formats)", r"(^|/)(lib)?swscale[^/]*\.(dll|dylib|so[.\d]*)$"),
    ("QtMultimedia QML module", r"(^|/)qml/QtMultimedia/qmldir$"),
    ("QtQuick.Controls QML module", r"(^|/)qml/QtQuick/Controls/qmldir$"),
    ("QtQuick.Dialogs QML module", r"(^|/)qml/QtQuick/Dialogs/qmldir$"),
    ("QtQuick.Shapes QML module", r"(^|/)qml/QtQuick/Shapes/qmldir$"),
    ("Aperture QML", r"(^|/)aperture/ui/qml/Main\.qml$"),
)
# Add-ons excluded on purpose (see UNUSED_QT in aperture.spec); finding one means the filter broke.
FORBIDDEN = (("Qt WebEngine", r"WebEngine"),)


def check(bundle: Path) -> list[str]:
    """Problems found in `bundle`; empty when it is complete."""
    if not bundle.is_dir():
        return [f"{bundle} is not a directory"]
    files = [p.relative_to(bundle).as_posix() for p in bundle.rglob("*") if p.is_file()]
    problems = [
        f"missing: {what}"
        for what, pattern in REQUIRED
        if not any(re.search(pattern, f) for f in files)
    ]
    for what, pattern in FORBIDDEN:
        hits = [f for f in files if re.search(pattern, f)]
        if hits:
            problems.append(f"unexpected: {what} ({hits[0]} and {len(hits) - 1} more)")
    return problems


def main(argv: list[str]) -> int:
    bundle = Path(argv[1] if len(argv) > 1 else "dist/aperture")
    problems = check(bundle)
    for problem in problems:
        print(problem, file=sys.stderr)
    if not problems:
        print(f"{bundle}: video backend and QML modules present")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
