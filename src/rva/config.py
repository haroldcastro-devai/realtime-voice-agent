from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    log_level: str = "INFO"
    listen_host: str = "0.0.0.0"
    dashboard_port: int = 8080
    audiosocket_port: int = 9092

    stt_backend: str = "mock"
    llm_backend: str = "mock"
    tts_backend: str = "mock"

    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_llm_model: str = "gpt-4o-mini"
    openai_stt_model: str = "whisper-1"
    openai_tts_model: str = "tts-1"
    openai_tts_voice: str = "alloy"

    agent_name: str = "Ava"
    agent_system_prompt: str = (
        "You are Ava, a concise phone assistant. "
        "Keep answers under two sentences."
    )

    sample_rate: int = 8000
    frame_ms: int = 20
    barge_in_enabled: bool = True
    energy_barge_threshold: float = 1800.0

    @property
    def frame_bytes(self) -> int:
        return int(self.sample_rate * (self.frame_ms / 1000) * 2)


@lru_cache
def get_settings() -> Settings:
    return Settings()
