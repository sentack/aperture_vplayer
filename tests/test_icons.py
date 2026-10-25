import importlib.util
import struct
import zlib
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "packaging" / "make_icons.py"


@pytest.fixture(scope="module")
def icons():
    spec = importlib.util.spec_from_file_location("make_icons", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pixel(raw: bytes, size: int, x: int, y: int) -> tuple[int, ...]:
    i = (y * size + x) * 4
    return tuple(raw[i : i + 4])


def test_render_layout(icons):
    size = 64
    raw = icons.render(size)
    assert len(raw) == size * size * 4
    assert pixel(raw, size, 0, 0)[3] == 0  # transparent margin
    assert pixel(raw, size, 32, 32) == (255, 255, 255, 255)  # play mark at the centre
    r, g, b, a = pixel(raw, size, 32, 8)  # accent above the mark
    assert a == 255 and b > r and b > g


def decode_png(data: bytes) -> tuple[int, int, bytes]:
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, width, height = 8, b"", 0, 0
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        kind, body = data[pos + 4 : pos + 8], data[pos + 8 : pos + 8 + length]
        (crc,) = struct.unpack(">I", data[pos + 8 + length : pos + 12 + length])
        assert crc == zlib.crc32(kind + body)
        if kind == b"IHDR":
            width, height = struct.unpack(">II", body[:8])
        elif kind == b"IDAT":
            idat += body
        pos += 12 + length
    return width, height, zlib.decompress(idat)


def test_png_is_valid(icons):
    width, height, scanlines = decode_png(icons.png(16))
    assert (width, height) == (16, 16)
    assert len(scanlines) == 16 * (1 + 16 * 4)


def test_ico_directory(icons):
    images = {16: icons.png(16), 32: icons.png(32)}
    data = icons.ico(images)
    reserved, kind, count = struct.unpack("<HHH", data[:6])
    assert (reserved, kind, count) == (0, 1, 2)
    for n, size in enumerate((16, 32)):
        entry = struct.unpack("<BBBBHHII", data[6 + 16 * n : 22 + 16 * n])
        assert entry[0] == entry[1] == size
        length, offset = entry[6], entry[7]
        assert data[offset : offset + length] == images[size]


def test_ico_encodes_256_as_zero(icons):
    data = icons.ico({256: b"x"})
    assert data[6] == 0 and data[7] == 0


def test_svg_matches_geometry(icons):
    text = icons.svg()
    assert 'rx="112"' in text and "stroke-linejoin=\"round\"" in text
