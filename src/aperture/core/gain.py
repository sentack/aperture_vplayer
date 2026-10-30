"""Audio boost: amplify past 100% without the harsh distortion of hard clipping.

Samples above the knee are bent smoothly towards full scale (a tanh soft limiter), so a
quiet track can be lifted to 200% and the loud peaks round off instead of crackling.
"""

from __future__ import annotations

import math
from array import array

MAX_BOOST = 2.0
KNEE = 0.8  # below this level samples pass through untouched


def soft_limit(x: float) -> float:
    """Identity up to the knee, then an asymptote at ±1.0: never clips."""
    magnitude = abs(x)
    if magnitude <= KNEE:
        return x
    headroom = 1.0 - KNEE
    shaped = KNEE + headroom * math.tanh((magnitude - KNEE) / headroom)
    return math.copysign(shaped, x)


def boost(samples: array, gain: float) -> array:
    """Scale `samples` by `gain` in place and return them.

    Typecodes: "f" for float audio in [-1, 1], "h" for 16-bit and "i" for 32-bit integers.
    """
    if gain == 1.0:
        return samples
    if samples.typecode == "f":
        for i, value in enumerate(samples):
            samples[i] = soft_limit(value * gain)
        return samples
    full = 32767 if samples.typecode == "h" else 2147483647
    for i, value in enumerate(samples):
        samples[i] = round(soft_limit(value * gain / full) * full)
    return samples
