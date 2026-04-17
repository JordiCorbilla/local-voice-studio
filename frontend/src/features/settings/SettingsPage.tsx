import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { SectionCard } from "../../components/SectionCard";

export function SettingsPage() {
  const runtimeQuery = useQuery({ queryKey: ["runtime"], queryFn: api.getRuntime });
  const healthQuery = useQuery({ queryKey: ["health"], queryFn: api.getHealth });

  return (
    <div className="page">
      <div className="page-header">
        <h1>Settings & diagnostics</h1>
        <p className="muted">Inspect the local runtime, model availability, and active data directories.</p>
      </div>
      <div className="two-column">
        <SectionCard title="Runtime" description="Current backend and XTTS runtime state.">
          {runtimeQuery.data ? (
            <div className="key-value-list">
              <div>
                <span>Model</span>
                <strong>{runtimeQuery.data.model_name}</strong>
              </div>
              <div>
                <span>Device</span>
                <strong>{runtimeQuery.data.runtime_device}</strong>
              </div>
              <div>
                <span>GPU</span>
                <strong>{runtimeQuery.data.gpu_name ?? "Not detected"}</strong>
              </div>
              <div>
                <span>TTS package</span>
                <strong>{runtimeQuery.data.tts_package_installed ? "installed" : "missing"}</strong>
              </div>
              <div>
                <span>Weights</span>
                <strong>{runtimeQuery.data.weights_available ? "available" : "missing / unknown"}</strong>
              </div>
              <div>
                <span>FFmpeg</span>
                <strong>{runtimeQuery.data.ffmpeg_available ? "available" : "missing"}</strong>
              </div>
            </div>
          ) : (
            <p className="muted">Loading runtime info…</p>
          )}
        </SectionCard>

        <SectionCard title="Health" description="Simple local readiness checks.">
          {healthQuery.data ? (
            <div className="key-value-list">
              <div>
                <span>Status</span>
                <strong>{healthQuery.data.status}</strong>
              </div>
              <div>
                <span>Database</span>
                <strong>{healthQuery.data.database}</strong>
              </div>
              <div>
                <span>FFmpeg</span>
                <strong>{healthQuery.data.ffmpeg_available ? "ok" : "missing"}</strong>
              </div>
              <div>
                <span>Engine ready</span>
                <strong>{healthQuery.data.engine_ready ? "yes" : "not yet"}</strong>
              </div>
            </div>
          ) : (
            <p className="muted">Loading health checks…</p>
          )}
        </SectionCard>
      </div>
      <SectionCard title="Directories" description="Where the app stores local state on disk.">
        {runtimeQuery.data ? (
          <div className="list">
            {Object.entries(runtimeQuery.data.directories).map(([key, value]) => (
              <div key={key} className="list-row">
                <strong>{key}</strong>
                <span className="muted">{value}</span>
              </div>
            ))}
          </div>
        ) : null}
      </SectionCard>
    </div>
  );
}
