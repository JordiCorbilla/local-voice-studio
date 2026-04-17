import { useMemo } from "react";
import { formatDuration } from "../../lib/format";
import { useRecorder } from "./useRecorder";

type Props = {
  onSave: (file: File) => Promise<void>;
};

export function RecorderPanel({ onSave }: Props) {
  const recorder = useRecorder();
  const audioUrl = useMemo(() => (recorder.blob ? URL.createObjectURL(recorder.blob) : null), [recorder.blob]);

  return (
    <div className="form-grid">
      <div className="split-header">
        <strong>Browser recording</strong>
        <span className="muted">{formatDuration(recorder.duration)}</span>
      </div>
      <div className="meter">
        <div className="meter-fill" style={{ transform: `scaleX(${Math.max(recorder.level, 0.03)})` }} />
      </div>
      <div className="button-row">
        {!recorder.isRecording ? (
          <button className="button" type="button" onClick={() => recorder.start()}>
            Start recording
          </button>
        ) : (
          <button className="button primary" type="button" onClick={() => recorder.stop()}>
            Stop
          </button>
        )}
        {recorder.blob ? (
          <>
            <button className="button subtle" type="button" onClick={() => recorder.discard()}>
              Discard
            </button>
            <button
              className="button primary"
              type="button"
              onClick={async () => {
                await onSave(new File([recorder.blob!], "recording.webm", { type: recorder.blob!.type || "audio/webm" }));
                recorder.discard();
              }}
            >
              Save recording
            </button>
          </>
        ) : null}
      </div>
      {audioUrl ? <audio className="audio-player" controls src={audioUrl} /> : null}
      {recorder.error ? <p className="error-text">{recorder.error}</p> : <p className="help">Record a reference clip and save it directly to the selected profile.</p>}
    </div>
  );
}
