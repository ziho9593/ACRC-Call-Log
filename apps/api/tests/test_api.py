from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    runtime_dir = Path("test-runtime") / str(uuid.uuid4())
    runtime_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DATABASE_PATH", str(runtime_dir / "test.db"))
    monkeypatch.setenv("UPLOAD_DIR", str(runtime_dir / "uploads"))
    monkeypatch.setenv("PROCESSED_DIR", str(runtime_dir / "processed"))
    monkeypatch.setenv("MAX_UPLOAD_BYTES", str(1024 * 1024))
    monkeypatch.setenv("STT_PROVIDER", "mock")
    monkeypatch.setenv("ANALYSIS_PROVIDER", "mock")
    db.init_db()
    try:
        yield TestClient(app)
    finally:
        shutil.rmtree(runtime_dir, ignore_errors=True)


def upload_sample(client: TestClient, filename: str = "sample-call.mp3") -> dict[str, object]:
    response = client.post(
        "/api/v1/calls",
        files={"file": (filename, b"fake audio bytes", "audio/mpeg")},
    )
    assert response.status_code == 201
    return response.json()


def test_health_api(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_audio_file(client: TestClient) -> None:
    body = upload_sample(client)
    assert body["originalFilename"] == "sample-call.mp3"
    assert body["status"] == "UPLOADED"


def test_reject_unsupported_extension(client: TestClient) -> None:
    response = client.post(
        "/api/v1/calls",
        files={"file": ("sample.txt", b"text", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "지원하지 않는 파일 형식입니다."


def test_reject_file_over_max_size(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "4")
    response = client.post(
        "/api/v1/calls",
        files={"file": ("sample.mp3", b"12345", "audio/mpeg")},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "파일 크기가 최대 허용 용량을 초과했습니다."


def test_list_calls(client: TestClient) -> None:
    upload_sample(client)
    response = client.get("/api/v1/calls")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_get_call_detail(client: TestClient) -> None:
    created = upload_sample(client)
    response = client.get(f"/api/v1/calls/{created['id']}")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "COMPLETED"
    assert len(body["utterances"]) >= 4
    assert len(body["sections"]) >= 3
    assert "민원" in body["oneLineSummary"]


def test_get_missing_call(client: TestClient) -> None:
    response = client.get("/api/v1/calls/missing-id")
    assert response.status_code == 404


def test_mock_analysis_completed(client: TestClient) -> None:
    created = upload_sample(client)
    response = client.get(f"/api/v1/calls/{created['id']}/status")
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"


def test_processing_failure_saved(client: TestClient) -> None:
    created = upload_sample(client, "fail-call.mp3")
    response = client.get(f"/api/v1/calls/{created['id']}/status")
    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"
    assert response.json()["errorMessage"] == "분석 처리 중 오류가 발생했습니다."


def test_delete_call_record(client: TestClient) -> None:
    created = upload_sample(client)
    assert client.get(f"/api/v1/calls/{created['id']}/audio").status_code == 200
    response = client.delete(f"/api/v1/calls/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/v1/calls/{created['id']}").status_code == 404
