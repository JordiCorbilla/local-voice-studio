type Props = {
  src: string;
};

export function AudioPlayer({ src }: Props) {
  return <audio controls preload="none" className="audio-player" src={src} />;
}
