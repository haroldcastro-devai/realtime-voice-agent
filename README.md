# realtime-voice-agent

Independent **real-time voice agent** for lab and interview demos.

A phone-style loop: **audio in → STT → LLM → TTS → audio out**, with **barge-in**, a **queued lab dialer**, and a **latency dashboard**. The AudioSocket server speaks the public Asterisk framing so a PBX can stream 8 kHz PCM into the process.

This repository is **original code** (MIT), written for a public portfolio. It is **not** a copy of any employer's product, it is **not** affiliated with any carrier or contact-center vendor, and it contains **no** production prompts, campaign catalogs, customer lists, or tenant infrastructure.

## What you can show

| Piece | Role |
|---|---|
| `ConversationPipeline` | One conversational turn with timing |
| `AudioSocketServer` | Accept Asterisk AudioSocket calls |
| `CallSession` | Energy VAD, utterance assembly, barge-in counter |
| `CampaignDialer` | In-process job queue (wire ARI originate in your lab) |
| Dashboard `:8080` | Live STT / LLM / TTS milliseconds |

Default backends are **mocks**, so a laptop can run the demo without GPU or paid APIs.

**Split used for interviews:** GPU work (NVIDIA NeMo STT/TTS) on **Google Colab**; everything else on your PC (dashboard, VAD, AudioSocket, dialer, LLM).

```
PC (no GPU)                         Colab T4
AudioSocket + VAD + dashboard  -->  POST /stt  NeMo ASR
LLM (mock or API)              <--  POST /tts  NeMo FastPitch
```

1. Open [`notebooks/colab_nemo_gpu.ipynb`](notebooks/colab_nemo_gpu.ipynb) with a T4 runtime.  
2. Paste the printed URL into `.env`:

```
STT_BACKEND=remote
TTS_BACKEND=remote
LLM_BACKEND=mock
REMOTE_INFERENCE_URL=https://....ngrok-free.app
REMOTE_INFERENCE_TOKEN=lab-token-change-me
```

3. On the PC: `python -m rva.cli serve` — still CPU-only.

Set `*_BACKEND=openai_compat` if you prefer a cloud API instead of Colab.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest -q
python -m rva.cli mock-call
python -m rva.cli serve
```

Open http://127.0.0.1:8080 — queue a lab dial and watch mock turns if you drive AudioSocket, or run `mock-call` for a single offline turn.

## Architecture

```
Softphone / Asterisk  --AudioSocket PCM 8 kHz-->  CallSession
                                                   |  VAD + barge-in
                                                   v
                                            ConversationPipeline
                                          STT  →  LLM  →  TTS
                                                   |
                                                   +--> MetricsStore → dashboard
```

Asterisk, Triton, or a specific LLM vendor are **optional adapters**. The core package only depends on FastAPI, httpx, and numpy.

## What this is not

- Not a drop-in replacement for a production ACD.
- Not a predictive dialer integrated with a live campaign engine.
- Not a dump of proprietary dialplans, prompts, or operator rate cards.

If you need a full PBX lab, install Asterisk yourself and point an AudioSocket dialplan at `AUDIOSOCKET_PORT` (default 9092).

## License

MIT. See [LICENSE](LICENSE).
