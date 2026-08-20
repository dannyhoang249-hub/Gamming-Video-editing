from __future__ import annotations

import json
from pathlib import Path

from .models import Transcript, TranscriptSegment, Word


def transcribe(
    source: Path,
    model_name: str = "base",
    language: str | None = None,
) -> Transcript:
    """Transcribe media locally with Whisper, preserving word-level timestamps."""
    try:
        import whisper
    except ImportError as exc:
        raise RuntimeError(
            "Whisper is not installed. Run: pip install -e ."
        ) from exc

    model = whisper.load_model(model_name)
    result = model.transcribe(
        str(source),
        language=language,
        word_timestamps=True,
        verbose=False,
    )

    segments: list[TranscriptSegment] = []
    for index, item in enumerate(result.get("segments", [])):
        words = [
            Word(
                word=str(word.get("word", "")).strip(),
                start=float(word.get("start", item["start"])),
                end=float(word.get("end", item["end"])),
            )
            for word in item.get("words", [])
        ]
        segments.append(
            TranscriptSegment(
                id=index,
                start=float(item["start"]),
                end=float(item["end"]),
                text=str(item["text"]).strip(),
                words=words,
            )
        )

    return Transcript(
        source=str(source),
        language=str(result.get("language", language or "unknown")),
        duration=max((segment.end for segment in segments), default=0.0),
        segments=segments,
    )


def save_transcript(transcript: Transcript, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(transcript.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_transcript(path: Path) -> Transcript:
    return Transcript.model_validate_json(path.read_text(encoding="utf-8"))