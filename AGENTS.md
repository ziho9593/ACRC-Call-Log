# ACRC-Call-Log 작업 메모

- PoC 범위에서는 인증, 권한, Redis/Celery, 외부 STT/LLM 연동을 구현하지 않는다.
- 녹취 파일과 전체 전사문은 로그에 남기지 않는다.
- 업로드 파일은 `storage/uploads`에 UUID 기반 파일명으로 저장하고 API를 통해서만 제공한다.
- 기본 Provider는 `mock`이며, 실제 STT/분석 Provider는 `apps/api/app/providers` 아래에 구현체를 추가한다.

