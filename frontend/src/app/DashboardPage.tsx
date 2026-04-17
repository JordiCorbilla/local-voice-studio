import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { formatDate } from "../lib/format";

export function DashboardPage() {
  const profilesQuery = useQuery({ queryKey: ["profiles"], queryFn: api.getProfiles });
  const generationsQuery = useQuery({ queryKey: ["generations"], queryFn: () => api.getGenerations() });
  const runtimeQuery = useQuery({ queryKey: ["runtime"], queryFn: api.getRuntime });

  const recentProfiles = profilesQuery.data?.slice(0, 4) ?? [];
  const recentGenerations = generationsQuery.data?.slice(0, 6) ?? [];

  return (
    <div className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">Local-first voice cloning</p>
          <h1>Build reusable voice profiles and synthesize speech without leaving your machine.</h1>
          <p className="hero-copy">
            Record directly in the browser, keep normalized references on disk, and generate XTTS outputs with a
            practical desktop workflow.
          </p>
        </div>
        <div className="hero-actions">
          <Link className="button primary" to="/generate">
            Open workspace
          </Link>
          <Link className="button subtle" to="/profiles">
            Manage profiles
          </Link>
        </div>
      </section>

      <div className="dashboard-grid">
        <SectionCard title="Runtime" description="Local engine and dependency health.">
          {runtimeQuery.data ? (
            <div className="key-value-list">
              <div>
                <span>Engine</span>
                <strong>{runtimeQuery.data.engine_name}</strong>
              </div>
              <div>
                <span>Device</span>
                <strong>{runtimeQuery.data.runtime_device}</strong>
              </div>
              <div>
                <span>Weights</span>
                <strong>{runtimeQuery.data.weights_available ? "ready" : "missing / unknown"}</strong>
              </div>
              <div>
                <span>FFmpeg</span>
                <strong>{runtimeQuery.data.ffmpeg_available ? "available" : "missing"}</strong>
              </div>
            </div>
          ) : (
            <p className="muted">Loading runtime status…</p>
          )}
        </SectionCard>

        <SectionCard title="Recent Profiles" description="Jump back into your active cloned voices.">
          {recentProfiles.length ? (
            <div className="list">
              {recentProfiles.map((profile) => (
                <Link key={profile.id} to={`/profiles/${profile.id}`} className="list-row list-link">
                  <div>
                    <strong>{profile.display_name}</strong>
                    <p className="muted">{profile.notes || "No notes yet."}</p>
                  </div>
                  <div className="row-meta">
                    <span>{profile.clip_count} clips</span>
                    <span>{profile.language_preference}</span>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState title="No profiles yet" description="Create a profile to start storing reference clips." />
          )}
        </SectionCard>

        <SectionCard title="Recent Generations" description="Latest synthesis jobs across all profiles.">
          {recentGenerations.length ? (
            <div className="list">
              {recentGenerations.map((generation) => (
                <div key={generation.id} className="list-row">
                  <div>
                    <strong>{generation.input_text.slice(0, 64)}</strong>
                    <p className="muted">{formatDate(generation.created_at)}</p>
                  </div>
                  <StatusBadge status={generation.status} />
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No generations yet" description="Generated audio will appear here once jobs complete." />
          )}
        </SectionCard>
      </div>
    </div>
  );
}
