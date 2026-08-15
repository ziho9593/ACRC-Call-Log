# ACRC-Call-Log

사내 통화 녹취 분석 서비스의 PoC입니다. 사용자가 녹취 파일을 업로드하면 백엔드 background task가 Mock 전사와 분석을 수행하고, 프론트엔드에서 타임스탬프 전사문, 전체 요약, 주요 키워드, 구간별 요약, 오디오 재생을 확인할 수 있습니다.

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
- `ANALYSIS_PROVIDER`: 기본값 `mock`
- `DATABASE_PATH`: SQLite 파일 경로
- `UPLOAD_DIR`: 업로드 파일 저장 경로
- `PROCESSED_DIR`: 처리 산출물 저장 경로
- `MAX_UPLOAD_BYTES`: 기본 100MB
- `API_CORS_ORIGINS`: 허용할 프론트엔드 Origin
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
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

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

`small` 모델을 `storage/models/whisper-small`에 한 번 다운로드합니다. 모델 파일은 Git에 포함되지 않습니다.

```bash
cd apps/api
. .venv/Scripts/activate
python -c "from faster_whisper.utils import download_model; download_model('small', output_dir='../../storage/models/whisper-small')"
```

로컬 API를 실행할 때 다음 환경 변수를 지정합니다.

```bash
export STT_PROVIDER=faster-whisper
export WHISPER_MODEL_PATH=../../storage/models/whisper-small
export WHISPER_DEVICE=cpu
export WHISPER_COMPUTE_TYPE=int8
export WHISPER_LANGUAGE=ko
uvicorn app.main:app --reload
```

Docker Compose에서는 프로젝트 루트의 `.env`를 다음과 같이 설정한 뒤 실행합니다. 모델 디렉터리는 컨테이너의 `/models`에 읽기 전용으로 마운트됩니다.

```dotenv
STT_PROVIDER=faster-whisper
WHISPER_MODEL_PATH=/models/whisper-small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_LANGUAGE=ko
ANALYSIS_PROVIDER=mock
```

```bash
docker compose up --build
```

Provider는 로컬 모델만 허용하므로 실행 중 모델을 자동으로 다운로드하거나 외부 STT API를 호출하지 않습니다. Whisper 자체에는 화자 분리 기능이 없어서 실제 전사 구간의 화자는 모두 `화자`로 저장됩니다.

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
- 고급 화자 분리, 전사문 편집, 전체 텍스트 검색, 통계 대시보드는 없습니다.
- 장기 보관 정책, 감사 로그, 자동 개인정보 마스킹은 구현하지 않았습니다.

## 실제 인트라넷 탑재 전 필요한 보안 작업

- 사내 SSO 또는 LDAP 기반 인증과 접근 통제
- 업로드 파일과 전사문에 대한 보관 기간, 삭제 정책, 접근 로그
- 개인정보 및 민감정보 마스킹 정책
- API 키와 인증정보의 비밀 관리 체계
- 네트워크 접근 제한과 TLS 종료 구성
- 운영 장애 대응을 위한 모니터링과 감사 로그

