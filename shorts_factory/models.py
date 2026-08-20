from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class Word(BaseModel):
    word: str
    start: float
    end: float


class TranscriptSegment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    words: list[Word] = Field(default_factory=list)


class Transcript(BaseModel):
    source: str
    language: str = "unknown"
    duration: float = 0.0
    segments: list[TranscriptSegment] = Field(default_factory=list)


class Clip(BaseModel):
    id: str
    start: float
    end: float
    score: float = 0.0
    reason: str = ""
    text: str = ""
    source: str = ""

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


class BrandConfig(BaseModel):
    name: str = "Your Brand"
    accent: str = "#7C3AED"
    text_color: str = "#FFFFFF"
    font_family: str = "Arial"
    logo_path: str | None = None
    watermark: bool = True


class PipelineConfig(BaseModel):
    input: Path
    output_dir: Path = Path("out")
    model: str = "base"
    language: str | None = None
    clip_count: int = Field(default=3, ge=1, le=20)
    min_clip_seconds: float = Field(default=12.0, gt=0)
    max_clip_seconds: float = Field(default=55.0, gt=0)
    padding_seconds: float = Field(default=1.5, ge=0)
    aspect_ratio: Literal["16:9", "9:16"] = "16:9"
    brand: BrandConfig = Field(default_factory=BrandConfig)
    music_path: Path | None = None
    ai_model: str = "gpt-4o-mini"