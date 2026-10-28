"""Render the Aperture app icon to PNG sizes, a Windows .ico and a macOS .icns, with no image libraries.

The mark is the logo from the UI spec: an accent rounded square holding a white play
triangle. Shapes are signed distance fields, so one sample per pixel gives clean edges.
The same geometry is written as SVG for runtime use (Qt renders it at any size).

    python packaging/make_icons.py      # rewrites packaging/icons/ and the runtime SVG
"""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICON_DIR = ROOT / "packaging" / "icons"
SVG_PATH = ROOT / "src" / "aperture" / "resources" / "aperture.svg"

PNG_SIZES = (16, 24, 32, 48, 64, 128, 256, 512, 1024)
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
# macOS icon slots: (type code, pixel size). The @2x slots reuse the larger renders.
ICNS_SLOTS = (
    (b"icp4", 16), (b"icp5", 32), (b"icp6", 64), (b"ic07", 128), (b"ic08", 256),
    (b"ic09", 512), (b"ic10", 1024), (b"ic11", 32), (b"ic12", 64), (b"ic13", 256), (b"ic14", 512),
)  # fmt: skip

# Geometry in unit coordinates (0..1 across the canvas).
MARGIN = 0.0625
CORNER = 0.21875
TRIANGLE = ((0.40, 0.32), (0.70, 0.50), (0.40, 0.68))
TRIANGLE_ROUND = 0.035
TOP = (0x5B, 0x93, 0xFF)  # accent #3D7FFF, lifted at the top...
BOTTOM = (0x2F, 0x6C, 0xF0)  # ...and deepened at the bottom


def _rounded_square(x: float, y: float) -> float:
    half = 0.5 - MARGIN - CORNER
    qx, qy = abs(x - 0.5) - half, abs(y - 0.5) - half
    outside = math.hypot(max(qx, 0.0), max(qy, 0.0))
    return outside + min(max(qx, qy), 0.0) - CORNER


def _triangle(x: float, y: float) -> float:
    """Exact distance to TRIANGLE, minus the rounding radius (Inigo Quilez's sdTriangle)."""
    (ax, ay), (bx, by), (cx, cy) = TRIANGLE
    best_d, best_s = math.inf, 1.0
    orientation = math.copysign(1.0, (bx - ax) * (ay - cy) - (by - ay) * (ax - cx))
    for (px, py), (qx, qy) in (((ax, ay), (bx, by)), ((bx, by), (cx, cy)), ((cx, cy), (ax, ay))):
        ex, ey = qx - px, qy - py
        vx, vy = x - px, y - py
        t = min(max((vx * ex + vy * ey) / (ex * ex + ey * ey), 0.0), 1.0)
        dx, dy = vx - ex * t, vy - ey * t
        d = dx * dx + dy * dy
        s = orientation * (vx * ey - vy * ex)
        best_d, best_s = min(best_d, d), min(best_s, s)
    return math.copysign(math.sqrt(best_d), -best_s) - TRIANGLE_ROUND


def render(size: int) -> bytes:
    """RGBA8 pixels, row-major, straight (non-premultiplied) alpha."""
    pixels = bytearray()
    for row in range(size):
        y = (row + 0.5) / size
        t = min(max((y - MARGIN) / (1 - 2 * MARGIN), 0.0), 1.0)
        base = [round(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3)]
        for col in range(size):
            x = (col + 0.5) / size
            square = min(max(0.5 - _rounded_square(x, y) * size, 0.0), 1.0)
            if square == 0.0:
                pixels += b"\0\0\0\0"
                continue
            mark = min(max(0.5 - _triangle(x, y) * size, 0.0), 1.0)
            rgb = [round(c + (255 - c) * mark) for c in base]
            pixels += bytes((*rgb, round(255 * square)))
    return bytes(pixels)


def png(size: int) -> bytes:
    raw = render(size)
    stride = size * 4
    scanlines = b"".join(b"\0" + raw[i : i + stride] for i in range(0, len(raw), stride))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(scanlines, 9))
        + chunk(b"IEND", b"")
    )


def ico(images: dict[int, bytes]) -> bytes:
    """ICO container with PNG-compressed entries (Windows Vista and later)."""
    sizes = sorted(images)
    offset = 6 + 16 * len(sizes)
    directory, payload = b"", b""
    for size in sizes:
        data = images[size]
        side = 0 if size >= 256 else size  # 0 means 256 in the ICO directory
        directory += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(data), offset)
        payload += data
        offset += len(data)
    return struct.pack("<HHH", 0, 1, len(sizes)) + directory + payload


def icns(images: dict[int, bytes]) -> bytes:
    """Apple icon container; every slot holds PNG data (macOS 10.7 and later)."""
    body = b"".join(
        kind + struct.pack(">I", 8 + len(images[size])) + images[size] for kind, size in ICNS_SLOTS
    )
    return b"icns" + struct.pack(">I", 8 + len(body)) + body


def svg() -> str:
    def px(value: float) -> str:
        return f"{value * 512:g}"

    points = " ".join(f"{px(x)},{px(y)}" for x, y in TRIANGLE)
    top, bottom = ("#%02X%02X%02X" % color for color in (TOP, BOTTOM))
    side = px(1 - 2 * MARGIN)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{top}"/>
      <stop offset="1" stop-color="{bottom}"/>
    </linearGradient>
  </defs>
  <rect x="{px(MARGIN)}" y="{px(MARGIN)}" width="{side}" height="{side}" rx="{px(CORNER)}" fill="url(#fill)"/>
  <polygon points="{points}" fill="#FFFFFF" stroke="#FFFFFF" stroke-width="{px(2 * TRIANGLE_ROUND)}" stroke-linejoin="round"/>
</svg>
"""


def main() -> None:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    images = {size: png(size) for size in PNG_SIZES}
    for size, data in images.items():
        (ICON_DIR / f"aperture-{size}.png").write_bytes(data)
    (ICON_DIR / "aperture.ico").write_bytes(ico({s: images[s] for s in ICO_SIZES}))
    (ICON_DIR / "aperture.icns").write_bytes(icns(images))
    SVG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SVG_PATH.write_text(svg(), encoding="utf-8")
    (ICON_DIR / "aperture.svg").write_text(svg(), encoding="utf-8")


if __name__ == "__main__":
    main()
