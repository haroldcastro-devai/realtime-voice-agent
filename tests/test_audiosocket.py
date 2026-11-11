from rva.audiosocket import KIND_PCM, encode, read_message


class FakeSock:
    def __init__(self, blob: bytes) -> None:
        self._buf = blob

    def recv(self, n: int) -> bytes:
        chunk, self._buf = self._buf[:n], self._buf[n:]
        return chunk


def test_roundtrip_pcm_frame() -> None:
    payload = b"\x01\x02" * 10
    framed = encode(KIND_PCM, payload)
    msg = read_message(FakeSock(framed))
    assert msg is not None
    assert msg.kind == KIND_PCM
    assert msg.payload == payload
