# ACRC-Call-Log PoC Architecture

## 처리 흐름

1. 사용자가 Web 화면에서 `.mp3`, `.wav`, `.m4a`, `.mp4` 파일을 선택하고 업로드한다.
2. Web은 `POST /api/v1/calls`로 multipart/form-data 요청을 보낸다.
3. API는 파일명, 확장자, MIME 타입, 크기를 검증한다.
4. API는 UUID 기반 내부 파일명을 생성해 `UPLOAD_DIR`에 저장하고 `call_records`에 `UPLOADED` 상태를 기록한다.
5. 응답은 즉시 반환되고, FastAPI background task가 분석을 시작한다.
6. background task는 상태를 `PROCESSING`으로 바꾸고 `SpeechToTextProvider`를 호출한다.
7. 선택한 STT Provider가 전사 결과를 반환한다. Mock은 한국어 샘플을, faster-whisper는 로컬 모델의 타임스탬프 전사를 반환한다.
8. `CallAnalysisProvider`는 전체 요약, 키워드, 구간별 요약을 생성한다. `local` Provider는 외부 LLM 없이 실제 전사문에서 결과를 추출하고, `ollama`와 `gemini` Provider는 각 API의 구조화 결과를 검증해 반환한다. 원격 분석 실패 시 전사문 기반 `local` 분석으로 전환한다.
9. API는 `utterances`, `call_sections`, `call_records` 분석 결과를 SQLite에 저장하고 상태를 `COMPLETED`로 변경한다.
10. 오류가 발생하면 전사문이나 녹취 내용을 로그에 남기지 않고 `FAILED` 상태와 사용자용 오류 메시지만 저장한다.
11. Web은 상세 화면에서 `GET /api/v1/calls/{call_id}/status`를 polling하고 완료 시 상세 데이터를 다시 조회한다.
12. 오디오는 공개 정적 경로가 아니라 `GET /api/v1/calls/{call_id}/audio` API를 통해서만 제공된다.

## 주요 경계

- API 라우터와 서비스 계층은 특정 AI SDK에 직접 의존하지 않는다.
- Provider 교체는 `apps/api/app/providers`의 구현체와 환경 변수 변경으로 처리한다.
- SQLite에는 키워드를 JSON 문자열로 저장한다.
- 업로드 파일명은 저장 경로에 직접 사용하지 않는다.

## GitHub PoC 경계

- GitHub Actions는 backend와 frontend의 정적 검증, 테스트, production build만 수행한다.
- Codespaces는 API와 Web을 실행하고 3000 포트를 임시 데모 URL로 전달한다.
- Web은 같은 origin의 `/api` 프록시를 사용하므로 FastAPI의 8000 포트를 공개할 필요가 없다.
- Gemini API 키는 Codespaces Secret으로 주입하며 저장소에 기록하지 않는다.
- Codespaces의 SQLite와 업로드 파일은 임시 PoC 데이터이며 영구 운영 저장소가 아니다.

