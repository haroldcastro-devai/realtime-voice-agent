from __future__ import annotations

from io import BytesIO
from typing import Any
from wave import Wave_write

import httpx


class OpenAICompatError(RuntimeError):
    pass


class OpenAICompatSTT:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def transcribe(self, pcm: bytes, sample_rate: int) -> str:
        if not self.api_key:
            raise OpenAICompatError("OPENAI_API_KEY is empty")
        wav = _pcm16_to_wav(pcm, sample_rate)
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"file": ("utterance.wav", wav, "audio/wav")},
                data={"model": self.model},
            )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        return str(payload.get("text") or "").strip()


class OpenAICompatLLM:
    def __init__(self, base_url: str, api_key: str, model: str, system_prompt: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt

    def reply(self, user_text: str, history: list[dict[str, str]]) -> str:
        if not self.api_key:
            raise OpenAICompatError("OPENAI_API_KEY is empty")
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(history[-8:])
        messages.append({"role": "user", "content": user_text})
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": messages, "temperature": 0.4},
            )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"].strip()


class OpenAICompatTTS:
    def __init__(self, base_url: str, api_key: str, model: str, voice: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.voice = voice

    def synthesize(self, text: str, sample_rate: int) -> bytes:
        if not self.api_key:
            raise OpenAICompatError("OPENAI_API_KEY is empty")
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/audio/speech",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "voice": self.voice, "input": text, "response_format": "pcm"},
            )
        response.raise_for_status()
        pcm = response.content
        if sample_rate == 8000:
            return _downsample_pcm16(pcm, 24000, 8000)
        return pcm


def _downsample_pcm16(pcm: bytes, src_rate: int, dst_rate: int) -> bytes:
    if src_rate == dst_rate or len(pcm) < 4:
        return pcm
    step = src_rate / dst_rate
    n_src = len(pcm) // 2
    n_dst = int(n_src / step)
    out = bytearray(n_dst * 2)
    for i in range(n_dst):
        src_index = int(i * step)
        if src_index >= n_src:
            break
        out[i * 2 : i * 2 + 2] = pcm[src_index * 2 : src_index * 2 + 2]
    return bytes(out)


def _pcm16_to_wav(pcm: bytes, sample_rate: int) -> bytes:
    bio = BytesIO()
    with Wave_write(bio) as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)
    return bio.getvalue()
