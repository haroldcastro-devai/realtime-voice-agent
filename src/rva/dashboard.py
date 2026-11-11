from __future__ import annotations

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse

from rva import __version__
from rva.dialer import DIALER
from rva.metrics import STORE

app = FastAPI(title="Realtime Voice Agent", version=__version__)

_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Realtime Voice Agent</title>
  <style>
    :root { color-scheme: dark; }
    body { font-family: ui-sans-serif, system-ui, sans-serif; margin: 2rem; background: #0f1419; color: #e7ecf1; }
    h1 { font-size: 1.4rem; }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(8rem, 1fr)); gap: 1rem; }
    .card { background: #1b232c; padding: 1rem; border-radius: 12px; }
    table { width: 100%; border-collapse: collapse; margin-top: 1.5rem; font-size: .9rem; }
    th, td { text-align: left; padding: .45rem .3rem; border-bottom: 1px solid #2c3640; }
    input, button { padding: .45rem .7rem; border-radius: 8px; border: 0; }
    button { background: #3d8bfd; color: white; cursor: pointer; }
    .muted { color: #9aa8b5; font-size: .85rem; }
  </style>
</head>
<body>
  <h1>Realtime Voice Agent</h1>
  <p class="muted">Independent lab dashboard — latency per turn, barge-in count, queued lab dials.</p>
  <div class="grid">
    <div class="card">Calls started<br><strong id="cs">0</strong></div>
    <div class="card">Calls finished<br><strong id="cf">0</strong></div>
    <div class="card">Barge-in<br><strong id="bi">0</strong></div>
    <div class="card">Avg turn (ms)<br><strong id="avg">0</strong></div>
  </div>
  <form method="post" action="/dial" style="margin-top:1.2rem">
    <input name="target" placeholder="sip:1001@127.0.0.1" value="sip:1001@127.0.0.1"/>
    <button type="submit">Queue lab dial</button>
  </form>
  <table>
    <thead><tr><th>Call</th><th>STT</th><th>LLM</th><th>TTS</th><th>Total</th><th>Heard</th></tr></thead>
    <tbody id="rows"></tbody>
  </table>
  <script>
    async function tick() {
      const m = await fetch('/api/metrics').then(r => r.json());
      document.getElementById('cs').textContent = m.calls_started;
      document.getElementById('cf').textContent = m.calls_finished;
      document.getElementById('bi').textContent = m.barge_ins;
      document.getElementById('avg').textContent = m.avg_turn_ms;
      document.getElementById('rows').innerHTML = m.turns.map(t =>
        `<tr><td>${t.call_id}</td><td>${t.stt_ms.toFixed(0)}</td><td>${t.llm_ms.toFixed(0)}</td>
         <td>${t.tts_ms.toFixed(0)}</td><td>${t.total_ms.toFixed(0)}</td>
         <td>${(t.transcript || '').slice(0,80)}</td></tr>`
      ).join('');
    }
    tick(); setInterval(tick, 1500);
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return _PAGE


@app.get("/api/metrics")
def metrics() -> JSONResponse:
    return JSONResponse(STORE.snapshot())


@app.get("/api/dialer")
def dialer() -> JSONResponse:
    return JSONResponse(DIALER.snapshot())


@app.post("/dial")
def dial(target: str = Form(...)) -> HTMLResponse:
    DIALER.enqueue(target)
    return HTMLResponse(_PAGE, status_code=201)
