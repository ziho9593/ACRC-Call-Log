from __future__ import annotations

from app.providers.base import TranscriptResult, TranscriptUtterance
from app.providers.local_analysis import LocalExtractiveCallAnalysisProvider


def sample_transcript() -> TranscriptResult:
    return TranscriptResult(
        duration_ms=40000,
        utterances=[
            TranscriptUtterance(1, "화자", 0, 5000, "안녕하세요 상담센터입니다."),
            TranscriptUtterance(2, "화자", 5000, 14000, "민원 처리 상태를 확인하고 싶습니다."),
            TranscriptUtterance(
                3,
                "화자",
                14000,
                28000,
                "담당 부서 배정은 완료되었지만 검토가 지연되고 있습니다.",
            ),
            TranscriptUtterance(
                4,
                "화자",
                28000,
                40000,
                "이번 주 안에 처리 결과를 문자로 안내드리겠습니다.",
            ),
        ],
    )


def test_analysis_is_derived_from_transcript() -> None:
    result = LocalExtractiveCallAnalysisProvider().analyze(sample_transcript())

    assert result.one_line_summary in {
        utterance.text for utterance in sample_transcript().utterances
    }
    assert "처리" in result.one_line_summary
    assert "처리" in result.keywords
    assert "민원 처리 상태" in result.detailed_summary
    assert len(result.keywords) <= 5
    assert len(result.sections) == 3
    assert result.sections[0].start_ms == 0
    assert result.sections[-1].end_ms == 40000
    assert all(section.summary for section in result.sections)
    assert all(section.keywords for section in result.sections)


def test_empty_transcript_returns_safe_result() -> None:
    result = LocalExtractiveCallAnalysisProvider().analyze(TranscriptResult(0, []))

    assert result.one_line_summary == "전사된 내용이 없습니다."
    assert result.detailed_summary == "전사된 내용이 없습니다."
    assert result.keywords == []
    assert result.sections == []


def test_blank_utterances_are_ignored() -> None:
    transcript = TranscriptResult(
        duration_ms=1000,
        utterances=[TranscriptUtterance(1, "화자", 0, 1000, "   ")],
    )

    result = LocalExtractiveCallAnalysisProvider().analyze(transcript)

    assert result.one_line_summary == "전사된 내용이 없습니다."
