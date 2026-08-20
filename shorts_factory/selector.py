from __future__ import annotations

import json
import os
import re
from typing import Any

from .models import Clip, Transcript


HOOK_WORDS = {
    "how", "why", "secret", "mistake", "truth", "never", "best", "worst",
    "first", "because", "imagine", "important", "problem", "solution",
    "bí mật", "sai lầm", "sự thật", "tại sao", "cách", "quan trọng",
}


def _heuristic_candidates(
    transcript: Transcript,
    count: int,
    minimum: float,
    maximum: float,
    padding: float,
) -> list[Clip]:
    segments = transcript.segments
    candidates: list[Clip] = []
    for index, segment in enumerate(segments):
        text = segment.text.strip()
        if not text:
            continue
        start = max(0.0, segment.start - padding)
        end = min(transcript.duration or segment.end + padding, segment.end + padding)
        while end - start < minimum and (index + 1 < len(segments)):
            index += 1
            end = min(transcript.duration or segments[index].end, segments[index].end + padding)
        end = min(end, start + maximum)
        words = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
        hook_hits = sum(word in HOOK_WORDS for word in words)
        punctuation = int("?" in text or "!" in text)
        density = min(len(words) / max(segment.end - segment.start, 1), 4) / 4
        score = min(1.0, 0.18 + hook_hits * 0.12 + punctuation * 0.12 + density * 0.35)
        candidates.append(
            Clip(
                id=f"clip-{len(candidates) + 1:02d}",
                start=round(start, 3),
                end=round(end, 3),
                score=round(score, 3),
                reason="heuristic hook/rhythm score",
                text=text,
                source=transcript.source,
            )
        )

    candidates.sort(key=lambda clip: clip.score, reverse=True)
    selected: list[Clip] = []
    for clip in candidates:
        if all(clip.end <= item.start or clip.start >= item.end for item in selected):
            selected.append(clip)
        if len(selected) == count:
            break
    return sorted(selected, key=lambda clip: clip.start)


def _llm_select(transcript: Transcript, model: str, count: int) -> list[dict[str, Any]]:
    from openai import OpenAI

    client = OpenAI()
    compact = [
        {"id": segment.id, "start": segment.start, "end": segment.end, "text": segment.text}
        for segment in transcript.segments
    ]
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Select the most engaging short-video moments. Return JSON with "
                    "clips: [{start, end, score, reason, text}]. Prefer self-contained "
                    "hooks, surprising claims, emotional turns, and actionable insights. "
                    "Return no more than the requested count."
                ),
            },
            {
                "role": "user",
                "content": json.dumps({"count": count, "segments": compact}, ensure_ascii=False),
            },
        ],
    )
    return json.loads(response.choices[0].message.content or "{}").get("clips", [])


def select_highlights(
    transcript: Transcript,
    count: int = 3,
    minimum: float = 12.0,
    maximum: float = 55.0,
    padding: float = 1.5,
    ai_model: str = "gpt-4o-mini",
) -> list[Clip]:
    if os.getenv("OPENAI_API_KEY"):
        try:
            raw = _llm_select(transcript, ai_model, count)
            clips = [
                Clip(
                    id=f"clip-{index + 1:02d}",
                    start=max(0.0, float(item["start"]) - padding),
                    end=min(transcript.duration, float(item["end"]) + padding),
                    score=float(item.get("score", 0.8)),
                    reason=str(item.get("reason", "LLM-selected highlight")),
                    text=str(item.get("text", "")),
                    source=transcript.source,
                )
                for index, item in enumerate(raw[:count])
            ]
            if clips:
                return sorted(clips, key=lambda clip: clip.start)
        except Exception:
            pass

    return _heuristic_candidates(transcript, count, minimum, maximum, padding)