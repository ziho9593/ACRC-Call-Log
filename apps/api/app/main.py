from __future__ import annotations

import shutil
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from . import db
from .config import get_settings
from .services import process_call

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4"}
ALLOWED_MIME_TYPES_BY_EXTENSION = {
    ".mp3": {"audio/mpeg", "audio/mp3"},
    ".wav": {"audio/wav", "audio/x-wav"},
    ".m4a": {"audio/mp4", "audio/m4a"},
    ".mp4": {"audio/mp4", "video/mp4"},
}


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    db.init_db()
    yield


app = FastAPI(title="ACRC-Call-Log API", lifespan=lifespan)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    active_settings = get_settings()
    return {
        "status": "ok",
        "sttProvider": active_settings.stt_provider,
        "diarizationProvider": active_settings.diarization_provider,
        "analysisProvider": active_settings.analysis_provider,
    }


@app.post("/api/v1/calls", status_code=201)
def upload_call(file: UploadFile, background_tasks: BackgroundTasks) -> dict[str, object]:
    db.init_db()
    if not file.filename or not file.filename.strip():
        raise HTTPException(status_code=400, detail="파일명이 비어 있습니다.")

    original_filename = Path(file.filename).name
    extension = Path(original_filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")

    mime_type = file.content_type or "application/octet-stream"
    if mime_type not in ALLOWED_MIME_TYPES_BY_EXTENSION[extension]:
        raise HTTPException(status_code=400, detail="지원하지 않는 MIME 타입입니다.")

    settings = get_settings()
    call_id = str(uuid.uuid4())
    storage_path = settings.upload_dir / f"{call_id}{extension}"
    total_size = 0

    try:
        with storage_path.open("wb") as output:
            while chunk := file.file.read(1024 * 1024):
                total_size += len(chunk)
                if total_size > settings.max_upload_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail="파일 크기가 최대 허용 용량을 초과했습니다.",
                    )
                output.write(chunk)
        if total_size == 0:
            raise HTTPException(status_code=400, detail="빈 파일은 업로드할 수 없습니다.")
    except HTTPException:
        storage_path.unlink(missing_ok=True)
        raise
    finally:
        file.file.close()

    record = db.create_call_record(
        call_id=call_id,
        original_filename=original_filename,
        storage_path=storage_path,
        mime_type=mime_type,
        file_size_bytes=total_size,
    )
    background_tasks.add_task(process_call, call_id)
    return db.row_to_call_summary(record)


@app.get("/api/v1/calls")
def list_calls() -> dict[str, list[dict[str, object]]]:
    db.init_db()
    return {"items": [db.row_to_call_summary(row) for row in db.list_call_records()]}


@app.get("/api/v1/calls/{call_id}")
def get_call(call_id: str) -> dict[str, object]:
    row = db.get_call_record(call_id)
    if row is None:
        raise HTTPException(status_code=404, detail="통화 기록을 찾을 수 없습니다.")
    return db.row_to_call_detail(row)


@app.get("/api/v1/calls/{call_id}/status")
def get_call_status(call_id: str) -> dict[str, object]:
    row = db.get_call_record(call_id)
    if row is None:
        raise HTTPException(status_code=404, detail="통화 기록을 찾을 수 없습니다.")
    return {
        "id": row["id"],
        "status": row["status"],
        "errorMessage": row["error_message"],
        "updatedAt": row["updated_at"],
    }


@app.get("/api/v1/calls/{call_id}/audio")
def get_call_audio(call_id: str) -> FileResponse:
    row = db.get_call_record(call_id)
    if row is None:
        raise HTTPException(status_code=404, detail="통화 기록을 찾을 수 없습니다.")
    storage_path = Path(row["storage_path"])
    if not storage_path.exists():
        raise HTTPException(status_code=404, detail="오디오 파일을 찾을 수 없습니다.")
    return FileResponse(
        storage_path,
        media_type=row["mime_type"],
        filename=row["original_filename"],
    )


@app.delete(
    "/api/v1/calls/{call_id}",
    status_code=204,
    response_class=Response,
    response_model=None,
)
def delete_call(call_id: str) -> Response:
    row = db.get_call_record(call_id)
    if row is None:
        raise HTTPException(status_code=404, detail="통화 기록을 찾을 수 없습니다.")
    storage_path = Path(row["storage_path"])
    processed_dir = get_settings().processed_dir / call_id
    try:
        if processed_dir.exists():
            shutil.rmtree(processed_dir)
        storage_path.unlink(missing_ok=True)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="통화 파일 삭제 중 오류가 발생했습니다.",
        ) from exc
    db.delete_call_record(call_id)
    return Response(status_code=204)
