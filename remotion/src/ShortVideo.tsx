import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Video,
} from "remotion";
import type {RenderProps} from "./index";

type Segment = {
  start: number;
  end: number;
  text: string;
  words?: Array<{word: string; start: number; end: number}>;
};

type Props = RenderProps & {
  transcript_data?: {segments: Segment[]};
};

export const ShortVideo: React.FC<Props> = (props) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const time = frame / fps;
  const accent = props.brand.accent;
  const current = props.transcript_data?.segments.find(
    (segment) => time >= segment.start && time <= segment.end,
  );
  const words = current?.words ?? [];
  const activeWord = words.findIndex(
    (word) => time >= word.start && time <= word.end,
  );
  const scale = spring({frame, fps, config: {damping: 14}});
  const progress = interpolate(frame, [0, 45], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{backgroundColor: "#111827", fontFamily: props.brand.font_family}}>
      <Video src={props.source} style={{width: "100%", height: "100%", objectFit: "cover"}} />
      <AbsoluteFill style={{background: "linear-gradient(180deg, rgba(0,0,0,.35), transparent 35%, rgba(0,0,0,.78))"}} />

      <div style={{position: "absolute", top: 72, left: 60, right: 60, display: "flex", alignItems: "center", gap: 20}}>
        {props.brand.logo_path ? (
          <img src={props.brand.logo_path} style={{width: 76, height: 76, objectFit: "contain"}} />
        ) : null}
        {props.brand.watermark ? (
          <span style={{color: props.brand.text_color, fontSize: 34, fontWeight: 800}}>
            {props.brand.name}
          </span>
        ) : null}
      </div>

      <div style={{position: "absolute", left: 54, right: 54, bottom: 220, transform: `scale(${0.96 + scale * 0.04})`}}>
        <div style={{display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 12, padding: 24}}>
          {words.length ? words.map((word, index) => (
            <span key={`${word.start}-${index}`} style={{
              color: index === activeWord ? "#111827" : props.brand.text_color,
              backgroundColor: index === activeWord ? accent : "rgba(0,0,0,.58)",
              fontSize: 58, lineHeight: 1.15, fontWeight: 900,
              padding: "8px 14px", borderRadius: 12,
            }}>{word.word}</span>
          )) : (
            <span style={{color: props.brand.text_color, backgroundColor: "rgba(0,0,0,.62)", fontSize: 56, fontWeight: 800, padding: 18, borderRadius: 14, textAlign: "center"}}>{current?.text ?? ""}</span>
          )}
        </div>
      </div>

      <div style={{position: "absolute", bottom: 90, left: 54, right: 54, height: 8, background: "rgba(255,255,255,.3)", borderRadius: 99}}>
        <div style={{width: `${progress * 100}%`, height: "100%", background: accent, borderRadius: 99}} />
      </div>

      {props.music ? <Audio src={props.music} volume={0.2} /> : null}
    </AbsoluteFill>
  );
};