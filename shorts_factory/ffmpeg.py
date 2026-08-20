from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from .models import Clip


class FFmpegError(RuntimeError):
    pass


def require_ffmpeg() -> str:
    binary = shutil.which("ffmpeg")
    if not binary:
        raise FFmpegError("FFmpeg is required. Install it with: brew install ffmpeg")
    return binary


def _run(args: Sequence[str]) -> None:
    try:
        subprocess.run(args, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise FFmpegError(exc.stderr[-2000:]) from exc


def cut_clip(source: Path, clip: Clip, destination: Path) -> None:
    ffmpeg = require_ffmpeg()
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run([
        ffmpeg, "-y", "-ss", str(clip.start), "-i", str(source),
        "-t", str(clip.duration), "-map", "0:v:0", "-map", "0:a:0?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-movflags", "+faststart", str(destination),
    ])


def concat_clips(clips: Sequence[Path], destination: Path, music: Path | None = None) -> None:
    if not clips:
        raise FFmpegError("No clips were selected; cannot assemble an output video.")

    ffmpeg = require_ffmpeg()
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest = destination.parent / "concat.txt"

    lines = []
    for clip in clips:
        escaped_path = clip.resolve().as_posix().replace("'", "'\\''")
        lines.append(f"file '{escaped_path}'\n")
    manifest.write_text("".join(lines), encoding="utf-8")
    if music:
        _run([
            ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(manifest),
            "-stream_loop", "-1", "-i", str(music),
            "-filter_complex",
            "[0:a]volume=1.0[a0];[1:a]volume=0.12,aloop=loop=-1:size=2e+09[a1];"
            "[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v:0", "-map", "[aout]", "-c:v", "libx264", "-c:a", "aac",
            "-shortest", "-movflags", "+faststart", str(destination),
        ])
    else:
        _run([
            ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(manifest),
            "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", str(destination),
        ])


def make_vertical(
    source: Path,
    destination: Path,
    aspect_ratio: str = "16:9",
) -> None:
    if aspect_ratio == "16:9":
        width, height = 1920, 1080
    elif aspect_ratio == "9:16":
        width, height = 1080, 1920
    else:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")

    ffmpeg = require_ffmpeg()
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run([
        ffmpeg, "-y", "-i", str(source),
        "-vf", (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},setsar=1"
        ),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-movflags", "+faststart", str(destination),
    ])