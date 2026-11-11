"""HTTP client for a GPU inference box (Google Colab + NeMo)."""

from __future__ import annotations

from io import BytesIO
from wave import Wave_read, Wave_write

import httpx

from rva.audio_io import resample_pcm16


class RemoteInferenceError(RuntimeError):
    pass


class RemoteSTT:
    def __init__(self, base_url: str, token: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def transcribe(self, pcm: bytes, sample_rate: int) -> str:
        wav = _pcm16_to_wav(resample_pcm16(pcm, sample_rate, 16000), 16000)
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self.base_url}/stt",
                headers=_headers(self.token),
                files={"file": ("utterance.wav", wav, "audio/wav")},
            )
        _raise(response)
        return str(response.json().get("text") or "").strip()


class RemoteTTS:
    def __init__(self, base_url: str, token: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def synthesize(self, text: str, sample_rate: int) -> bytes:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self.base_url}/tts",
                headers=_headers(self.token),
                json={"text": text},
            )
        _raise(response)
        pcm, rate = _wav_to_pcm16(response.content)
        return resample_pcm16(pcm, rate, sample_rate)


def _headers(token: str) -> dict[str, str]:
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _raise(response: httpx.Response) -> None:
    if response.status_code >= 400:
        raise RemoteInferenceError(f"Colab inference HTTP {response.status_code}")
    response.raise_for_status()


def _pcm16_to_wav(pcm: bytes, sample_rate: int) -> bytes:
    bio = BytesIO()
    with Wave_write(bio) as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)
    return bio.getvalue()


def _wav_to_pcm16(blob: bytes) -> tuple[bytes, int]:
    with Wave_read(BytesIO(blob)) as wav:
        rate = wav.getframerate()
        width = wav.getsampwidth()
        channels = wav.getnchannels()
        frames = wav.readframes(wav.getnframes())
    if width != 2 or channels != 1:
        raise RemoteInferenceError("Colab TTS must return mono PCM16 WAV")
    return frames, rate
