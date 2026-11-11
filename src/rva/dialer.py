"""In-process campaign dialer.

This is a queue of synthetic (or ARI-originated) calls. It does not talk to
any third-party predictive dialer. Wire `originate` to Asterisk ARI in your lab.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field

from rva.metrics import STORE


@dataclass
class DialJob:
    job_id: str
    target: str
    status: str
    created_at: float
    note: str = ""


@dataclass
class CampaignDialer:
    name: str = "lab-campaign"
    jobs: list[DialJob] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def enqueue(self, target: str) -> DialJob:
        job = DialJob(
            job_id=uuid.uuid4().hex[:10],
            target=target,
            status="queued",
            created_at=time.time(),
            note="Lab job. Attach ARI originate in a real PBX.",
        )
        with self._lock:
            self.jobs.append(job)
        return job

    def mark_dialing(self, job_id: str) -> None:
        with self._lock:
            for job in self.jobs:
                if job.job_id == job_id:
                    job.status = "dialing"
                    STORE.start_call()
                    return

    def snapshot(self) -> dict:
        with self._lock:
            jobs = [
                {
                    "job_id": j.job_id,
                    "target": j.target,
                    "status": j.status,
                    "created_at": j.created_at,
                    "note": j.note,
                }
                for j in reversed(self.jobs[-50:])
            ]
        return {"campaign": self.name, "jobs": jobs}


DIALER = CampaignDialer()
