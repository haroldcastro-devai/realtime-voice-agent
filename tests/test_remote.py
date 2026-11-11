from rva.backends.remote import RemoteSTT, RemoteTTS
from rva.config import Settings
from rva.backends.factory import build_backends


class DummyResp:
    def __init__(self, status_code=200, json_data=None, content=b"") -> None:
        self.status_code = status_code
        self._json = json_data or {}
        self.content = content

    def json(self):
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("http error")


def test_remote_stt_reads_text(monkeypatch) -> None:
    import rva.backends.remote as remote

    def fake_post(*_a, **_k):
        return DummyResp(json_data={"text": "hola"})

    class DummyClient:
        def __enter__(self):
            return self

        def __exit__(self, *_a):
            return False

        def post(self, *a, **k):
            return fake_post()

    monkeypatch.setattr(remote.httpx, "Client", lambda **_k: DummyClient())
    assert RemoteSTT("http://colab.example").transcribe(b"\x00\x10" * 800, 8000) == "hola"


def test_factory_remote_requires_url() -> None:
    settings = Settings(stt_backend="remote", tts_backend="mock", remote_inference_url="")
    try:
        build_backends(settings)
        assert False, "expected ValueError"
    except ValueError:
        pass
