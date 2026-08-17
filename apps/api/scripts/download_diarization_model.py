from __future__ import annotations

import os
import shutil
from pathlib import Path

from huggingface_hub import snapshot_download
from huggingface_hub.errors import GatedRepoError


def main() -> None:
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        raise SystemExit("HF_TOKEN 또는 HUGGINGFACE_TOKEN 환경 변수가 필요합니다.")

    destination = Path(__file__).resolve().parents[3] / "storage" / "models"
    model_path = destination / "pyannote-speaker-diarization-community-1"
    model_path_existed = model_path.exists()
    try:
        snapshot_download(
            repo_id="pyannote/speaker-diarization-community-1",
            local_dir=model_path,
            token=token,
        )
    except GatedRepoError as exc:
        if not model_path_existed:
            shutil.rmtree(model_path, ignore_errors=True)
        raise SystemExit(
            "모델 접근이 거부되었습니다. Hugging Face 모델 페이지에서 사용 조건에 "
            "동의한 뒤 다시 실행하세요:\n"
            "https://huggingface.co/pyannote/speaker-diarization-community-1"
        ) from exc
    print(f"화자분리 모델 저장 완료: {model_path}")


if __name__ == "__main__":
    main()
