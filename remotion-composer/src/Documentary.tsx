import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import { Scene } from "./Scene";
import { Captions } from "./Captions";
import { TitleCard } from "./TitleCard";
import type { Props } from "./types";

export const INTRO_FRAMES = 60; // 2s at 30fps — kept in sync with Root.tsx's duration math

export const Documentary: React.FC<Props> = ({
  topic,
  narrationPath,
  assets,
  captions,
  showCaptions,
}) => {
  const { durationInFrames } = useVideoConfig();
  const mainDuration = Math.max(durationInFrames - INTRO_FRAMES, 1);

  // Split the main runtime evenly across whatever assets we have (at least
  // one "scene" even if no footage was fetched, so it never renders blank).
  const sceneCount = Math.max(assets.length, 1);
  const sceneDuration = Math.ceil(mainDuration / sceneCount);

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <Sequence from={0} durationInFrames={INTRO_FRAMES}>
        <TitleCard topic={topic} />
      </Sequence>

      <Sequence from={INTRO_FRAMES}>
        <AbsoluteFill>
          {Array.from({ length: sceneCount }).map((_, i) => {
            const from = i * sceneDuration;
            return (
              <Sequence key={i} from={from} durationInFrames={sceneDuration}>
                <Scene
                  asset={assets[i]}
                  durationInFrames={sceneDuration}
                  direction={i % 2 === 0 ? "in" : "out"}
                />
              </Sequence>
            );
          })}

          {narrationPath ? <Audio src={staticFile(narrationPath)} /> : null}

          {showCaptions ? <Captions words={captions} /> : null}
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};