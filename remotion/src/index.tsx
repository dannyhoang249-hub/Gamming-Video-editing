import React from "react";
import {registerRoot, Composition} from "remotion";
import {ShortVideo} from "./ShortVideo";

export type RenderProps = {
  source: string;
  transcript: string;
  transcript_data?: {
    segments: Array<{
      start: number;
      end: number;
      text: string;
      words?: Array<{word: string; start: number; end: number}>;
    }>;
  };
  music?: string | null;
  aspect_ratio?: "16:9" | "9:16";
  clips: Array<{start: number; end: number; text: string}>;
  brand: {
    name: string;
    accent: string;
    text_color: string;
    font_family: string;
    logo_path?: string | null;
    watermark: boolean;
  };
};

const Root: React.FC = () => (
  <Composition
    id="ShortVideo"
    component={ShortVideo}
    durationInFrames={30 * 60}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={{
      source: "",
      transcript: "",
      aspect_ratio: "16:9",
      clips: [],
      brand: {
        name: "Your Brand",
        accent: "#7C3AED",
        text_color: "#FFFFFF",
        font_family: "Arial",
        watermark: true,
      },
    }}
    calculateMetadata={({props}) => ({
      durationInFrames: Math.max(
        1,
        Math.ceil((props.clips.at(-1)?.end ?? 60) * 30),
      ),
    })}
  />
);

registerRoot(Root);