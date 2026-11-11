from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import asdict, dataclass


@dataclass
class TurnMetrics:
    call_id: str
    stt_ms: float
    llm_ms: float
    tts_ms: float
    total_ms: float
    transcript: str
    reply: str
    ts: float


class MetricsStore:
    def __init__(self, maxlen: int = 200) -> None:
        self._lock = threading.Lock()
        self._turns: deque[TurnMetrics] = deque(maxlen=maxlen)
        self.calls_started = 0
        self.calls_finished = 0
        self.barge_ins = 0

    def start_call(self) -> None:
        with self._lock:
            self.calls_started += 1

    def finish_call(self) -> None:
        with self._lock:
            self.calls_finished += 1

    def barge_in(self) -> None:
        with self._lock:
            self.barge_ins += 1

    def record_turn(self, turn: TurnMetrics) -> None:
        with self._lock:
            self._turns.append(turn)

    def snapshot(self) -> dict:
        with self._lock:
            turns = [asdict(t) for t in self._turns]
            totals = [t.total_ms for t in self._turns]
        avg = sum(totals) / len(totals) if totals else 0.0
        return {
            "calls_started": self.calls_started,
            "calls_finished": self.calls_finished,
            "barge_ins": self.barge_ins,
            "avg_turn_ms": round(avg, 1),
            "turns": list(reversed(turns))[:40],
            "now": time.time(),
        }


STORE = MetricsStore()
