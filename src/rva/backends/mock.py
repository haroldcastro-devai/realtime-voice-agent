from __future__ import annotations

import array
import math
import time


class MockSTT:
    def __init__(self, canned: str = "hello, I would like to check my order") -> None:
        self.canned = canned

    def transcribe(self, pcm: bytes, sample_rate: int) -> str:
        time.sleep(0.04)
        if not pcm:
            return ""
        return self.canned


class MockLLM:
    def __init__(self, agent_name: str = "Ava") -> None:
        self.agent_name = agent_name

    def reply(self, user_text: str, history: list[dict[str, str]]) -> str:
        time.sleep(0.05)
        text = (user_text or "").strip() or "there"
        return f"Hi, this is {self.agent_name}. I heard: {text[:80]}. How else can I help?"


class MockTTS:
    def synthesize(self, text: str, sample_rate: int) -> bytes:
        time.sleep(0.03)
        duration = min(2.5, 0.35 + 0.04 * len(text))
        n = int(sample_rate * duration)
        buf = array.array("h")
        for i in range(n):
            t = i / sample_rate
            sample = int(7000 * math.sin(2 * math.pi * 220 * t) * max(0.0, 1 - t / duration))
            buf.append(sample)
        return buf.tobytes()
