"""Asterisk AudioSocket framing (public protocol).

Each message is: 1-byte kind + 2-byte big-endian length + payload.
Kinds used here: hangup 0x00, UUID 0x01, PCM 0x10.
"""

from __future__ import annotations

import socket
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass

KIND_HANGUP = 0x00
KIND_UUID = 0x01
KIND_PCM = 0x10


@dataclass
class SocketMessage:
    kind: int
    payload: bytes


def encode(kind: int, payload: bytes = b"") -> bytes:
    if len(payload) > 65535:
        raise ValueError("AudioSocket payload too large")
    return bytes([kind, (len(payload) >> 8) & 0xFF, len(payload) & 0xFF]) + payload


def read_message(sock: socket.socket) -> SocketMessage | None:
    header = _recv_exact(sock, 3)
    if header is None:
        return None
    kind = header[0]
    length = (header[1] << 8) | header[2]
    payload = b""
    if length:
        body = _recv_exact(sock, length)
        if body is None:
            return None
        payload = body
    return SocketMessage(kind=kind, payload=payload)


def _recv_exact(sock: socket.socket, n: int) -> bytes | None:
    chunks = bytearray()
    while len(chunks) < n:
        piece = sock.recv(n - len(chunks))
        if not piece:
            return None
        chunks.extend(piece)
    return bytes(chunks)


class AudioSocketServer:
    def __init__(self, host: str, port: int, on_call: Callable[[socket.socket, str], None]) -> None:
        self.host = host
        self.port = port
        self.on_call = on_call
        self._sock: socket.socket | None = None
        self._stop = threading.Event()

    def serve_forever(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(32)
        self._sock.settimeout(1.0)
        while not self._stop.is_set():
            try:
                conn, _addr = self._sock.accept()
            except TimeoutError:
                continue
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def stop(self) -> None:
        self._stop.set()
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass

    def _handle(self, conn: socket.socket) -> None:
        call_id = uuid.uuid4().hex[:12]
        try:
            first = read_message(conn)
            if first and first.kind == KIND_UUID and first.payload:
                try:
                    call_id = str(uuid.UUID(bytes=first.payload))
                except ValueError:
                    call_id = first.payload.decode("ascii", "ignore") or call_id
            self.on_call(conn, call_id)
        finally:
            try:
                conn.close()
            except OSError:
                pass
