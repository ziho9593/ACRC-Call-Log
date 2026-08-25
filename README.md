# ACRC-Call-Log

사내 통화 녹취 분석 서비스의 PoC입니다. 사용자가 녹취 파일을 업로드하면 백엔드 background task가 선택한 Provider로 전사와 분석을 수행하고, 프론트엔드에서 타임스탬프 전사문, 전체 요약, 주요 키워드, 구간별 요약, 오디오 재생을 확인할 수 있습니다.

## 기술 스택

- Frontend: Next.js, TypeScript
- Backend: FastAPI, Python
- Database: SQLite
- File Storage: 로컬 파일 시스템
- Local Execution: Docker Compose
- Audio Processing: FFmpeg
- UI: 기본 CSS

## 디렉터리 구조

```text
ACRC-Call-Log/
├─ .devcontainer/
├─ .github/workflows/
├─ apps/
│  ├─ api/
│  └─ web/
├─ docs/
│  └─ architecture.md
├─ storage/
│  ├─ uploads/
│  ├─ processed/
│  └─ models/
├─ docker-compose.yml
├─ .env.example
└─ README.md
```

## 사전 요구사항

- Docker와 Docker Compose
- 로컬 개발 시 Python 3.12, Node.js 22, FFmpeg

## 환경 변수

`.env.example`을 참고해 `.env`를 만들 수 있습니다. 기본값은 Mock Provider입니다.

- `STT_PROVIDER`: 기본값 `mock`
- `WHISPER_MODEL_PATH`: 로컬 CTranslate2 Whisper 모델 디렉터리
- `WHISPER_DEVICE`: 기본값 `cpu` (`cuda` 사용 가능)
- `WHISPER_COMPUTE_TYPE`: 기본값 `int8` (GPU에서는 일반적으로 `float16`)
- `WHISPER_LANGUAGE`: 기본값 `ko`
- `WHISPER_PREPROCESS_AUDIO`: FFmpeg 노이즈 제거·음량 정규화 사용 여부
- `WHISPER_INITIAL_PROMPT`: 선택적 전사 문맥. 기본값은 비어 있으며 잘못 지정하면 문구가 전사문에 섞일 수 있음
- `WHISPER_HOTWORDS`: 선택적 전문 용어. 기본값은 비어 있음
- `WHISPER_CONDITION_ON_PREVIOUS_TEXT`: 이전 구간 오류의 반복 전파 여부
- `WHISPER_VAD_THRESHOLD`: 음성 감지 민감도, 기본값 `0.5`
- `WHISPER_NO_SPEECH_THRESHOLD`: 비음성 구간 제외 기준, 기본값 `0.5`
- `WHISPER_LOG_PROB_THRESHOLD`: 낮은 신뢰도 결과 제한, 기본값 `-0.8`
- `WHISPER_HALLUCINATION_SILENCE_THRESHOLD`: 긴 무음 주변 환각 제한, 기본값 `1.0`
- `ANALYSIS_PROVIDER`: 기본값 `mock`
- `OLLAMA_BASE_URL`: 로컬 Ollama API 주소
- `OLLAMA_MODEL`: 분석 모델, 기본값 `qwen3.5:4b`
- `OLLAMA_TIMEOUT_SECONDS`: 모델 분석 제한 시간, 기본값 180초
- `OLLAMA_CONTEXT_WINDOW`: 모델 컨텍스트 크기, 기본값 32768
- `OLLAMA_MAX_INPUT_CHARS`: 한 번에 분석할 최대 전사문 길이, 기본값 40000자
- `GEMINI_API_KEY`: Gemini 분석용 서버 비밀 키. 브라우저와 Git 저장소에 노출하지 않음
- `GEMINI_BASE_URL`: Gemini API 주소
- `GEMINI_MODEL`: Gemini 분석 모델, 기본값 `gemini-2.5-flash`
- `GEMINI_TIMEOUT_SECONDS`: Gemini 분석 제한 시간, 기본값 180초
- `GEMINI_MAX_INPUT_CHARS`: 한 번에 Gemini로 분석할 최대 전사문 길이, 기본값 40000자
- `DATABASE_PATH`: SQLite 파일 경로
- `UPLOAD_DIR`: 업로드 파일 저장 경로
- `PROCESSED_DIR`: 처리 산출물 저장 경로
- `MAX_UPLOAD_BYTES`: 기본 100MB
- `API_CORS_ORIGINS`: 허용할 프론트엔드 Origin (기본값은 `localhost:3000`과 `127.0.0.1:3000`)
- `NEXT_PUBLIC_API_BASE_URL`: 브라우저에서 호출할 API 주소

## Docker Compose 실행

```bash
docker compose up --build
```

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- Health Check: `http://localhost:8000/api/v1/health`

## 로컬 개발 실행

Backend:

```bash
cd apps/api
python -m venv .venv  # .venv가 이미 있으면 생략
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

이미 환경 세팅이 끝난 PC에서는 다음만 실행하면 됩니다.

```powershell
cd apps/api
.\.venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

`.venv\Scripts\python.exe` 권한 오류가 나면 활성화된 터미널이나 실행 중인 API 서버를 종료한 뒤 다시 시도합니다. 기존 `.venv`가 정상이라면 `python -m venv .venv`를 반복 실행하지 않아도 됩니다.

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

## 테스트 실행

Backend:

```bash
cd apps/api
ruff format --check .
ruff check .
pytest
```

Frontend:

```bash
cd apps/web
npm run lint
npm run type-check
npm run test
```

Docker Compose 설정 검증:

```bash
docker compose config
```

## 로컬 faster-whisper 사용 방법

정확도 우선 설정은 `large-v3` 모델을 `storage/models/whisper-large-v3`에 한 번 다운로드합니다. 모델 파일은 Git에 포함되지 않습니다.

```bash
cd apps/api
. .venv/Scripts/activate
python -m pip install -r requirements-local-ai.txt
python -c "from faster_whisper.utils import download_model; download_model('large-v3', output_dir='../../storage/models/whisper-large-v3')"
```

로컬 API를 실행할 때 다음 환경 변수를 지정합니다.

```bash
export STT_PROVIDER=faster-whisper
export WHISPER_MODEL_PATH=../../storage/models/whisper-large-v3
export WHISPER_DEVICE=cpu
export WHISPER_COMPUTE_TYPE=int8
export WHISPER_LANGUAGE=ko
export WHISPER_PREPROCESS_AUDIO=true
export WHISPER_CONDITION_ON_PREVIOUS_TEXT=false
export WHISPER_INITIAL_PROMPT=
export WHISPER_HOTWORDS=
export WHISPER_VAD_THRESHOLD=0.5
export ANALYSIS_PROVIDER=ollama
uvicorn app.main:app --reload
```

Docker Compose에서는 프로젝트 루트의 `.env`를 다음과 같이 설정한 뒤 실행합니다. 모델 디렉터리는 컨테이너의 `/models`에 읽기 전용으로 마운트됩니다.

```dotenv
STT_PROVIDER=faster-whisper
API_REQUIREMENTS_FILE=requirements-local-ai.txt
WHISPER_MODEL_PATH=/models/whisper-large-v3
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_LANGUAGE=ko
WHISPER_PREPROCESS_AUDIO=true
WHISPER_CONDITION_ON_PREVIOUS_TEXT=false
WHISPER_INITIAL_PROMPT=
WHISPER_HOTWORDS=
WHISPER_VAD_THRESHOLD=0.5
ANALYSIS_PROVIDER=ollama
```

```bash
docker compose up --build
```

Provider는 로컬 모델만 허용하므로 실행 중 모델을 자동으로 다운로드하거나 외부 STT API를 호출하지 않습니다. 전사 전에 임시 16kHz mono WAV를 만들고 고역·저역 필터, 노이즈 감소, 음량 정규화를 적용하며 전사가 끝나면 즉시 삭제합니다. 전처리가 실패하면 원본 오디오로 계속 전사합니다. 기본 prompt와 hotwords는 환각 방지를 위해 비워 두며, 명백한 자막·광고 안내 환각은 저장 전에 제외합니다.

## 로컬 화자분리 사용 방법

화자분리는 로컬 `pyannote/speaker-diarization-community-1` 모델을 사용합니다. 먼저 [모델 페이지](https://huggingface.co/pyannote/speaker-diarization-community-1)에서 사용 조건에 동의하고 read 권한 Hugging Face 토큰을 준비합니다. 아래 다운로드 단계에서만 토큰이 필요하며 API 실행 중에는 외부 서비스나 토큰을 사용하지 않습니다.

```bash
cd apps/api
. .venv/Scripts/activate
export HF_TOKEN=발급받은_토큰
python scripts/download_diarization_model.py
```

API 실행 전에 다음 설정을 추가합니다. 일반적인 상담 통화처럼 화자가 정확히 두 명이면 최소/최대 화자 수를 모두 `2`로 두는 것이 안정적입니다. 화자 수가 일정하지 않은 파일에는 두 값을 비우면 자동 추정합니다.

로컬 전체 구성을 한 번에 실행하려면 다음 명령을 사용합니다. 이 스크립트는 faster-whisper, pyannote 화자분리, Ollama 설정을 함께 적용하므로 mock Provider로 되돌아가는 실수를 방지합니다.

```bash
bash apps/api/run-local.sh
```

PowerShell에서는 다음 명령을 사용합니다.

```powershell
powershell -ExecutionPolicy Bypass -File apps/api/run-local.ps1
```

```bash
export DIARIZATION_PROVIDER=pyannote
export DIARIZATION_MODEL_PATH=../../storage/models/pyannote-speaker-diarization-community-1
export DIARIZATION_DEVICE=cpu
export DIARIZATION_MIN_SPEAKERS=2
export DIARIZATION_MAX_SPEAKERS=2
python -m uvicorn app.main:app --reload
```

Docker Compose에서는 `DIARIZATION_MODEL_PATH=/models/pyannote-speaker-diarization-community-1`을 사용합니다. 화자분리 결과는 Whisper 전사 구간과 시간상 가장 많이 겹치는 화자를 기준으로 `화자 1`, `화자 2`처럼 저장합니다. `community-1`의 exclusive diarization 결과가 있으면 이를 우선 사용합니다.

`ANALYSIS_PROVIDER=local`은 외부 LLM 없이 실제 전사문에서 대표 문장, 주요 키워드, 최대 3개의 구간별 요약을 추출합니다. 생성형 요약이 아닌 추출형 PoC이므로 결과 문장은 원문 전사 구간을 그대로 사용합니다.

## 로컬 Ollama 분석 사용 방법

Ollama를 설치한 뒤 로컬 분석 모델을 한 번 다운로드합니다.

```bash
ollama pull qwen3.5:4b
```

API를 실행할 때 Ollama 분석 Provider를 선택합니다.

```bash
export ANALYSIS_PROVIDER=ollama
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen3.5:4b
python -m uvicorn app.main:app --reload
```

Ollama Provider는 전사문을 로컬 Ollama API에만 전달하고 JSON Schema로 결과 형식을 검증합니다. 긴 전사문은 자동으로 나누어 분석하며, Ollama 연결이나 응답 검증이 실패하면 기존 `local` 추출형 분석으로 전환합니다. 전사 전문과 모델 응답은 로그에 남기지 않습니다.

## Gemini 분석 사용 방법

Gemini는 분석 Provider로만 사용하며 음성 전사는 기존 Mock 또는 faster-whisper Provider가 담당합니다. API 키는 FastAPI 서버 환경 변수에만 설정합니다.

PowerShell:

```powershell
$env:ANALYSIS_PROVIDER = "gemini"
$env:GEMINI_API_KEY = "발급받은_키"
$env:GEMINI_MODEL = "gemini-2.5-flash"
python -m uvicorn app.main:app --reload
```

Bash:

```bash
export ANALYSIS_PROVIDER=gemini
export GEMINI_API_KEY=발급받은_키
export GEMINI_MODEL=gemini-2.5-flash
python -m uvicorn app.main:app --reload
```

Gemini Provider는 전사문을 Gemini `generateContent` API에 전달하고 JSON Schema 응답을 Pydantic으로 다시 검증합니다. 긴 전사문은 나누어 분석하며, API 연결 또는 응답 검증에 실패하면 `local` 추출형 분석으로 전환합니다. API 키, 전사 전문, 모델 응답은 애플리케이션 로그에 남기지 않습니다.

## GitHub Actions와 Codespaces PoC

GitHub Actions는 웹서비스를 계속 실행하지 않고, push와 pull request마다 backend와 frontend의 formatting, lint, test, build를 자동 검증합니다. 결과는 GitHub 저장소의 `Actions` 탭에서 확인합니다.

임시 웹 데모는 GitHub Codespaces에서 실행합니다. 저장소의 `Settings > Secrets and variables > Codespaces`에서 `GEMINI_API_KEY` Secret을 만들고 이 저장소에 접근을 허용합니다. Secret이 없으면 Mock 분석으로 실행되므로 화면과 업로드 흐름은 그대로 확인할 수 있습니다.

1. GitHub 저장소의 `Code > Codespaces`에서 `Create codespace on main`을 선택합니다.
2. 최초 의존성 설치가 끝나면 API와 Web이 자동으로 시작됩니다.
3. 브라우저가 자동으로 열리지 않으면 Codespace의 `PORTS` 탭에서 `ACRC-Call-Log` 3000 포트를 엽니다.
4. 다른 사람에게 잠시 공유할 때만 3000 포트의 `Port Visibility`를 `Public` 또는 `Organization`으로 변경합니다.
5. 데모가 끝나면 Codespace를 중지하거나 삭제합니다.

프론트엔드는 같은 origin의 `/api` 경로를 통해 FastAPI를 호출하므로 8000 포트를 공개할 필요가 없습니다. Codespaces의 로컬 SQLite와 업로드 파일은 정식 운영 데이터로 간주하지 않으며, 공개 포트 데모에는 실제 민감 녹취 대신 테스트 파일만 사용합니다.

Codespace에 `GEMINI_API_KEY`가 있으면 기본 분석 Provider는 `gemini`, 없으면 `mock`입니다. 음성 전사는 Codespaces의 빠른 시작을 위해 항상 기본 `mock`으로 시작합니다. faster-whisper와 pyannote는 `requirements-local-ai.txt`를 별도로 설치해야 하며 일반 Codespace의 자원과 시작 시간에는 적합하지 않을 수 있습니다.

## Mock Provider 사용 방법

기본 설정인 `STT_PROVIDER=mock`, `ANALYSIS_PROVIDER=mock` 상태에서는 외부 API 키 없이 업로드부터 분석 완료까지 동작합니다. 업로드된 파일의 실제 음성 내용은 읽지 않고, 한국어 상담 통화 샘플 전사와 요약을 반환합니다. 파일명이 `fail`로 시작하면 PoC 테스트를 위해 실패 상태가 저장됩니다.

## 실제 STT Provider 추가 방법

1. `apps/api/app/providers/base.py`의 `SpeechToTextProvider`, `CallAnalysisProvider` 인터페이스를 따른 구현체를 추가합니다.
2. `apps/api/app/providers/__init__.py`에서 새 Provider 이름을 매핑합니다.
3. `.env`의 `STT_PROVIDER` 또는 `ANALYSIS_PROVIDER` 값을 새 이름으로 변경합니다.

서비스 계층과 프론트엔드는 Provider 인터페이스만 사용하므로 실제 SDK 연동 시 화면과 API 계약을 바꾸지 않아도 됩니다. API 키는 반드시 환경 변수나 승인된 비밀 관리 경로를 사용하고 소스 코드에 작성하지 않아야 합니다.

## 알려진 PoC 한계

- 사용자 인증과 권한 관리가 없습니다.
- Mock Provider는 실제 음성 내용을 전사하지 않습니다. faster-whisper Provider를 선택하면 로컬 모델로 전사할 수 있습니다.
- Codespaces 데모 URL과 프로세스는 Codespace가 중지되면 사용할 수 없습니다.
- Codespaces의 SQLite와 업로드 파일은 영구 운영 저장소가 아닙니다.
- 고급 화자 분리, 전사문 편집, 전체 텍스트 검색, 통계 대시보드는 없습니다.
- 장기 보관 정책, 감사 로그, 자동 개인정보 마스킹은 구현하지 않았습니다.

## 실제 인트라넷 탑재 전 필요한 보안 작업

- 사내 SSO 또는 LDAP 기반 인증과 접근 통제
- 업로드 파일과 전사문에 대한 보관 기간, 삭제 정책, 접근 로그
- 개인정보 및 민감정보 마스킹 정책
- API 키와 인증정보의 비밀 관리 체계
- 네트워크 접근 제한과 TLS 종료 구성
- 운영 장애 대응을 위한 모니터링과 감사 로그

