import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api, type GenerationInput } from "../../api/client";
import { AudioPlayer } from "../../components/AudioPlayer";
import { EmptyState } from "../../components/EmptyState";
import { SectionCard } from "../../components/SectionCard";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDate } from "../../lib/format";
import type { ProfileDefaults } from "../../types/api";

const similarityPreset: ProfileDefaults = {
  temperature: 0.55,
  speed: 1,
  length_penalty: 1,
  repetition_penalty: 2.2,
  top_k: 40,
  top_p: 0.75,
  enable_text_splitting: true,
};

const recommendedTestText =
  "This is a short similarity test. I speak calmly, clearly, and at a natural pace.";

export function GeneratePage() {
  const queryClient = useQueryClient();
  const profilesQuery = useQuery({ queryKey: ["profiles"], queryFn: api.getProfiles });
  const [profileId, setProfileId] = useState("");
  const [language, setLanguage] = useState("en");
  const [inputText, setInputText] = useState("");
  const [deliveryInstructions, setDeliveryInstructions] = useState("");
  const [seed, setSeed] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [parameters, setParameters] = useState<ProfileDefaults>(similarityPreset);
  const [activeGenerationId, setActiveGenerationId] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!profileId && profilesQuery.data?.length) {
      const firstProfile = profilesQuery.data[0];
      setProfileId(firstProfile.id);
      setLanguage(firstProfile.language_preference);
      setParameters(firstProfile.synthesis_defaults);
    }
  }, [profileId, profilesQuery.data]);

  const generationQuery = useQuery({
    queryKey: ["generation", activeGenerationId],
    queryFn: () => api.getGeneration(activeGenerationId!),
    enabled: Boolean(activeGenerationId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "queued" || status === "running") {
        return 2000;
      }
      return false;
    },
  });

  useEffect(() => {
    const status = generationQuery.data?.status;
    if (status === "completed" || status === "failed") {
      queryClient.invalidateQueries({ queryKey: ["generations"] });
      if (profileId) {
        queryClient.invalidateQueries({ queryKey: ["profile", profileId] });
      }
    }
  }, [generationQuery.data?.status, profileId, queryClient]);

  const createGeneration = useMutation({
    mutationFn: (payload: GenerationInput) => api.createGeneration(payload),
    onSuccess: (generation) => {
      setActiveGenerationId(generation.id);
      setError("");
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : "Unable to start generation.");
    },
  });

  const historyQuery = useQuery({
    queryKey: ["generations", profileId],
    queryFn: () => api.getGenerations(profileId || undefined),
  });
  const selectedProfileQuery = useQuery({
    queryKey: ["profile", profileId],
    queryFn: () => api.getProfile(profileId),
    enabled: Boolean(profileId),
  });
  const primaryClip = selectedProfileQuery.data?.clips.find((clip) => clip.is_primary);
  const primaryTranscriptMissing = Boolean(selectedProfileQuery.data && !primaryClip?.reference_text?.trim());
  const activeStatus = generationQuery.data?.status;
  const generationRunning = createGeneration.isPending || activeStatus === "queued" || activeStatus === "running";

  return (
    <div className="page">
      <div className="page-header">
        <h1>Generate</h1>
        <p className="muted">Choose a saved voice profile, enter text, and run local synthesis jobs with XTTS parameters.</p>
      </div>

      <div className="workspace-grid">
        <SectionCard title="Generation workspace" description="Focused text-to-speech workspace.">
          <div className="form-grid">
            <div className="guidance-card">
              <div className="split-header">
                <div>
                  <strong>Start with a similarity check</strong>
                  <p className="muted">Use one strong primary clip and a short sentence before testing longer text.</p>
                </div>
                <div className="inline-actions">
                  <button className="button subtle" type="button" onClick={() => setParameters(similarityPreset)}>
                    Use similarity preset
                  </button>
                  <button className="button subtle" type="button" onClick={() => setInputText(recommendedTestText)}>
                    Load test text
                  </button>
                </div>
              </div>
              <p className="muted">
                Recommended text: <span className="guidance-text">{recommendedTestText}</span>
              </p>
              {primaryTranscriptMissing ? (
                <p className="error-text">
                  The selected primary reference clip has no saved transcript. Qwen3-TTS requires the exact words spoken
                  in that clip before generation.
                </p>
              ) : null}
            </div>
            <div className="form-grid two">
              <div className="field">
                <label htmlFor="profile">Voice profile</label>
                <select
                  id="profile"
                  value={profileId}
                  onChange={(event) => {
                    const nextId = event.target.value;
                    setProfileId(nextId);
                    const nextProfile = profilesQuery.data?.find((profile) => profile.id === nextId);
                    if (nextProfile) {
                      setLanguage(nextProfile.language_preference);
                      setParameters(nextProfile.synthesis_defaults);
                    }
                  }}
                >
                  <option value="">Select a profile</option>
                  {profilesQuery.data?.map((profile) => (
                    <option key={profile.id} value={profile.id}>
                      {profile.display_name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="language">Output language</label>
                <input id="language" value={language} onChange={(event) => setLanguage(event.target.value)} />
              </div>
            </div>
            <div className="field">
              <label htmlFor="input_text">Text</label>
              <textarea
                id="input_text"
                value={inputText}
                onChange={(event) => setInputText(event.target.value)}
                placeholder="Enter the text you want synthesized..."
              />
            </div>
            <div className="field">
              <label htmlFor="delivery_instructions">Delivery instructions</label>
              <textarea
                id="delivery_instructions"
                value={deliveryInstructions}
                onChange={(event) => setDeliveryInstructions(event.target.value)}
                placeholder="Optional. Calm, warm, measured, lightly emphatic..."
              />
              <p className="help">Used by engines that support instruction-style delivery control.</p>
            </div>
            <div className="button-row">
              <button className="button subtle" type="button" onClick={() => setShowAdvanced((current) => !current)}>
                {showAdvanced ? "Hide advanced" : "Show advanced"}
              </button>
              <button
                className="button primary"
                type="button"
                disabled={generationRunning || !profileId || primaryTranscriptMissing}
                onClick={() =>
                  createGeneration.mutate({
                    profile_id: profileId,
                    input_text: inputText,
                    language,
                    delivery_instructions: deliveryInstructions || undefined,
                    seed: seed.trim() ? Number(seed) : undefined,
                    parameters,
                  })
                }
              >
                {generationRunning ? (
                  <>
                    <span className="spinner" aria-hidden="true" />
                    Generating...
                  </>
                ) : (
                  "Generate audio"
                )}
              </button>
            </div>
            {showAdvanced ? (
              <div className="advanced-grid">
                <div className="form-grid two">
                  <div className="field">
                    <label htmlFor="temperature">Temperature</label>
                    <input
                      id="temperature"
                      type="number"
                      step="0.05"
                      value={parameters.temperature}
                      onChange={(event) =>
                        setParameters((current) => ({ ...current, temperature: Number(event.target.value) }))
                      }
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="speed">Speed</label>
                    <input
                      id="speed"
                      type="number"
                      step="0.05"
                      value={parameters.speed}
                      onChange={(event) => setParameters((current) => ({ ...current, speed: Number(event.target.value) }))}
                    />
                  </div>
                </div>
                <div className="form-grid two">
                  <div className="field">
                    <label htmlFor="repetition_penalty">Repetition penalty</label>
                    <input
                      id="repetition_penalty"
                      type="number"
                      step="0.1"
                      value={parameters.repetition_penalty}
                      onChange={(event) =>
                        setParameters((current) => ({ ...current, repetition_penalty: Number(event.target.value) }))
                      }
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="top_p">Top P</label>
                    <input
                      id="top_p"
                      type="number"
                      step="0.05"
                      value={parameters.top_p}
                      onChange={(event) => setParameters((current) => ({ ...current, top_p: Number(event.target.value) }))}
                    />
                  </div>
                </div>
                <div className="form-grid two">
                  <div className="field">
                    <label htmlFor="seed">Seed</label>
                    <input
                      id="seed"
                      type="number"
                      value={seed}
                      onChange={(event) => setSeed(event.target.value)}
                      placeholder="Optional"
                    />
                  </div>
                </div>
              </div>
            ) : null}
            {error ? <p className="error-text">{error}</p> : null}
          </div>
        </SectionCard>

        <div className="page sticky-column">
          <SectionCard title="Active job" description="Current synthesis state with preview on completion.">
            {generationQuery.data ? (
              <div className="form-grid">
                <div className="split-header">
                  <strong>{generationQuery.data.input_text.slice(0, 80)}</strong>
                  <StatusBadge status={generationQuery.data.status} />
                </div>
                <p className="muted">
                  {generationQuery.data.engine_name} | {formatDate(generationQuery.data.created_at)}
                </p>
                {generationQuery.data.delivery_instructions ? (
                  <p className="muted">Delivery: {generationQuery.data.delivery_instructions}</p>
                ) : null}
                {generationQuery.data.output_url ? (
                  <>
                    <AudioPlayer src={generationQuery.data.output_url} />
                    <a className="button subtle" href={generationQuery.data.output_url} download>
                      Download WAV
                    </a>
                  </>
                ) : (
                  <div className="job-progress">
                    {generationRunning ? <span className="spinner" aria-hidden="true" /> : null}
                    <span>Waiting for synthesized audio...</span>
                  </div>
                )}
                {generationQuery.data.error_message ? <p className="error-text">{generationQuery.data.error_message}</p> : null}
              </div>
            ) : (
              <EmptyState title="No active job" description="Start a generation to preview job progress here." />
            )}
          </SectionCard>

          <SectionCard title="History" description="Recent jobs for the selected profile.">
            {historyQuery.data?.length ? (
              <div className="list">
                {historyQuery.data.slice(0, 8).map((generation) => (
                  <div key={generation.id} className="history-row">
                    <div className="split-header">
                      <strong>{generation.input_text.slice(0, 64)}</strong>
                      <StatusBadge status={generation.status} />
                    </div>
                    <p className="muted">{generation.engine_name}</p>
                    {generation.output_url ? <AudioPlayer src={generation.output_url} /> : null}
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No history yet" description="Generated outputs for the selected profile will collect here." />
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
