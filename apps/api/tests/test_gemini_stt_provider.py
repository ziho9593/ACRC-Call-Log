from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from app.providers.gemini_stt import GeminiSpeechToTextProvider


def test_gemini_stt_uploads_audio_and_maps_transcript(tmp_path: Path) -> None:
    audio_path = tmp_path / "call.mp3"
    audio_path.write_bytes(b"real audio bytes")
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/upload/v1beta/files":
            return httpx.Response(
                200,
                headers={"x-goog-upload-url": "https://gemini.test/upload-session"},
            )
        if request.url.path == "/upload-session":
            assert request.read() == b"real audio bytes"
            return httpx.Response(
                200,
                json={
                    "file": {
                        "name": "files/test-audio",
                        "uri": "https://files.test/test-audio",
                        "state": "ACTIVE",
                    }
                },
            )
        if request.url.path == "/v1beta/models/gemini-test:generateContent":
            content = {
                "duration_ms": 5200,
                "utterances": [
                    {
                        "speaker": "화자 1",
                        "start_ms": 0,
                        "end_ms": 2200,
                        "text": "민원 접수 상태를 확인해주세요.",
                    },
                    {
                        "speaker": "화자 2",
                        "start_ms": 2300,
                        "end_ms": 5200,
                        "text": "담당 부서에서 확인 중입니다.",
                    },
                ],
            }
            return httpx.Response(
                200,
                json={
                    "candidates": [
                        {"content": {"parts": [{"text": json.dumps(content)}]}}
                    ]
                },
            )
        if request.method == "DELETE" and request.url.path == "/v1beta/files/test-audio":
            return httpx.Response(204)
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = httpx.Client(
        base_url="https://gemini.test",
        transport=httpx.MockTransport(handler),
    )
    provider = GeminiSpeechToTextProvider(
        api_key="test-api-key",
        model="gemini-test",
        base_url="https://gemini.test",
        client=client,
    )

    result = provider.transcribe(str(audio_path))

    assert result.duration_ms == 5200
    assert [item.speaker for item in result.utterances] == ["화자 1", "화자 2"]
    assert result.utterances[0].text == "민원 접수 상태를 확인해주세요."
    generate_request = next(
        request for request in requests if request.url.path.endswith(":generateContent")
    )
    body = json.loads(generate_request.content)
    assert body["contents"][0]["parts"][1]["fileData"] == {
        "mimeType": "audio/mpeg",
        "fileUri": "https://files.test/test-audio",
    }
    assert requests[-1].method == "DELETE"
    assert all(b"test-api-key" not in request.content for request in requests)


def test_gemini_stt_requires_api_key() -> None:
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiSpeechToTextProvider(api_key="")
