import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { api } from "../../api/client";
import { AudioPlayer } from "../../components/AudioPlayer";
import { EmptyState } from "../../components/EmptyState";
import { SectionCard } from "../../components/SectionCard";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDate, formatDuration } from "../../lib/format";
import { ProfileForm, type ProfileFormValues } from "./ProfileForm";
import { RecorderPanel } from "./RecorderPanel";

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

  if (!profileQuery.data) {
    return <div className="page"><p className="muted">Loading profile...</p></div>;
  }

  const profile = profileQuery.data;

  return (
    <div className="page">
      <div className="page-header">
        <h1>{profile.display_name}</h1>
        <p className="muted">Manage reference clips, update defaults, and test the profile’s recent generations.</p>
      </div>

      <div className="profile-grid">
        <div className="page">
          <SectionCard title="Profile settings" description="Edit the metadata and synthesis defaults for this voice.">
            <ProfileForm
              initialProfile={profile}
              submitLabel="Save changes"
              onSubmit={(values) => updateProfile.mutateAsync(values)}
            />
          </SectionCard>

          <SectionCard title="Reference clips" description="Upload normalized voice references or record a new one.">
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
            <RecorderPanel onSave={(file) => uploadRecording.mutateAsync(file)} />
            {profile.clips.length ? (
              <div className="list">
                {profile.clips.map((clip) => (
                  <div key={clip.id} className="clip-row">
                    <div className="split-header">
                      <div>
                        <strong>{clip.original_filename}</strong>
                        <p className="muted">
                          {formatDuration(clip.duration_seconds)} · {clip.sample_rate} Hz · {formatDate(clip.created_at)}
                        </p>
                      </div>
                      {clip.is_primary ? <span className="pill">Primary</span> : null}
                    </div>
                    <AudioPlayer src={clip.audio_url} />
                    <div className="button-row">
                      {!clip.is_primary ? (
                        <button className="button subtle" type="button" onClick={() => setPrimary.mutate(clip.id)}>
                          Set primary
                        </button>
                      ) : null}
                      <button className="button danger" type="button" onClick={() => deleteClip.mutate(clip.id)}>
                        Remove clip
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No reference clips" description="Upload or record audio to make the profile usable for generation." />
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
              <EmptyState title="No outputs yet" description="Generate speech from the main workspace to build profile history." />
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
