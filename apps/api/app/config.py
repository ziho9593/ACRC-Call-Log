from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    stt_provider: str
    whisper_model_path: Path
    whisper_device: str
    whisper_compute_type: str
    whisper_language: str
    whisper_preprocess_audio: bool
    whisper_initial_prompt: str
    whisper_hotwords: str
    whisper_condition_on_previous_text: bool
    whisper_vad_threshold: float
    whisper_min_silence_duration_ms: int
    whisper_speech_pad_ms: int
    analysis_provider: str
    ollama_base_url: str
    ollama_model: str
    ollama_timeout_seconds: float
    ollama_context_window: int
    ollama_max_input_chars: int
    database_path: Path
    upload_dir: Path
    processed_dir: Path
    max_upload_bytes: int
    cors_origins: list[str]


def get_settings() -> Settings:
    origins = os.getenv(
        "API_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return Settings(
        stt_provider=os.getenv("STT_PROVIDER", "mock"),
        whisper_model_path=Path(os.getenv("WHISPER_MODEL_PATH", "storage/models/whisper-large-v3")),
        whisper_device=os.getenv("WHISPER_DEVICE", "cpu"),
        whisper_compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
        whisper_language=os.getenv("WHISPER_LANGUAGE", "ko"),
        whisper_preprocess_audio=os.getenv("WHISPER_PREPROCESS_AUDIO", "true").lower()
        in {"1", "true", "yes", "on"},
        whisper_initial_prompt=os.getenv(
            "WHISPER_INITIAL_PROMPT",
            "국민권익위원회 상담 통화입니다. 민원, 접수번호, 담당 부서, "
            "처리 상태를 정확히 전사하세요.",
        ),
        whisper_hotwords=os.getenv(
            "WHISPER_HOTWORDS",
            "국민권익위원회, 민원, 접수번호, 담당 부서, 처리 상태, 상담원",
        ),
        whisper_condition_on_previous_text=os.getenv(
            "WHISPER_CONDITION_ON_PREVIOUS_TEXT", "false"
        ).lower()
        in {"1", "true", "yes", "on"},
        whisper_vad_threshold=float(os.getenv("WHISPER_VAD_THRESHOLD", "0.35")),
        whisper_min_silence_duration_ms=int(os.getenv("WHISPER_MIN_SILENCE_DURATION_MS", "500")),
        whisper_speech_pad_ms=int(os.getenv("WHISPER_SPEECH_PAD_MS", "400")),
        analysis_provider=os.getenv("ANALYSIS_PROVIDER", "mock"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen3.5:4b"),
        ollama_timeout_seconds=float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180")),
        ollama_context_window=int(os.getenv("OLLAMA_CONTEXT_WINDOW", "32768")),
        ollama_max_input_chars=int(os.getenv("OLLAMA_MAX_INPUT_CHARS", "40000")),
        database_path=Path(os.getenv("DATABASE_PATH", "storage/acrc_call_log.db")),
        upload_dir=Path(os.getenv("UPLOAD_DIR", "storage/uploads")),
        processed_dir=Path(os.getenv("PROCESSED_DIR", "storage/processed")),
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(100 * 1024 * 1024))),
        cors_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
    )
