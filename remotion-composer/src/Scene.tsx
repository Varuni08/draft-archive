import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { AssetItem } from "./types";

/**
 * One still image, slowly zoomed and panned (the classic "Ken Burns"
 * documentary look), for the portion of the timeline this scene owns.
 */
export const Scene: React.FC<{
  asset: AssetItem | undefined;
  durationInFrames: number;
  direction: "in" | "out";
}> = ({ asset, durationInFrames, direction }) => {
  const { width, height } = useVideoConfig();
  const localFrame = useCurrentFrame();

  const progress = interpolate(localFrame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const scale =
    direction === "in"
      ? interpolate(progress, [0, 1], [1, 1.12])
      : interpolate(progress, [0, 1], [1.12, 1]);

  const opacity = interpolate(
    localFrame,
    [0, 12, durationInFrames - 12, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ opacity }}>
      {asset ? (
        <Img
          src={staticFile(asset.staticPath)}
          style={{
            width,
            height,
            objectFit: "cover",
            transform: `scale(${scale})`,
          }}
        />
      ) : (
        // No footage fetched yet (e.g. offline run) — fall back to a plain
        // brand-colored background rather than a broken image.
        <AbsoluteFill style={{ backgroundColor: "#5F4A8B" }} />
      )}
    </AbsoluteFill>
  );
};