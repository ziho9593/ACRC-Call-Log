from __future__ import annotations

from urllib.parse import quote

import httpx

from .base import CallAnalysisProvider
from .ollama_analysis import ResponseModel, StructuredCallAnalysisProvider


def _gemini_json_schema(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _gemini_json_schema(item)
            for key, item in value.items()
            if key not in {"minLength", "maxLength"}
        }
    if isinstance(value, list):
        return [_gemini_json_schema(item) for item in value]
    return value


class GeminiCallAnalysisProvider(StructuredCallAnalysisProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        base_url: str = "https://generativelanguage.googleapis.com",
        timeout_seconds: float = 180,
        max_input_chars: int = 40000,
        client: httpx.Client | None = None,
        fallback: CallAnalysisProvider | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Gemini Provider에는 GEMINI_API_KEY가 필요합니다.")
        super().__init__(max_input_chars=max_input_chars, fallback=fallback)
        self._api_key = api_key
        self._model = model
        self._client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout_seconds,
        )

    def _chat(
        self,
        response_model: type[ResponseModel],
        system_prompt: str,
        user_prompt: str,
    ) -> ResponseModel:
        model_name = quote(self._model, safe="")
        response = self._client.post(
            f"/v1beta/models/{model_name}:generateContent",
            headers={"x-goog-api-key": self._api_key},
            json={
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": user_prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0,
                    "responseMimeType": "application/json",
                    "responseJsonSchema": _gemini_json_schema(response_model.model_json_schema()),
                },
            },
        )
        response.raise_for_status()
        parts = response.json()["candidates"][0]["content"]["parts"]
        content = "".join(part.get("text", "") for part in parts)
        return response_model.model_validate_json(content)
