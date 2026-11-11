from __future__ import annotations

from typing import Protocol


class STTBackend(Protocol):
    def transcribe(self, pcm: bytes, sample_rate: int) -> str: ...


class LLMBackend(Protocol):
    def reply(self, user_text: str, history: list[dict[str, str]]) -> str: ...


class TTSBackend(Protocol):
    def synthesize(self, text: str, sample_rate: int) -> bytes: ...
