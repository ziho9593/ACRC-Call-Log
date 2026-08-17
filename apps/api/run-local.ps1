$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$env:STT_PROVIDER = "faster-whisper"
$env:WHISPER_MODEL_PATH = "../../storage/models/whisper-large-v3"
$env:WHISPER_DEVICE = "cpu"
$env:WHISPER_COMPUTE_TYPE = "int8"
$env:WHISPER_LANGUAGE = "ko"
$env:WHISPER_PREPROCESS_AUDIO = "true"
$env:WHISPER_INITIAL_PROMPT = ""
$env:WHISPER_HOTWORDS = ""
$env:WHISPER_CONDITION_ON_PREVIOUS_TEXT = "false"
$env:WHISPER_VAD_THRESHOLD = "0.5"

$env:DIARIZATION_PROVIDER = "pyannote"
$env:DIARIZATION_MODEL_PATH = "../../storage/models/pyannote-speaker-diarization-community-1"
$env:DIARIZATION_DEVICE = "cpu"
$env:DIARIZATION_MIN_SPEAKERS = "2"
$env:DIARIZATION_MAX_SPEAKERS = "2"
$env:PYANNOTE_METRICS_ENABLED = "0"

$env:ANALYSIS_PROVIDER = "ollama"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:OLLAMA_MODEL = "qwen3.5:4b"

& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
