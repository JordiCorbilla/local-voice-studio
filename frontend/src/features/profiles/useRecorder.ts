import { useEffect, useRef, useState } from "react";

export function useRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [level, setLevel] = useState(0);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [error, setError] = useState("");
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const startedAtRef = useRef<number>(0);
  const meterFrameRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (meterFrameRef.current) {
        cancelAnimationFrame(meterFrameRef.current);
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  async function start() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      setBlob(null);
      setError("");
      setDuration(0);
      streamRef.current = stream;
      mediaRecorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      recorder.onstop = () => {
        setBlob(new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" }));
      };
      recorder.start();
      startedAtRef.current = Date.now();
      setIsRecording(true);
      animateLevel(stream);
    } catch (startError) {
      setError(startError instanceof Error ? startError.message : "Unable to access microphone.");
    }
  }

  function animateLevel(stream: MediaStream) {
    const context = new AudioContext();
    const source = context.createMediaStreamSource(stream);
    const analyser = context.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    const buffer = new Uint8Array(analyser.frequencyBinCount);

    const tick = () => {
      analyser.getByteFrequencyData(buffer);
      const average = buffer.reduce((sum, value) => sum + value, 0) / buffer.length;
      setDuration((Date.now() - startedAtRef.current) / 1000);
      setLevel(average / 255);
      if (isRecording || mediaRecorderRef.current?.state === "recording") {
        meterFrameRef.current = requestAnimationFrame(tick);
      } else {
        context.close().catch(() => undefined);
      }
    };

    meterFrameRef.current = requestAnimationFrame(tick);
  }

  function stop() {
    mediaRecorderRef.current?.stop();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    setIsRecording(false);
    setLevel(0);
  }

  function discard() {
    setBlob(null);
    setDuration(0);
  }

  return {
    isRecording,
    duration,
    level,
    blob,
    error,
    start,
    stop,
    discard,
  };
}
