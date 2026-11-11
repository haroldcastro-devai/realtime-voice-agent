"""GPU inference process for Google Colab (or any CUDA host).

Local PCs should NOT import this file. They call HTTP /stt and /tts instead.

Public NeMo checkpoints only — no tenant models.
"""

from __future__ import annotations

import io
import os
from functools import lru_cache

import numpy as np
import soundfile as sf
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

TOKEN = os.getenv("INFERENCE_TOKEN", "")
ASR_NAME = os.getenv("NEMO_ASR_MODEL", "nvidia/stt_multilingual_fastconformer_hybrid_large_pc")
TTS_SPEC_NAME = os.getenv("NEMO_TTS_SPEC", "tts_en_fastpitch")
TTS_VOCODER_NAME = os.getenv("NEMO_TTS_VOCODER", "tts_en_hifigan")

app = FastAPI(title="NeMo GPU inference", version="0.1.0")


def _auth(authorization: str | None) -> None:
    if not TOKEN:
        return
    expected = f"Bearer {TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="unauthorized")


@lru_cache
def asr_model():
    import nemo.collections.asr as nemo_asr

    return nemo_asr.models.ASRModel.from_pretrained(ASR_NAME)


@lru_cache
def tts_models():
    from nemo.collections.tts.models import FastPitchModel, HifiGanModel

    spec = FastPitchModel.from_pretrained(TTS_SPEC_NAME).eval().cuda()
    vocoder = HifiGanModel.from_pretrained(TTS_VOCODER_NAME).eval().cuda()
    return spec, vocoder


class TtsIn(BaseModel):
    text: str


@app.get("/health")
def health() -> dict:
    return {"ok": True, "asr": ASR_NAME, "tts": TTS_SPEC_NAME}


@app.post("/stt")
def stt(file: UploadFile = File(...), authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    raw = file.file.read()
    audio, rate = sf.read(io.BytesIO(raw), dtype="float32", always_2d=False)
    if getattr(audio, "ndim", 1) > 1:
        audio = np.mean(audio, axis=1)
    path = "/tmp/rva_utt.wav"
    sf.write(path, audio, rate)
    text = asr_model().transcribe([path])[0]
    if hasattr(text, "text"):
        text = text.text
    return {"text": str(text).strip()}


@app.post("/tts")
def tts(body: TtsIn, authorization: str | None = Header(default=None)) -> Response:
    _auth(authorization)
    spec, vocoder = tts_models()
    parsed = spec.parse(body.text or "hello")
    spectrogram = spec.generate_spectrogram(tokens=parsed)
    audio = vocoder.convert_spectrogram_to_audio(spec=spectrogram)
    wav = audio.to("cpu").detach().numpy().flatten().astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, wav, 22050, format="WAV", subtype="PCM_16")
    return Response(content=buf.getvalue(), media_type="audio/wav")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
