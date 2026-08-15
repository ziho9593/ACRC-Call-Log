from __future__ import annotations

import subprocess
from pathlib import Path

from . import db
from .config import get_settings
from .providers import get_analysis_provider, get_stt_provider


def probe_duration_ms(audio_path: Path) -> int | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        return int(float(result.stdout.strip()) * 1000)
    except (
        FileNotFoundError,
        ValueError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ):
        return None


def process_call(call_id: str) -> None:
    row = db.get_call_record(call_id)
    if row is None:
        return

    db.update_status(call_id, "PROCESSING")
    settings = get_settings()
    try:
        audio_path = Path(row["storage_path"])
        stt_path = str(audio_path)
        if row["original_filename"].lower().startswith("fail"):
            stt_path = f"{audio_path}-force-fail"

        transcript = get_stt_provider(
            settings.stt_provider,
            settings.whisper_model_path,
            settings.whisper_device,
            settings.whisper_compute_type,
            settings.whisper_language,
        ).transcribe(stt_path)
        probed_duration = probe_duration_ms(audio_path)
        if probed_duration:
            transcript = type(transcript)(probed_duration, transcript.utterances)

        analysis = get_analysis_provider(
            settings.analysis_provider,
            settings.ollama_base_url,
            settings.ollama_model,
            settings.ollama_timeout_seconds,
            settings.ollama_context_window,
            settings.ollama_max_input_chars,
        ).analyze(transcript)
        db.save_analysis(call_id, transcript, analysis)
    except Exception:
        db.update_status(call_id, "FAILED", "분석 처리 중 오류가 발생했습니다.")
