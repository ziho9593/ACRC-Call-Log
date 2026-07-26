from __future__ import annotations

from .base import (
    AnalysisResult,
    AnalysisSection,
    CallAnalysisProvider,
    SpeechToTextProvider,
    TranscriptResult,
    TranscriptUtterance,
)


class MockSpeechToTextProvider(SpeechToTextProvider):
    def transcribe(self, audio_path: str) -> TranscriptResult:
        if "force-fail" in audio_path:
            raise RuntimeError("Mock STT 처리 실패")

        utterances = [
            TranscriptUtterance(
                1,
                "상담원",
                0,
                8500,
                "안녕하세요, 국민권익위원회 상담센터입니다. 어떤 내용으로 문의 주셨을까요?",
            ),
            TranscriptUtterance(
                2,
                "고객",
                8500,
                22100,
                "지난주에 온라인으로 민원을 접수했는데 처리 상태가 계속 접수로만 보여서 "
                "확인하고 싶습니다.",
            ),
            TranscriptUtterance(
                3,
                "상담원",
                22100,
                36500,
                "접수번호를 확인해 보겠습니다. 담당 부서 배정은 완료되었고 검토 의견 등록이 "
                "지연된 상태입니다.",
            ),
            TranscriptUtterance(
                4,
                "고객",
                36500,
                49300,
                "이번 주 안에는 답변을 받을 수 있을까요? 추가 자료가 필요하면 문자로 알려주세요.",
            ),
            TranscriptUtterance(
                5,
                "상담원",
                49300,
                64000,
                "담당자에게 진행 상황 확인 요청을 남기고, 추가 자료가 필요하면 오늘 중 "
                "안내드리겠습니다.",
            ),
        ]
        return TranscriptResult(duration_ms=64000, utterances=utterances)


class MockCallAnalysisProvider(CallAnalysisProvider):
    def analyze(self, transcript: TranscriptResult) -> AnalysisResult:
        return AnalysisResult(
            one_line_summary=(
                "민원 처리 상태 지연에 대한 확인 요청과 담당자 후속 안내가 이루어졌습니다."
            ),
            detailed_summary=(
                "고객은 온라인으로 접수한 민원의 상태가 장기간 '접수'로 표시되는 점을 "
                "문의했습니다. "
                "상담원은 접수번호 기준으로 담당 부서 배정은 완료되었으나 검토 의견 등록이 지연된 "
                "상태라고 설명했습니다. 고객은 이번 주 내 답변 가능성과 추가 자료 요청 방식에 대해 "
                "확인했고, 상담원은 담당자에게 진행 상황 확인 요청을 남긴 뒤 필요 시 "
                "문자로 안내하겠다고 답변했습니다."
            ),
            keywords=["민원 접수", "처리 상태", "담당 부서", "검토 지연", "추가 자료"],
            sections=[
                AnalysisSection(
                    1,
                    "문의 접수",
                    0,
                    22100,
                    "고객이 온라인 민원 접수 후 상태가 변경되지 않는 문제를 문의했습니다.",
                    ["민원 접수", "상태 확인"],
                ),
                AnalysisSection(
                    2,
                    "처리 현황 안내",
                    22100,
                    36500,
                    "상담원이 담당 부서 배정 완료와 검토 의견 등록 지연 사실을 설명했습니다.",
                    ["담당 부서", "검토 지연"],
                ),
                AnalysisSection(
                    3,
                    "후속 조치 약속",
                    36500,
                    transcript.duration_ms,
                    "상담원이 진행 상황 확인 요청과 추가 자료 필요 시 문자 안내를 약속했습니다.",
                    ["답변 일정", "문자 안내"],
                ),
            ],
        )
