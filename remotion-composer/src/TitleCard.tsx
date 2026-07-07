import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * A short animated title card, in the same visual language as the project's
 * landing page: Ultra Violet background, Cormorant Garamond italic display
 * type, a small mono-caps eyebrow, a thin cream rule. This is the one
 * deliberately bold motion moment that opens every video.
 */
export const TitleCard: React.FC<{ topic: string }> = ({ topic }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const eyebrowOpacity = interpolate(frame, [0, 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const titleSpring = spring({ frame, fps, config: { damping: 14, mass: 0.6 } });
  const titleOpacity = interpolate(frame, [6, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const titleY = interpolate(titleSpring, [0, 1], [24, 0]);

  const ruleWidth = interpolate(frame, [20, 34], [0, 120], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#5F4A8B",
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
        gap: 22,
      }}
    >
      <div
        style={{
          opacity: eyebrowOpacity,
          fontFamily: "'IBM Plex Sans', sans-serif",
          fontWeight: 600,
          fontSize: 22,
          letterSpacing: "0.28em",
          textTransform: "uppercase",
          color: "#B7A9D6",
        }}
      >
        Draft Archive
      </div>

      <div
        style={{
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
          fontFamily: "'Cormorant Garamond', serif",
          fontStyle: "italic",
          fontWeight: 500,
          fontSize: 92,
          color: "#FFFACD",
          textAlign: "center",
          maxWidth: "80%",
          lineHeight: 1.05,
        }}
      >
        {topic}
      </div>

      <div
        style={{
          width: ruleWidth,
          height: 2,
          backgroundColor: "#FFFACD",
        }}
      />
    </AbsoluteFill>
  );
};
