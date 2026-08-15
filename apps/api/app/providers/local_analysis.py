from __future__ import annotations

import math
import re
from collections import Counter

from .base import (
    AnalysisResult,
    AnalysisSection,
    CallAnalysisProvider,
    TranscriptResult,
    TranscriptUtterance,
)

TOKEN_PATTERN = re.compile(r"[가-힣A-Za-z0-9]{2,}")
PARTICLE_SUFFIXES = (
    "으로부터",
    "에게서",
    "에서는",
    "으로는",
    "이라고",
    "에서",
    "으로",
    "에게",
    "한테",
    "께서",
    "까지",
    "부터",
    "처럼",
    "보다",
    "하고",
    "이며",
    "에는",
    "에도",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "에",
    "의",
    "도",
    "만",
    "와",
    "과",
    "로",
)
STOP_WORDS = frozenset(
    {
        "안녕하세요",
        "감사합니다",
        "상담센터",
        "그리고",
        "그런데",
        "그러면",
        "그래서",
        "저희",
        "제가",
        "지금",
        "관련",
        "대한",
        "통해서",
        "말씀",
        "정도",
        "아마",
        "있습니다",
        "없습니다",
        "합니다",
        "됩니다",
        "해주세요",
    }
)


def _canonicalize(token: str) -> str:
    token = token.lower()
    for suffix in PARTICLE_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 2:
            return token[: -len(suffix)]
    return token


def _tokens(text: str) -> list[str]:
    tokens = [_canonicalize(token) for token in TOKEN_PATTERN.findall(text)]
    return [token for token in tokens if token not in STOP_WORDS]


def _keyword_counts(utterances: list[TranscriptUtterance]) -> Counter[str]:
    return Counter(token for utterance in utterances for token in _tokens(utterance.text))


def _keywords(utterances: list[TranscriptUtterance], limit: int = 5) -> list[str]:
    counts = _keyword_counts(utterances)
    return [token for token, _ in counts.most_common(limit)]


def _representative_utterances(
    utterances: list[TranscriptUtterance],
    limit: int,
) -> list[TranscriptUtterance]:
    counts = _keyword_counts(utterances)

    def score(utterance: TranscriptUtterance) -> float:
        tokens = _tokens(utterance.text)
        if not tokens:
            return 0
        return sum(counts[token] for token in tokens) / math.sqrt(len(tokens))

    ranked = sorted(utterances, key=lambda item: (-score(item), item.sequence))[:limit]
    return sorted(ranked, key=lambda item: item.sequence)


def _join_text(utterances: list[TranscriptUtterance]) -> str:
    return " ".join(item.text.strip() for item in utterances if item.text.strip())


def _build_sections(utterances: list[TranscriptUtterance]) -> list[AnalysisSection]:
    section_count = min(3, len(utterances))
    sections: list[AnalysisSection] = []
    for index in range(section_count):
        start_index = index * len(utterances) // section_count
        end_index = (index + 1) * len(utterances) // section_count
        group = utterances[start_index:end_index]
        keywords = _keywords(group, limit=3)
        title = " · ".join(keywords[:2]) if keywords else f"구간 {index + 1}"
        summary_items = _representative_utterances(group, limit=min(2, len(group)))
        sections.append(
            AnalysisSection(
                sequence=index + 1,
                title=title,
                start_ms=group[0].start_ms,
                end_ms=group[-1].end_ms,
                summary=_join_text(summary_items),
                keywords=keywords,
            )
        )
    return sections


class LocalExtractiveCallAnalysisProvider(CallAnalysisProvider):
    def analyze(self, transcript: TranscriptResult) -> AnalysisResult:
        utterances = [item for item in transcript.utterances if item.text.strip()]
        if not utterances:
            empty_message = "전사된 내용이 없습니다."
            return AnalysisResult(
                one_line_summary=empty_message,
                detailed_summary=empty_message,
                keywords=[],
                sections=[],
            )

        one_line_item = _representative_utterances(utterances, limit=1)[0]
        representative = _representative_utterances(utterances, limit=min(3, len(utterances)))
        return AnalysisResult(
            one_line_summary=one_line_item.text.strip(),
            detailed_summary=_join_text(representative),
            keywords=_keywords(utterances),
            sections=_build_sections(utterances),
        )
