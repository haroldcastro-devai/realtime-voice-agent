from __future__ import annotations

import time
import uuid

from rva.backends.base import LLMBackend, STTBackend, TTSBackend
from rva.config import Settings
from rva.metrics import STORE, TurnMetrics


class ConversationPipeline:
    def __init__(
        self,
        settings: Settings,
        stt: STTBackend,
        llm: LLMBackend,
        tts: TTSBackend,
        call_id: str | None = None,
    ) -> None:
        self.settings = settings
        self.stt = stt
        self.llm = llm
        self.tts = tts
        self.call_id = call_id or uuid.uuid4().hex[:12]
        self.history: list[dict[str, str]] = []

    def handle_utterance(self, pcm: bytes) -> bytes:
        t0 = time.perf_counter()
        transcript = self.stt.transcribe(pcm, self.settings.sample_rate)
        t1 = time.perf_counter()
        reply = self.llm.reply(transcript, self.history)
        t2 = time.perf_counter()
        audio = self.tts.synthesize(reply, self.settings.sample_rate)
        t3 = time.perf_counter()

        self.history.append({"role": "user", "content": transcript})
        self.history.append({"role": "assistant", "content": reply})

        STORE.record_turn(
            TurnMetrics(
                call_id=self.call_id,
                stt_ms=(t1 - t0) * 1000,
                llm_ms=(t2 - t1) * 1000,
                tts_ms=(t3 - t2) * 1000,
                total_ms=(t3 - t0) * 1000,
                transcript=transcript,
                reply=reply,
                ts=time.time(),
            )
        )
        return audio
