from __future__ import annotations

import os
import warnings
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from .base import SpeakerDiarizationProvider, SpeakerTurn, TranscriptResult, TranscriptUtterance

PipelineFactory = Callable[..., Any]
AudioLoader = Callable[[str], Any]


def assign_speakers(
    transcript: TranscriptResult, speaker_turns: Iterable[SpeakerTurn]
) -> TranscriptResult:
    """Assign the speaker with the greatest time overlap to every STT segment."""
    turns = list(speaker_turns)
    if not turns:
        return transcript

    label_order: dict[str, str] = {}
    for turn in sorted(turns, key=lambda item: (item.start_ms, item.end_ms)):
        if turn.speaker not in label_order:
            label_order[turn.speaker] = f"화자 {len(label_order) + 1}"

    utterances: list[TranscriptUtterance] = []
    previous_speaker: str | None = None
    for item in transcript.utterances:
        best_turn: SpeakerTurn | None = None
        best_overlap = 0
        midpoint = (item.start_ms + item.end_ms) / 2
        nearest_distance = float("inf")

        for turn in turns:
            overlap = max(0, min(item.end_ms, turn.end_ms) - max(item.start_ms, turn.start_ms))
            turn_midpoint = (turn.start_ms + turn.end_ms) / 2
            distance = abs(midpoint - turn_midpoint)
            if overlap > best_overlap or (overlap == best_overlap and distance < nearest_distance):
                best_turn = turn
                best_overlap = overlap
                nearest_distance = distance

        if best_turn is not None and best_overlap > 0:
            speaker = label_order[best_turn.speaker]
        elif previous_speaker is not None:
            speaker = previous_speaker
        else:
            speaker = item.speaker

        previous_speaker = speaker
        utterances.append(
            TranscriptUtterance(
                sequence=item.sequence,
                speaker=speaker,
                start_ms=item.start_ms,
                end_ms=item.end_ms,
                text=item.text,
            )
        )

    return TranscriptResult(duration_ms=transcript.duration_ms, utterances=utterances)


class PyannoteSpeakerDiarizationProvider(SpeakerDiarizationProvider):
    def __init__(
        self,
        model_path: Path,
        device: str = "cpu",
        min_speakers: int | None = None,
        max_speakers: int | None = None,
        pipeline_factory: PipelineFactory | None = None,
        audio_loader: AudioLoader | None = None,
    ) -> None:
        if not model_path.is_dir() or not (model_path / "config.yaml").is_file():
            raise FileNotFoundError(f"화자분리 모델 디렉터리를 찾을 수 없습니다: {model_path}")

        os.environ.setdefault("PYANNOTE_METRICS_ENABLED", "0")
        if pipeline_factory is None:
            import torch

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=r"\s*torchcodec is not installed correctly.*",
                )
                from pyannote.audio import Pipeline

            pipeline_factory = Pipeline.from_pretrained
            target_device: Any = torch.device(device)
        else:
            target_device = device

        if audio_loader is None:
            import soundfile
            import torch

            def load_audio(audio_path: str) -> dict[str, Any]:
                samples, sample_rate = soundfile.read(
                    audio_path,
                    dtype="float32",
                    always_2d=True,
                )
                return {
                    "waveform": torch.from_numpy(samples.T),
                    "sample_rate": sample_rate,
                }

            audio_loader = load_audio

        pipeline = pipeline_factory(str(model_path))
        if pipeline is None:
            raise RuntimeError(f"화자분리 모델을 불러오지 못했습니다: {model_path}")
        if hasattr(pipeline, "to"):
            pipeline.to(target_device)

        self._pipeline = pipeline
        self._audio_loader = audio_loader
        self._min_speakers = min_speakers
        self._max_speakers = max_speakers

    def diarize(self, audio_path: str) -> list[SpeakerTurn]:
        options: dict[str, int] = {}
        if self._min_speakers is not None:
            options["min_speakers"] = self._min_speakers
        if self._max_speakers is not None:
            options["max_speakers"] = self._max_speakers

        # Preload audio to avoid TorchCodec/FFmpeg DLL compatibility issues on Windows.
        output = self._pipeline(self._audio_loader(audio_path), **options)
        annotation = getattr(output, "exclusive_speaker_diarization", None)
        if annotation is None:
            annotation = getattr(output, "speaker_diarization", output)

        turns: list[SpeakerTurn] = []
        for item in annotation:
            if len(item) == 2:
                segment, speaker = item
            else:
                segment, _, speaker = item
            turns.append(
                SpeakerTurn(
                    start_ms=round(float(segment.start) * 1000),
                    end_ms=round(float(segment.end) * 1000),
                    speaker=str(speaker),
                )
            )
        return turns
