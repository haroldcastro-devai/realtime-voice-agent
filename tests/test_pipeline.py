from rva.backends.mock import MockLLM, MockSTT, MockTTS
from rva.config import Settings
from rva.pipeline import ConversationPipeline


def test_mock_turn_returns_audio_and_history() -> None:
    settings = Settings()
    pipeline = ConversationPipeline(settings, MockSTT("order status"), MockLLM("Ava"), MockTTS(), call_id="t1")
    pcm = b"\x00\x10" * 1600
    audio = pipeline.handle_utterance(pcm)
    assert len(audio) > 1000
    assert pipeline.history[0]["content"] == "order status"
    assert "Ava" in pipeline.history[1]["content"]
