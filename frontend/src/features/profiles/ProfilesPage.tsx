import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { EmptyState } from "../../components/EmptyState";
import { SectionCard } from "../../components/SectionCard";
import { initials } from "../../lib/format";
import { ProfileForm, type ProfileFormValues } from "./ProfileForm";

function toPayload(values: ProfileFormValues) {
  return {
    ...values,
    tags: values.tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
  };
}

export function ProfilesPage() {
  const queryClient = useQueryClient();
  const profilesQuery = useQuery({ queryKey: ["profiles"], queryFn: api.getProfiles });
  const createProfile = useMutation({
    mutationFn: (values: ProfileFormValues) => api.createProfile(toPayload(values)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["profiles"] }),
  });

  return (
    <div className="page">
      <div className="page-header">
        <h1>Profiles</h1>
        <p className="muted">Store reusable cloned voices with reference clips, notes, and sensible defaults.</p>
      </div>
      <div className="two-column">
        <SectionCard title="Create profile" description="Start a new reusable voice profile.">
          <ProfileForm submitLabel="Create profile" onSubmit={(values) => createProfile.mutateAsync(values)} />
        </SectionCard>
        <SectionCard title="Saved voices" description="Recent profiles on this machine.">
          {profilesQuery.data?.length ? (
            <div className="card-grid">
              {profilesQuery.data.map((profile) => (
                <article key={profile.id} className="profile-card">
                  <div className="profile-header">
                    <div className="brand-block">
                      <div className="profile-mark" style={{ backgroundColor: profile.avatar_color }}>
                        {initials(profile.display_name)}
                      </div>
                      <div>
                        <strong>{profile.display_name}</strong>
                        <p className="muted">{profile.notes || "No notes yet."}</p>
                      </div>
                    </div>
                  </div>
                  <div className="pill-row">
                    <span className="pill">{profile.language_preference}</span>
                    <span className="pill">{profile.clip_count} clips</span>
                    {profile.tags.map((tag) => (
                      <span key={tag} className="pill">
                        {tag}
                      </span>
                    ))}
                  </div>
                  <Link className="button primary" to={`/profiles/${profile.id}`}>
                    Open profile
                  </Link>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState title="No profiles yet" description="Create your first profile to add uploaded or recorded reference audio." />
          )}
        </SectionCard>
      </div>
    </div>
  );
}
