from __future__ import annotations

from rva.backends.base import LLMBackend, STTBackend, TTSBackend
from rva.backends.mock import MockLLM, MockSTT, MockTTS
from rva.backends.openai_compat import OpenAICompatLLM, OpenAICompatSTT, OpenAICompatTTS
from rva.config import Settings


def build_backends(settings: Settings) -> tuple[STTBackend, LLMBackend, TTSBackend]:
    stt: STTBackend
    llm: LLMBackend
    tts: TTSBackend

    if settings.stt_backend == "openai_compat":
        stt = OpenAICompatSTT(settings.openai_base_url, settings.openai_api_key, settings.openai_stt_model)
    else:
        stt = MockSTT()

    if settings.llm_backend == "openai_compat":
        llm = OpenAICompatLLM(
            settings.openai_base_url,
            settings.openai_api_key,
            settings.openai_llm_model,
            settings.agent_system_prompt,
        )
    else:
        llm = MockLLM(settings.agent_name)

    if settings.tts_backend == "openai_compat":
        tts = OpenAICompatTTS(
            settings.openai_base_url,
            settings.openai_api_key,
            settings.openai_tts_model,
            settings.openai_tts_voice,
        )
    else:
        tts = MockTTS()

    return stt, llm, tts
