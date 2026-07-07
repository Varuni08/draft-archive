export type AssetItem = {
  title: string;
  staticPath: string; // relative to public/ (via staticFile()), e.g. "assets/asset_000.jpg"
};

export type CaptionWord = {
  word: string;
  start: number; // seconds
  end: number; // seconds
};

export type Props = {
  topic: string;
  narrationPath: string; // filename relative to public/ (via staticFile()), or "" if none
  assets: AssetItem[];
  captions: CaptionWord[];
  showCaptions: boolean;
  audioDurationInSeconds: number;
};