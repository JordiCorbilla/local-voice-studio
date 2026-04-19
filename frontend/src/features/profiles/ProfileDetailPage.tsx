import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../../api/client";
import { AudioPlayer } from "../../components/AudioPlayer";
import { EmptyState } from "../../components/EmptyState";
import { SectionCard } from "../../components/SectionCard";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDate, formatDuration } from "../../lib/format";
import { ProfileForm, type ProfileFormValues } from "./ProfileForm";
import { RecorderPanel } from "./RecorderPanel";

const referenceScripts = [
  {
    label: "Balanced read",
    text:
      "Hello, this is a voice reference for Local Voice Studio. I am speaking in a calm, natural tone at a steady pace. Today the weather is mild, and the streets are busy with people heading to work, school, and home. I enjoy clear communication, careful pronunciation, and relaxed conversation. This sample includes short and long words, different sentence shapes, and a normal speaking rhythm.",
  },
  {
    label: "Natural intro",
    text:
      "Good morning. My name is [your name], and this is another clean voice sample. I am reading in my usual speaking style, without rushing or exaggerating. The purpose of this recording is to capture my natural accent, pitch, and cadence. I would like the generated voice to sound clear, grounded, and consistent across everyday sentences.",
  },
];

function toPayload(values: ProfileFormValues) {
  return {
    ...values,
    tags: values.tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
  };
}

export function ProfileDetailPage() {
  const { profileId = "" } = useParams();
  const queryClient = useQueryClient();
  const [clipDrafts, setClipDrafts] = useState<Record<string, string>>({});
  const [transcribingClipId, setTranscribingClipId] = useState<string | null>(null);
  const [clipActionError, setClipActionError] = useState("");
  const profileQuery = useQuery({
    queryKey: ["profile", profileId],
    queryFn: () => api.getProfile(profileId),
    enabled: Boolean(profileId),
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["profiles"] });
    queryClient.invalidateQueries({ queryKey: ["profile", profileId] });
    queryClient.invalidateQueries({ queryKey: ["generations"] });
  };

  const updateProfile = useMutation({
    mutationFn: (values: ProfileFormValues) => api.updateProfile(profileId, toPayload(values)),
    onSuccess: refresh,
  });
  const uploadClip = useMutation({
    mutationFn: (file: File) => api.uploadClip(profileId, file),
    onSuccess: refresh,
  });
  const uploadRecording = useMutation({
    mutationFn: (file: File) => api.uploadRecording(profileId, file),
    onSuccess: refresh,
  });
  const deleteClip = useMutation({
    mutationFn: (clipId: string) => api.deleteClip(profileId, clipId),
    onSuccess: refresh,
  });
  const setPrimary = useMutation({
    mutationFn: (clipId: string) => api.setPrimaryClip(profileId, clipId),
    onSuccess: refresh,
  });
  const updateTranscript = useMutation({
    mutationFn: ({ clipId, referenceText }: { clipId: string; referenceText: string }) =>
      api.updateClipTranscript(profileId, clipId, referenceText),
    onSuccess: () => {
      setClipActionError("");
      refresh();
    },
    onError: (mutationError) => {
      setClipActionError(mutationError instanceof Error ? mutationError.message : "Unable to save transcript.");
    },
  });
  const transcribeClip = useMutation({
    mutationFn: (clipId: string) => api.transcribeClip(profileId, clipId),
    onMutate: (clipId) => {
      setTranscribingClipId(clipId);
      setClipActionError("");
    },
    onSuccess: () => {
      refresh();
    },
    onError: (mutationError) => {
      setClipActionError(mutationError instanceof Error ? mutationError.message : "Unable to transcribe clip.");
    },
    onSettled: () => {
      setTranscribingClipId(null);
    },
  });

  if (!profileQuery.data) {
    return (
      <div className="page">
        <p className="muted">Loading profile...</p>
      </div>
    );
  }

  const profile = profileQuery.data;

  return (
    <div className="page">
      <div className="page-header">
        <h1>{profile.display_name}</h1>
        <p className="muted">Manage reference clips, update defaults, and review recent outputs for this profile.</p>
      </div>

      <div className="profile-grid">
        <div className="page">
          <SectionCard title="Profile settings" description="Edit the metadata and synthesis defaults for this voice.">
            <ProfileForm
              initialProfile={profile}
              submitLabel="Save changes"
              onSubmit={(values) => updateProfile.mutateAsync(values).then(() => undefined)}
            />
          </SectionCard>

          <SectionCard title="Reference clips" description="Upload normalized voice references or record a new one.">
            <div className="guidance-card">
              <strong>Similarity checklist</strong>
              <div className="pill-row">
                <span className="pill">1 primary clip</span>
                <span className="pill">15 to 30 seconds</span>
                <span className="pill">quiet room</span>
                <span className="pill">steady natural tone</span>
              </div>
              <p className="muted">
                XTTS zero-shot is much more sensitive to clip quality than clip quantity. Start with one clean primary
                reference and only add alternates if they sound equally close to your real voice.
              </p>
              <p className="muted">
                Qwen-style cloning also wants the transcript of the selected primary clip. Paste exactly what you said,
                or use local transcription if available.
              </p>
            </div>
            <div className="reference-script-block">
              <div className="split-header">
                <div>
                  <strong>Suggested reference text</strong>
                  <p className="muted">Read one prompt naturally for 15 to 30 seconds in a quiet room.</p>
                </div>
              </div>
              <div className="reference-script-list">
                {referenceScripts.map((script) => (
                  <div key={script.label} className="reference-script-card">
                    <div className="split-header">
                      <span className="pill">{script.label}</span>
                      <button
                        className="button subtle"
                        type="button"
                        onClick={async () => {
                          await navigator.clipboard.writeText(script.text);
                        }}
                      >
                        Copy text
                      </button>
                    </div>
                    <p>{script.text}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="button-row">
              <label className="button subtle">
                Upload clip
                <input
                  hidden
                  type="file"
                  accept=".wav,.mp3,.m4a,.flac,.ogg,.webm,audio/*"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) {
                      uploadClip.mutate(file);
                    }
                  }}
                />
              </label>
            </div>
            <RecorderPanel onSave={(file) => uploadRecording.mutateAsync(file).then(() => undefined)} />
            {profile.clips.length ? (
              <div className="list">
                {clipActionError ? <p className="error-text">{clipActionError}</p> : null}
                {profile.clips.map((clip) => (
                  <div key={clip.id} className="clip-row">
                    <div className="split-header">
                      <div>
                        <strong>{clip.original_filename}</strong>
                        <p className="muted">
                          {formatDuration(clip.duration_seconds)} | {clip.sample_rate} Hz | {formatDate(clip.created_at)}
                        </p>
                      </div>
                      {clip.is_primary ? <span className="pill">Primary</span> : null}
                    </div>
                    <AudioPlayer src={clip.audio_url} />
                    <div className="field">
                      <label htmlFor={`clip-transcript-${clip.id}`}>Reference transcript</label>
                      <textarea
                        id={`clip-transcript-${clip.id}`}
                        value={clipDrafts[clip.id] ?? clip.reference_text}
                        onChange={(event) =>
                          setClipDrafts((current) => ({
                            ...current,
                            [clip.id]: event.target.value,
                          }))
                        }
                        placeholder="Paste the exact words spoken in this reference clip..."
                      />
                      <p className="help">
                        {clip.transcript_source === "transcribed"
                          ? "Transcript source: local transcription"
                          : clip.transcript_source === "manual"
                            ? "Transcript source: manual"
                            : "No transcript saved yet"}
                      </p>
                    </div>
                    <div className="button-row">
                      {!clip.is_primary ? (
                        <button className="button subtle" type="button" onClick={() => setPrimary.mutate(clip.id)}>
                          Set primary
                        </button>
                      ) : null}
                      <button
                        className="button subtle"
                        type="button"
                        onClick={() =>
                          updateTranscript.mutate({
                            clipId: clip.id,
                            referenceText: (clipDrafts[clip.id] ?? clip.reference_text).trim(),
                          })
                        }
                      >
                        Save transcript
                      </button>
                      <button
                        className="button subtle"
                        type="button"
                        disabled={transcribingClipId === clip.id || transcribingClipId !== null}
                        onClick={() => transcribeClip.mutate(clip.id)}
                      >
                        {transcribingClipId === clip.id ? (
                          <>
                            <span className="spinner" aria-hidden="true" />
                            Transcribing...
                          </>
                        ) : (
                          "Transcribe locally"
                        )}
                      </button>
                      <button className="button danger" type="button" onClick={() => deleteClip.mutate(clip.id)}>
                        Remove clip
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No reference clips"
                description="Upload or record audio to make the profile usable for generation."
              />
            )}
          </SectionCard>
        </div>

        <div className="page sticky-column">
          <SectionCard title="Recent outputs" description="Latest generation jobs for this profile.">
            {profile.recent_generations.length ? (
              <div className="list">
                {profile.recent_generations.map((generation) => (
                  <div key={generation.id} className="history-row">
                    <div className="split-header">
                      <strong>{generation.input_text.slice(0, 80)}</strong>
                      <StatusBadge status={generation.status} />
                    </div>
                    <p className="muted">{formatDate(generation.created_at)}</p>
                    {generation.output_url ? <AudioPlayer src={generation.output_url} /> : null}
                    {generation.error_message ? <p className="error-text">{generation.error_message}</p> : null}
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No outputs yet"
                description="Generate speech from the main workspace to build profile history."
              />
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
