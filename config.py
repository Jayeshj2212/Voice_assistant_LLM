import os
from dataclasses import dataclass


@dataclass
class Settings:
    app_name: str = "AI Telecaller"
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "8000"))
    debug: bool = os.getenv("APP_DEBUG", "false").lower() == "true"

    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2")

    whisper_model: str = os.getenv("WHISPER_MODEL", "base")
    tts_engine: str = os.getenv("TTS_ENGINE", "f5")
    tts_voice: str = os.getenv("TTS_VOICE", "hi")
    piper_bin: str = os.getenv("PIPER_BIN", "/usr/local/bin/piper")
    f5_ref_audio: str = os.getenv(
        "F5_TTS_REF_AUDIO",
        "/home/jayesh/voice_agent/.venv/lib/python3.11/site-packages/f5_tts/infer/examples/basic/basic_ref_en.wav",
    )
    f5_ref_text: str = os.getenv(
        "F5_TTS_REF_TEXT",
        "Some call me nature, others call me mother nature.",
    )
    f5_ref_voice_name: str = os.getenv("F5_TTS_REF_VOICE_NAME", "default")
    piper_voice_path: str = os.getenv("PIPER_VOICE_PATH", "")

    crm_api_url: str = os.getenv("CRM_API_URL", "")
    crm_api_key: str = os.getenv("CRM_API_KEY", "")

    call_recordings_dir: str = os.getenv("CALL_RECORDINGS_DIR", "./recordings")
    transcripts_dir: str = os.getenv("TRANSCRIPTS_DIR", "./transcripts")
    summary_dir: str = os.getenv("SUMMARY_DIR", "./summaries")

    default_language: str = os.getenv("DEFAULT_LANGUAGE", "hi")
    supported_languages: list[str] = None

    def __post_init__(self):
        if self.supported_languages is None:
            self.supported_languages = ["hi", "en", "bn"]


settings = Settings()
