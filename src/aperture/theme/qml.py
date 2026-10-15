"""Token conversion for QML, which has no CSS rgba() parser."""

from __future__ import annotations

import re
from dataclasses import fields

from aperture.theme.tokens import Theme

_RGBA = re.compile(r"rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*([\d.]+)\s*\)")


def qml_color(value: str) -> str:
    """`#RRGGBB` passes through; `rgba(r,g,b,a)` becomes `#AARRGGBB`."""
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        return value
    match = _RGBA.fullmatch(value)
    if match is None:
        raise ValueError(f"unsupported color: {value!r}")
    r, g, b = (int(match[i]) for i in (1, 2, 3))
    alpha = round(float(match[4]) * 255)
    return f"#{alpha:02X}{r:02X}{g:02X}{b:02X}"


def qml_palette(theme: Theme, accent: str) -> dict[str, str]:
    palette = {f.name: qml_color(getattr(theme, f.name)) for f in fields(theme) if f.name != "name"}
    palette["accent"] = qml_color(accent)
    return palette
