"""Energy VAD on 16-bit PCM. Independent of any vendor stack."""

from __future__ import annotations

import array
import math


def rms(pcm: bytes) -> float:
    if len(pcm) < 2:
        return 0.0
    samples = array.array("h")
    samples.frombytes(pcm[: len(pcm) - (len(pcm) % 2)])
    if not samples:
        return 0.0
    acc = 0
    for s in samples:
        acc += s * s
    return math.sqrt(acc / len(samples))


def is_speech(pcm: bytes, threshold: float) -> bool:
    return rms(pcm) >= threshold
