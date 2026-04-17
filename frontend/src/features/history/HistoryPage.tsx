import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../../api/client";
import { AudioPlayer } from "../../components/AudioPlayer";
import { EmptyState } from "../../components/EmptyState";
import { SectionCard } from "../../components/SectionCard";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDate, formatDuration } from "../../lib/format";

export function HistoryPage() {
  const queryClient = useQueryClient();
  const [profileId, setProfileId] = useState("");
  const profilesQuery = useQuery({ queryKey: ["profiles"], queryFn: api.getProfiles });
  const generationsQuery = useQuery({
    queryKey: ["history", profileId],
    queryFn: () => api.getGenerations(profileId || undefined),
  });
  const deleteGeneration = useMutation({
    mutationFn: (generationId: string) => api.deleteGeneration(generationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["history", profileId] });
      queryClient.invalidateQueries({ queryKey: ["generations"] });
    },
  });

  return (
    <div className="page">
      <div className="page-header">
        <h1>History</h1>
        <p className="muted">Replay, download, and prune generated local outputs.</p>
      </div>
      <SectionCard
        title="Generated outputs"
        description="Filter by profile and manage completed synthesis jobs."
        aside={
          <select value={profileId} onChange={(event) => setProfileId(event.target.value)}>
            <option value="">All profiles</option>
            {profilesQuery.data?.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.display_name}
              </option>
            ))}
          </select>
        }
      >
        {generationsQuery.data?.length ? (
          <div className="list">
            {generationsQuery.data.map((generation) => (
              <div key={generation.id} className="history-row">
                <div className="split-header">
                  <div>
                    <strong>{generation.input_text}</strong>
                    <p className="muted">
                      {formatDate(generation.created_at)} · {formatDuration(generation.duration_seconds)}
                    </p>
                  </div>
                  <StatusBadge status={generation.status} />
                </div>
                {generation.output_url ? <AudioPlayer src={generation.output_url} /> : null}
                <div className="button-row">
                  {generation.output_url ? (
                    <a className="button subtle" href={generation.output_url} download>
                      Download
                    </a>
                  ) : null}
                  <button className="button danger" type="button" onClick={() => deleteGeneration.mutate(generation.id)}>
                    Delete
                  </button>
                </div>
                {generation.error_message ? <p className="error-text">{generation.error_message}</p> : null}
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="No outputs stored" description="Generate speech to build a replayable local history." />
        )}
      </SectionCard>
    </div>
  );
}
