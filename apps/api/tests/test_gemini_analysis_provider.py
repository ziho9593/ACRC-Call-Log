from __future__ import annotations

import json

import httpx
import pytest

from app.providers.base import TranscriptResult, TranscriptUtterance
from app.providers.gemini_analysis import GeminiCallAnalysisProvider


def transcript() -> TranscriptResult:
    return TranscriptResult(
        duration_ms=10000,
        utterances=[
            TranscriptUtterance(
                sequence=1,
                speaker="고객",
                start_ms=0,
                end_ms=5000,
                text="민원 처리 상태를 확인하고 싶습니다.",
            ),
            TranscriptUtterance(
                sequence=2,
                speaker="상담원",
                start_ms=5000,
                end_ms=10000,
                text="담당 부서에서 검토하고 있습니다.",
            ),
        ],
    )


def gemini_response(content: dict[str, object]) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "candidates": [
                {
                    "content": {
                        "role": "model",
                        "parts": [{"text": json.dumps(content)}],
                    }
                }
            ]
        },
    )


def test_gemini_analysis_maps_structured_response() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return gemini_response(
            {
                "one_line_summary": "고객이 민원 처리 상태를 문의했습니다.",
                "detailed_summary": "담당 부서 검토가 진행 중이라고 안내했습니다.",
                "keywords": ["민원", "처리 상태", "담당 부서"],
                "sections": [
                    {
                        "start_sequence": 1,
                        "end_sequence": 2,
                        "title": "처리 상태 문의",
                        "summary": "민원 처리 상태를 확인하고 진행 상황을 안내했습니다.",
                        "keywords": ["처리 상태"],
                    }
                ],
            }
        )

    client = httpx.Client(
        base_url="https://gemini.test",
        transport=httpx.MockTransport(handler),
    )
    provider = GeminiCallAnalysisProvider(
        api_key="test-api-key",
        base_url="https://gemini.test",
        model="gemini-test-model",
        client=client,
    )

    result = provider.analyze(transcript())

    assert result.one_line_summary == "고객이 민원 처리 상태를 문의했습니다."
    assert result.sections[0].start_ms == 0
    assert result.sections[0].end_ms == 10000
    assert captured_request is not None
    assert captured_request.url.path == "/v1beta/models/gemini-test-model:generateContent"
    assert captured_request.headers["x-goog-api-key"] == "test-api-key"
    body = json.loads(captured_request.content)
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert isinstance(body["generationConfig"]["responseJsonSchema"], dict)
    assert "minLength" not in json.dumps(body["generationConfig"]["responseJsonSchema"])
    assert b"test-api-key" not in captured_request.content
    assert "민원 처리 상태" in body["contents"][0]["parts"][0]["text"]


def test_gemini_failure_uses_local_fallback() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Gemini is unavailable", request=request)

    client = httpx.Client(
        base_url="https://gemini.test",
        transport=httpx.MockTransport(handler),
    )
    provider = GeminiCallAnalysisProvider(
        api_key="test-api-key",
        base_url="https://gemini.test",
        client=client,
    )

    result = provider.analyze(transcript())

    assert result.one_line_summary == "민원 처리 상태를 확인하고 싶습니다."
    assert "민원" in result.keywords


def test_gemini_requires_api_key() -> None:
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiCallAnalysisProvider(api_key="")
