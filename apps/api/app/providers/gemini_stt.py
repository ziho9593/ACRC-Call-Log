from __future__ import annotations

import mimetypes
import time
from pathlib import Path
from urllib.parse import quote

import httpx
from pydantic import BaseModel, Field

from .base import SpeechToTextProvider, TranscriptResult, TranscriptUtterance
from .gemini_analysis import _gemini_json_schema


class GeminiTranscriptUtterance(BaseModel):
    speaker: str
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    text: str


class GeminiTranscriptResponse(BaseModel):
    duration_ms: int = Field(ge=0)
    utterances: list[GeminiTranscriptUtterance]


class GeminiSpeechToTextProvider(SpeechToTextProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        base_url: str = "https://generativelanguage.googleapis.com",
        timeout_seconds: float = 180,
        language: str = "ko",
        client: httpx.Client | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Gemini STT Provider requires GEMINI_API_KEY.")
        self._api_key = api_key
        self._model = model
        self._language = language
        self._timeout_seconds = timeout_seconds
        self._client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout_seconds,
        )

    def transcribe(self, audio_path: str) -> TranscriptResult:
        path = Path(audio_path)
        if not path.is_file():
            raise FileNotFoundError(path)

        mime_type = mimetypes.guess_type(path.name)[0] or "audio/mpeg"
        uploaded = self._upload(path, mime_type)
        file_name = str(uploaded["name"])
        try:
            uploaded = self._wait_until_active(uploaded)
            response = self._generate(str(uploaded["uri"]), mime_type)
            return self._to_transcript(response)
        finally:
            self._delete(file_name)

    def _upload(self, path: Path, mime_type: str) -> dict[str, object]:
        size = path.stat().st_size
        start_response = self._client.post(
            "/upload/v1beta/files",
            headers={
                "x-goog-api-key": self._api_key,
                "X-Goog-Upload-Protocol": "resumable",
                "X-Goog-Upload-Command": "start",
                "X-Goog-Upload-Header-Content-Length": str(size),
                "X-Goog-Upload-Header-Content-Type": mime_type,
            },
            json={"file": {"displayName": path.name}},
        )
        start_response.raise_for_status()
        upload_url = start_response.headers.get("x-goog-upload-url")
        if not upload_url:
            raise ValueError("Gemini Files API did not return an upload URL.")

        with path.open("rb") as audio_file:
            upload_response = self._client.post(
                upload_url,
                headers={
                    "Content-Length": str(size),
                    "X-Goog-Upload-Offset": "0",
                    "X-Goog-Upload-Command": "upload, finalize",
                },
                content=audio_file,
            )
        upload_response.raise_for_status()
        uploaded = upload_response.json().get("file")
        if not isinstance(uploaded, dict) or not uploaded.get("name") or not uploaded.get("uri"):
            raise ValueError("Gemini Files API returned invalid file metadata.")
        return uploaded

    def _wait_until_active(self, uploaded: dict[str, object]) -> dict[str, object]:
        state = str(uploaded.get("state", "ACTIVE"))
        deadline = time.monotonic() + self._timeout_seconds
        while state == "PROCESSING" and time.monotonic() < deadline:
            time.sleep(1)
            response = self._client.get(
                f"/v1beta/{uploaded['name']}",
                headers={"x-goog-api-key": self._api_key},
            )
            response.raise_for_status()
            uploaded = response.json()
            state = str(uploaded.get("state", ""))
        if state != "ACTIVE":
            raise ValueError(f"Gemini audio file is not ready: {state or 'UNKNOWN'}")
        return uploaded

    def _generate(self, file_uri: str, mime_type: str) -> GeminiTranscriptResponse:
        model_name = quote(self._model, safe="")
        response = self._client.post(
            f"/v1beta/models/{model_name}:generateContent",
            headers={"x-goog-api-key": self._api_key},
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": (
                                    f"Transcribe the entire audio verbatim in {self._language}. "
                                    "Do not summarize, invent, or omit speech. "
                                    "Split the transcript when the speaker changes and return "
                                    "millisecond timestamps. Use stable labels such as 화자 1 "
                                    "and 화자 2 when names are unknown."
                                )
                            },
                            {"fileData": {"mimeType": mime_type, "fileUri": file_uri}},
                        ],
                    }
                ],
                "generationConfig": {
                    "temperature": 0,
                    "responseMimeType": "application/json",
                    "responseJsonSchema": _gemini_json_schema(
                        GeminiTranscriptResponse.model_json_schema()
                    ),
                },
            },
        )
        response.raise_for_status()
        parts = response.json()["candidates"][0]["content"]["parts"]
        content = "".join(part.get("text", "") for part in parts)
        return GeminiTranscriptResponse.model_validate_json(content)

    def _delete(self, file_name: str) -> None:
        try:
            self._client.delete(
                f"/v1beta/{file_name}",
                headers={"x-goog-api-key": self._api_key},
            )
        except httpx.HTTPError:
            pass

    @staticmethod
    def _to_transcript(response: GeminiTranscriptResponse) -> TranscriptResult:
        utterances: list[TranscriptUtterance] = []
        for item in response.utterances:
            text = item.text.strip()
            if not text:
                continue
            start_ms = max(0, item.start_ms)
            end_ms = max(start_ms + 1, item.end_ms)
            utterances.append(
                TranscriptUtterance(
                    sequence=len(utterances) + 1,
                    speaker=item.speaker.strip() or "화자",
                    start_ms=start_ms,
                    end_ms=end_ms,
                    text=text,
                )
            )
        if not utterances:
            raise ValueError("Gemini returned an empty transcript.")
        duration_ms = max(response.duration_ms, max(item.end_ms for item in utterances))
        return TranscriptResult(duration_ms=duration_ms, utterances=utterances)
