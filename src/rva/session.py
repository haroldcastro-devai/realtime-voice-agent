from __future__ import annotations

import logging
import socket

from rva.audiosocket import KIND_HANGUP, KIND_PCM, encode, read_message
from rva.config import Settings
from rva.metrics import STORE
from rva.pipeline import ConversationPipeline
from rva.vad import is_speech, rms

log = logging.getLogger("rva.session")


class CallSession:
    def __init__(self, conn: socket.socket, pipeline: ConversationPipeline, settings: Settings) -> None:
        self.conn = conn
        self.pipeline = pipeline
        self.settings = settings
        self._speaking = False
        self._utterance = bytearray()
        self._silence_frames = 0

    def run(self) -> None:
        STORE.start_call()
        try:
            greeting = self.pipeline.tts.synthesize(
                f"Hi, this is {self.settings.agent_name}. How can I help?",
                self.settings.sample_rate,
            )
            self._play(greeting)
            while True:
                msg = read_message(self.conn)
                if msg is None or msg.kind == KIND_HANGUP:
                    break
                if msg.kind != KIND_PCM or not msg.payload:
                    continue
                self._on_pcm(msg.payload)
        except OSError as exc:
            log.info("call %s closed: %s", self.pipeline.call_id, exc)
        finally:
            STORE.finish_call()

    def _on_pcm(self, pcm: bytes) -> None:
        energy = rms(pcm)
        talking = is_speech(pcm, self.settings.energy_barge_threshold)
        if talking:
            if self._speaking is False and self.settings.barge_in_enabled and energy > self.settings.energy_barge_threshold:
                STORE.barge_in()
            self._speaking = True
            self._utterance.extend(pcm)
            self._silence_frames = 0
            return
        if not self._speaking:
            return
        self._silence_frames += 1
        self._utterance.extend(pcm)
        hangover = int(400 / self.settings.frame_ms)
        if self._silence_frames < hangover:
            return
        blob = bytes(self._utterance)
        self._utterance.clear()
        self._speaking = False
        self._silence_frames = 0
        if len(blob) < self.settings.frame_bytes * 4:
            return
        reply_audio = self.pipeline.handle_utterance(blob)
        self._play(reply_audio)

    def _play(self, pcm: bytes) -> None:
        frame = self.settings.frame_bytes
        for offset in range(0, len(pcm), frame):
            chunk = pcm[offset : offset + frame]
            if len(chunk) < frame:
                chunk = chunk + b"\x00" * (frame - len(chunk))
            try:
                self.conn.sendall(encode(KIND_PCM, chunk))
            except OSError:
                return
