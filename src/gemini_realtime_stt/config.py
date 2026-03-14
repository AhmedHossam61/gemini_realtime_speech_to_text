import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    google_api_key: str
    chunk_duration_sec: int = 5
    target_language: str = "English"
    source_language: str = "auto"
    output_file: str = "translation_output.txt"
    model_name: str = "gemini-2.0-flash"
    sample_rate: int = 16000
    channels: int = 1
    frames_per_buffer: int = 1024
    silence_rms_threshold: float = 50.0
    debug_audio: bool = False


    @property
    def record_seconds(self) -> int:
        return self.chunk_duration_sec


def load_config() -> AppConfig:
    # Load .env from project root if present, without overriding pre-set env vars.
    load_dotenv(override=False)

    return AppConfig(
        google_api_key=os.environ.get("GOOGLE_API_KEY", ""),
        chunk_duration_sec=int(os.environ.get("CHUNK_DURATION_SEC", 5)),
        target_language=os.environ.get("TARGET_LANGUAGE", "English"),
        source_language=os.environ.get("SOURCE_LANGUAGE", "auto"),
        output_file=os.environ.get("OUTPUT_FILE", "translation_output.txt"),
        model_name=os.environ.get("MODEL_NAME", "gemini-2.0-flash"),
        sample_rate=int(os.environ.get("SAMPLE_RATE", 16000)),
        channels=int(os.environ.get("CHANNELS", 1)),
        frames_per_buffer=int(os.environ.get("FRAMES_PER_BUFFER", 1024)),
        silence_rms_threshold=float(os.environ.get("SILENCE_RMS_THRESHOLD", 50.0)),
        debug_audio=os.environ.get("DEBUG_AUDIO", "false").lower() == "true",
    )
