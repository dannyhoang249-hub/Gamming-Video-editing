from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import PipelineConfig
from .pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Create branded vertical shorts from a long video.")
    parser.add_argument("input", type=Path, help="Source video path")
    parser.add_argument("--config", type=Path, help="YAML or JSON pipeline config")
    parser.add_argument("--output", type=Path, default=Path("out"))
    parser.add_argument("--transcript", type=Path, help="Use an existing Whisper JSON transcript")
    parser.add_argument("--model", default="base", help="Whisper model name")
    parser.add_argument("--clips", type=int, default=3)
    parser.add_argument("--render", action="store_true", help="Render the Remotion composition")
    args = parser.parse_args()

    data: dict = {}
    if args.config:
        if args.config.suffix.lower() in {".yaml", ".yml"}:
            import yaml
            data = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
        else:
            data = json.loads(args.config.read_text(encoding="utf-8"))

    config = PipelineConfig(
        input=args.input,
        output_dir=args.output,
        model=args.model,
        clip_count=args.clips,
        **{key: value for key, value in data.items() if key not in {"input", "output_dir"}},
    )
    result = run_pipeline(config, transcript_path=args.transcript, render=args.render)
    print(json.dumps({key: str(value) for key, value in result.items() if key != "clips"}, indent=2))