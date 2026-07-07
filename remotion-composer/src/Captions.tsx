import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { CaptionWord } from "./types";

type Phrase = { text: string; start: number; end: number };

const MAX_WORDS_PER_PHRASE = 6;
const MAX_GAP_SECONDS = 0.6; // a pause this long starts a new phrase

/**
 * Groups individual Whisper word timestamps into short phrases, so text
 * appears as designed kinetic-typography chunks (slide + fade + scale in)
 * rather than one word lighting up at a time. Still driven by the real
 * alignment timestamps — just grouped for a more intentional motion feel.
 */
function groupIntoPhrases(words: CaptionWord[]): Phrase[] {
  const phrases: Phrase[] = [];
  let current: CaptionWord[] = [];

  const flush = () => {
    if (current.length === 0) return;
    phrases.push({
      text: current.map((w) => w.word).join(" "),
      start: current[0].start,
      end: current[current.length - 1].end,
    });
    current = [];
  };

  for (const word of words) {
    const prev = current[current.length - 1];
    const gap = prev ? word.start - prev.end : 0;
    if (prev && (gap > MAX_GAP_SECONDS || current.length >= MAX_WORDS_PER_PHRASE)) {
      flush();
    }
    current.push(word);
  }
  flush();

  return phrases;
}

export const Captions: React.FC<{ words: CaptionWord[] }> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const phrases = React.useMemo(() => groupIntoPhrases(words), [words]);
  if (!phrases.length) return null;

  const active = phrases.find((p) => t >= p.start && t <= p.end + 0.15);
  if (!active) return null;

  const localFrame = frame - Math.round(active.start * fps);
  const entrance = spring({ frame: localFrame, fps, config: { damping: 16, mass: 0.5 } });
  const opacity = interpolate(localFrame, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(entrance, [0, 1], [28, 0]);
  const scale = interpolate(entrance, [0, 1], [0.92, 1]);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 120,
      }}
    >
      <div
        style={{
          opacity,
          transform: `translateY(${translateY}px) scale(${scale})`,
          maxWidth: "78%",
          padding: "18px 34px",
          borderRadius: 4,
          background:
            "linear-gradient(180deg, rgba(42,33,64,0) 0%, rgba(42,33,64,0.72) 35%, rgba(42,33,64,0.72) 100%)",
        }}
      >
        <div
          style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontWeight: 600,
            fontSize: 58,
            lineHeight: 1.15,
            textAlign: "center",
            color: "#FFFACD",
          }}
        >
          {active.text}
        </div>
      </div>
    </AbsoluteFill>
  );
};