import React from "react";
import { Composition } from "remotion";
import { Documentary, INTRO_FRAMES } from "./Documentary";
import type { Props } from "./types";

const FPS = 30;

const defaultProps: Props = {
  topic: "city life in the rain",
  narrationPath: "",
  assets: [],
  captions: [],
  showCaptions: true,
  audioDurationInSeconds: 8,
};

// No filesystem access here at all — Python (render_remotion.py) already
// read the asset manifest and captions JSON and resolved the real audio
// duration via ffprobe, so this just does arithmetic on data it was given.
// That sidesteps a real Remotion/webpack quirk: importing "fs" (even as
// "node:fs") inside a file that also gets bundled for the browser preview
// throws "Can't resolve 'fs'" / "UnhandledSchemeError" during bundling.
const calculateMetadata = ({ props }: { props: Props }) => {
  const mainFrames = Math.max(Math.round(props.audioDurationInSeconds * FPS), 1);
  return {
    durationInFrames: INTRO_FRAMES + mainFrames,
    fps: FPS,
  };
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Documentary"
      component={Documentary}
      durationInFrames={240}
      fps={FPS}
      width={1920}
      height={1080}
      defaultProps={defaultProps}
      calculateMetadata={calculateMetadata}
    />
  );
};