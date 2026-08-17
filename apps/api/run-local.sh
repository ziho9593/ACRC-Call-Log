#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

export STT_PROVIDER=faster-whisper
export WHISPER_MODEL_PATH=../../storage/models/whisper-large-v3
export WHISPER_DEVICE=cpu
export WHISPER_COMPUTE_TYPE=int8
export WHISPER_LANGUAGE=ko
export WHISPER_PREPROCESS_AUDIO=true
export WHISPER_INITIAL_PROMPT=
export WHISPER_HOTWORDS=
export WHISPER_CONDITION_ON_PREVIOUS_TEXT=false
export WHISPER_VAD_THRESHOLD=0.5

export DIARIZATION_PROVIDER=pyannote
export DIARIZATION_MODEL_PATH=../../storage/models/pyannote-speaker-diarization-community-1
export DIARIZATION_DEVICE=cpu
export DIARIZATION_MIN_SPEAKERS=2
export DIARIZATION_MAX_SPEAKERS=2
export PYANNOTE_METRICS_ENABLED=0

export ANALYSIS_PROVIDER=ollama
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen3.5:4b

exec .venv/Scripts/python.exe -m uvicorn app.main:app --reload
