from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .ffmpeg import concat_clips, cut_clip, make_vertical
from .models import Clip, PipelineConfig, Transcript, TranscriptSegment, Word
from .selector import select_highlights
from .transcriber import load_transcript, save_transcript, transcribe


def _timeline_transcript(transcript: Transcript, clips: list[Clip]) -> Transcript:
    """Map source timestamps onto the concatenated clip timeline."""
    mapped_segments: list[TranscriptSegment] = []
    timeline_offset = 0.0

    for clip in clips:
        for segment in transcript.segments:
            start = max(segment.start, clip.start)
            end = min(segment.end, clip.end)
            if end <= start:
                continue

            mapped_words = [
                Word(
                    word=word.word,
                    start=round(timeline_offset + max(word.start, clip.start) - clip.start, 3),
                    end=round(timeline_offset + min(word.end, clip.end) - clip.start, 3),
                )
                for word in segment.words
                if word.end > clip.start and word.start < clip.end
            ]
            mapped_segments.append(
                TranscriptSegment(
                    id=len(mapped_segments),
                    start=round(timeline_offset + start - clip.start, 3),
                    end=round(timeline_offset + end - clip.start, 3),
                    text=segment.text,
                    words=mapped_words,
                )
            )
        timeline_offset += clip.duration

    return Transcript(
        source=transcript.source,
        language=transcript.language,
        duration=round(timeline_offset, 3),
        segments=mapped_segments,
    )


def write_render_manifest(
    config: PipelineConfig,
    clips: list[Clip],
    transcript: Transcript,
    transcript_path: Path,
    source_video: Path,
) -> Path:
    timeline_transcript = _timeline_transcript(transcript, clips)
    manifest = config.output_dir / "render-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "source": str(source_video.resolve()),
                "transcript": str(transcript_path.resolve()),
                "transcript_data": timeline_transcript.model_dump(mode="json"),
                "clips": [clip.model_dump(mode="json") for clip in clips],
                "brand": config.brand.model_dump(mode="json"),
                "music": str(config.music_path.resolve()) if config.music_path else None,
                "aspect_ratio": config.aspect_ratio,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest


def run_pipeline(
    config: PipelineConfig,
    transcript_path: Path | None = None,
    render: bool = False,
) -> dict[str, object]:
    if not config.input.exists():
        raise FileNotFoundError(f"Input video not found: {config.input}")
    config.output_dir.mkdir(parents=True, exist_ok=True)

    transcript_file = transcript_path or config.output_dir / "transcript.json"
    transcript = (
        load_transcript(transcript_file)
        if transcript_file.exists()
        else transcribe(config.input, config.model, config.language)
    )
    save_transcript(transcript, transcript_file)

    clips = select_highlights(
        transcript,
        count=config.clip_count,
        minimum=config.min_clip_seconds,
        maximum=config.max_clip_seconds,
        padding=config.padding_seconds,
        ai_model=config.ai_model,
    )

    clip_files: list[Path] = []
    for clip in clips:
        path = config.output_dir / "clips" / f"{clip.id}.mp4"
        cut_clip(config.input, clip, path)
        clip_files.append(path)

    assembled = config.output_dir / "assembled.mp4"
    concat_clips(clip_files, assembled, config.music_path)
    vertical = config.output_dir / "vertical-source.mp4"
    make_vertical(assembled, vertical, config.aspect_ratio)
    manifest = write_render_manifest(config, clips, transcript, transcript_file, vertical)

    rendered: Path | None = None
    if render:
        rendered = config.output_dir / "short.mp4"
        subprocess.run(
            [
                "npx", "--prefix", "remotion", "remotion", "render", "remotion/src/index.tsx",
                "ShortVideo", str(rendered), "--props", str(manifest),
            ],
            check=True,
        )

    return {
        "transcript": transcript_file,
        "clips": clips,
        "assembled": assembled,
        "vertical_source": vertical,
        "manifest": manifest,
        "rendered": rendered,
    }