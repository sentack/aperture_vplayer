"""Color tokens. Only accent varies per user; everything else is theme-locked."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Theme:
    name: str
    bg_0: str
    bg_1: str
    bg_2: str
    bg_3: str
    text_primary: str
    text_secondary: str
    text_tertiary: str
    bar_bg: str
    bar_border: str
    track_bg: str
    divider: str
    chip_bg: str
    scrim_top: str
    scrim_bottom: str
    idle_track: str


DARK = Theme(
    name="dark",
    bg_0="#111319",
    bg_1="#1A1D27",
    bg_2="#232733",
    bg_3="#2E3342",
    text_primary="#F5F5F7",
    text_secondary="rgba(245,245,247,.64)",
    text_tertiary="rgba(245,245,247,.42)",
    bar_bg="rgba(24,25,31,.70)",
    bar_border="rgba(255,255,255,.09)",
    track_bg="rgba(255,255,255,.18)",
    divider="rgba(255,255,255,.12)",
    chip_bg="rgba(255,255,255,.07)",
    scrim_top="rgba(0,0,0,.40)",
    scrim_bottom="rgba(6,6,10,.55)",
    idle_track="rgba(255,255,255,.14)",
)

LIGHT = Theme(
    name="light",
    bg_0="#F2F2F0",
    bg_1="#E7E7E3",
    bg_2="#DADAD5",
    bg_3="#CDCDC6",
    text_primary="#17171A",
    text_secondary="rgba(23,23,26,.64)",
    text_tertiary="rgba(23,23,26,.42)",
    bar_bg="rgba(255,255,255,.72)",
    bar_border="rgba(0,0,0,.07)",
    track_bg="rgba(0,0,0,.13)",
    divider="rgba(0,0,0,.10)",
    chip_bg="rgba(0,0,0,.045)",
    scrim_top="rgba(0,0,0,.08)",
    scrim_bottom="rgba(255,255,255,.55)",
    idle_track="rgba(0,0,0,.12)",
)

ACCENTS: dict[str, str] = {
    "blue": "#3D7FFF",
    "coral": "#FF6A52",
    "green": "#3FA671",
    "amber": "#E8A23D",
    "violet": "#8B6FE8",
}

DEFAULT_ACCENT = "blue"
