from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def resolve_project_path(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


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
    whisper_no_speech_threshold: float
    whisper_log_prob_threshold: float
    whisper_compression_ratio_threshold: float
    whisper_hallucination_silence_threshold: float
    diarization_provider: str
    diarization_model_path: Path
    diarization_device: str
    diarization_min_speakers: int | None
    diarization_max_speakers: int | None
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
    min_speakers = os.getenv("DIARIZATION_MIN_SPEAKERS", "").strip()
    max_speakers = os.getenv("DIARIZATION_MAX_SPEAKERS", "").strip()
    settings = Settings(
        stt_provider=os.getenv("STT_PROVIDER", "mock"),
        whisper_model_path=Path(os.getenv("WHISPER_MODEL_PATH", "storage/models/whisper-large-v3")),
        whisper_device=os.getenv("WHISPER_DEVICE", "cpu"),
        whisper_compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
        whisper_language=os.getenv("WHISPER_LANGUAGE", "ko"),
        whisper_preprocess_audio=os.getenv("WHISPER_PREPROCESS_AUDIO", "true").lower()
        in {"1", "true", "yes", "on"},
        whisper_initial_prompt=os.getenv("WHISPER_INITIAL_PROMPT", ""),
        whisper_hotwords=os.getenv("WHISPER_HOTWORDS", ""),
        whisper_condition_on_previous_text=os.getenv(
            "WHISPER_CONDITION_ON_PREVIOUS_TEXT", "false"
        ).lower()
        in {"1", "true", "yes", "on"},
        whisper_vad_threshold=float(os.getenv("WHISPER_VAD_THRESHOLD", "0.5")),
        whisper_min_silence_duration_ms=int(os.getenv("WHISPER_MIN_SILENCE_DURATION_MS", "700")),
        whisper_speech_pad_ms=int(os.getenv("WHISPER_SPEECH_PAD_MS", "200")),
        whisper_no_speech_threshold=float(os.getenv("WHISPER_NO_SPEECH_THRESHOLD", "0.5")),
        whisper_log_prob_threshold=float(os.getenv("WHISPER_LOG_PROB_THRESHOLD", "-0.8")),
        whisper_compression_ratio_threshold=float(
            os.getenv("WHISPER_COMPRESSION_RATIO_THRESHOLD", "2.2")
        ),
        whisper_hallucination_silence_threshold=float(
            os.getenv("WHISPER_HALLUCINATION_SILENCE_THRESHOLD", "1.0")
        ),
        diarization_provider=os.getenv("DIARIZATION_PROVIDER", "none"),
        diarization_model_path=Path(
            os.getenv(
                "DIARIZATION_MODEL_PATH",
                "storage/models/pyannote-speaker-diarization-community-1",
            )
        ),
        diarization_device=os.getenv("DIARIZATION_DEVICE", "cpu"),
        diarization_min_speakers=int(min_speakers) if min_speakers else None,
        diarization_max_speakers=int(max_speakers) if max_speakers else None,
        analysis_provider=os.getenv("ANALYSIS_PROVIDER", "mock"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen3.5:4b"),
        ollama_timeout_seconds=float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180")),
        ollama_context_window=int(os.getenv("OLLAMA_CONTEXT_WINDOW", "32768")),
        ollama_max_input_chars=int(os.getenv("OLLAMA_MAX_INPUT_CHARS", "40000")),
        database_path=resolve_project_path(os.getenv("DATABASE_PATH", "storage/acrc_call_log.db")),
        upload_dir=resolve_project_path(os.getenv("UPLOAD_DIR", "storage/uploads")),
        processed_dir=resolve_project_path(os.getenv("PROCESSED_DIR", "storage/processed")),
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(100 * 1024 * 1024))),
        cors_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
    )
    if settings.stt_provider == "mock" and settings.diarization_provider != "none":
        raise ValueError(
            "화자분리를 사용할 때는 STT_PROVIDER=faster-whisper를 함께 설정해야 합니다."
        )
    return settings
