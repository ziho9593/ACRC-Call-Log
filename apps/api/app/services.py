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


def preprocess_audio_for_stt(audio_path: Path, processed_dir: Path, call_id: str) -> Path:
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / f"{call_id}-stt.wav"
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(audio_path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-af",
                "highpass=f=80,lowpass=f=7600,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11",
                "-c:a",
                "pcm_s16le",
                str(output_path),
            ],
            capture_output=True,
            timeout=300,
            check=True,
        )
    except Exception:
        output_path.unlink(missing_ok=True)
        raise
    return output_path


def process_call(call_id: str) -> None:
    row = db.get_call_record(call_id)
    if row is None:
        return

    db.update_status(call_id, "PROCESSING")
    settings = get_settings()
    temporary_stt_path: Path | None = None
    try:
        audio_path = Path(row["storage_path"])
        stt_path = str(audio_path)
        if settings.stt_provider == "mock" and row["original_filename"].lower().startswith("fail"):
            stt_path = f"{audio_path}-force-fail"
        elif settings.stt_provider == "faster-whisper" and settings.whisper_preprocess_audio:
            try:
                temporary_stt_path = preprocess_audio_for_stt(
                    audio_path,
                    settings.processed_dir,
                    call_id,
                )
                stt_path = str(temporary_stt_path)
            except (OSError, subprocess.SubprocessError):
                temporary_stt_path = None

        transcript = get_stt_provider(
            settings.stt_provider,
            settings.whisper_model_path,
            settings.whisper_device,
            settings.whisper_compute_type,
            settings.whisper_language,
            settings.whisper_initial_prompt,
            settings.whisper_hotwords,
            settings.whisper_condition_on_previous_text,
            settings.whisper_vad_threshold,
            settings.whisper_min_silence_duration_ms,
            settings.whisper_speech_pad_ms,
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
    finally:
        if temporary_stt_path is not None:
            temporary_stt_path.unlink(missing_ok=True)
