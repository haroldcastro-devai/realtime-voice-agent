from __future__ import annotations

import argparse
import logging
import socket
import threading

from rva.audiosocket import AudioSocketServer
from rva.backends.factory import build_backends
from rva.config import get_settings
from rva.pipeline import ConversationPipeline
from rva.session import CallSession


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="rva")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("mock-call", help="Run one in-process STT→LLM→TTS turn")
    sub.add_parser("serve", help="Dashboard + AudioSocket server")
    args = parser.parse_args(argv)

    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    stt, llm, tts = build_backends(settings)

    if args.cmd == "mock-call":
        pipeline = ConversationPipeline(settings, stt, llm, tts, call_id="mock")
        silence = b"\x00\x00" * settings.sample_rate
        audio = pipeline.handle_utterance(silence)
        last = pipeline.history[-1]["content"]
        print(f"reply: {last}")
        print(f"tts_bytes: {len(audio)}")
        return

    if args.cmd == "serve":
        import uvicorn

        from rva import dashboard

        def on_call(conn: socket.socket, call_id: str) -> None:
            pipeline = ConversationPipeline(settings, stt, llm, tts, call_id=call_id)
            CallSession(conn, pipeline, settings).run()

        server = AudioSocketServer(settings.listen_host, settings.audiosocket_port, on_call)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        logging.getLogger("rva").info("AudioSocket on %s:%s", settings.listen_host, settings.audiosocket_port)
        uvicorn.run(dashboard.app, host=settings.listen_host, port=settings.dashboard_port, log_level="info")


if __name__ == "__main__":
    main()
