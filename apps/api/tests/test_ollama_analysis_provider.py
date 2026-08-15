from __future__ import annotations

import json

import httpx

from app.providers.base import TranscriptResult, TranscriptUtterance
from app.providers.ollama_analysis import OllamaCallAnalysisProvider


def transcript_with(*texts: str) -> TranscriptResult:
    utterances = [
        TranscriptUtterance(
            sequence=index,
            speaker="화자",
            start_ms=(index - 1) * 5000,
            end_ms=index * 5000,
            text=text,
        )
        for index, text in enumerate(texts, start=1)
    ]
    return TranscriptResult(duration_ms=len(utterances) * 5000, utterances=utterances)


def ollama_response(content: dict[str, object]) -> httpx.Response:
    return httpx.Response(
        200,
        json={"message": {"role": "assistant", "content": json.dumps(content)}},
    )


def test_ollama_analysis_maps_structured_response() -> None:
    request_bodies: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        request_bodies.append(json.loads(request.content))
        return ollama_response(
            {
                "one_line_summary": "고객이 민원 처리 상태를 문의했습니다.",
                "detailed_summary": "담당 부서 검토가 지연되어 진행 상태를 안내했습니다.",
                "keywords": ["민원", "처리 상태", "검토 지연"],
                "sections": [
                    {
                        "start_sequence": 1,
                        "end_sequence": 2,
                        "title": "처리 상태 문의",
                        "summary": "고객이 처리 상태를 확인했습니다.",
                        "keywords": ["처리 상태"],
                    }
                ],
            }
        )

    client = httpx.Client(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(handler),
    )
    provider = OllamaCallAnalysisProvider(
        base_url="http://ollama.test",
        model="qwen3.5:4b",
        client=client,
    )

    result = provider.analyze(
        transcript_with(
            "민원 처리 상태를 확인하고 싶습니다.",
            "담당 부서에서 검토하고 있습니다.",
        )
    )

    assert result.one_line_summary == "고객이 민원 처리 상태를 문의했습니다."
    assert result.keywords == ["민원", "처리 상태", "검토 지연"]
    assert result.sections[0].start_ms == 0
    assert result.sections[0].end_ms == 10000
    assert request_bodies[0]["model"] == "qwen3.5:4b"
    assert request_bodies[0]["stream"] is False
    assert request_bodies[0]["think"] is False
    assert isinstance(request_bodies[0]["format"], dict)


def test_ollama_failure_uses_local_fallback() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Ollama is offline", request=request)

    client = httpx.Client(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(handler),
    )
    provider = OllamaCallAnalysisProvider(
        base_url="http://ollama.test",
        model="qwen3.5:4b",
        client=client,
    )

    result = provider.analyze(transcript_with("민원 처리 상태를 확인하고 싶습니다."))

    assert result.one_line_summary == "민원 처리 상태를 확인하고 싶습니다."
    assert "민원" in result.keywords


def test_long_transcript_is_analyzed_in_chunks() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        body = json.loads(request.content)
        schema = body["format"]
        if "sections" not in schema["properties"]:
            return ollama_response(
                {
                    "one_line_summary": "전체 통화 요약",
                    "detailed_summary": "두 구간의 내용을 종합했습니다.",
                    "keywords": ["전체", "통화", "종합"],
                }
            )

        sequence = 1 if "[1]" in body["messages"][1]["content"] else 2
        return ollama_response(
            {
                "one_line_summary": f"구간 {sequence} 요약",
                "detailed_summary": f"구간 {sequence} 상세 요약",
                "keywords": [f"구간{sequence}", "통화", "분석"],
                "sections": [
                    {
                        "start_sequence": sequence,
                        "end_sequence": sequence,
                        "title": f"구간 {sequence}",
                        "summary": f"구간 {sequence} 요약",
                        "keywords": [f"구간{sequence}"],
                    }
                ],
            }
        )

    client = httpx.Client(
        base_url="http://ollama.test",
        transport=httpx.MockTransport(handler),
    )
    provider = OllamaCallAnalysisProvider(
        base_url="http://ollama.test",
        model="qwen3.5:4b",
        max_input_chars=1000,
        client=client,
    )

    result = provider.analyze(transcript_with("가" * 700, "나" * 700))

    assert request_count == 3
    assert result.one_line_summary == "전체 통화 요약"
    assert len(result.sections) == 2
    assert result.sections[1].start_ms == 5000
