import { useState } from "react";
import type { ProfileDefaults, ProfileSummary } from "../../types/api";

export type ProfileFormValues = {
  display_name: string;
  notes: string;
  language_preference: string;
  tags: string;
  avatar_color: string;
  synthesis_defaults: ProfileDefaults;
};

const defaultValues: ProfileFormValues = {
  display_name: "",
  notes: "",
  language_preference: "en",
  tags: "",
  avatar_color: "#7dd3fc",
  synthesis_defaults: {
    temperature: 0.55,
    speed: 1,
    length_penalty: 1,
    repetition_penalty: 2.2,
    top_k: 40,
    top_p: 0.75,
    enable_text_splitting: true,
  },
};

type Props = {
  initialProfile?: ProfileSummary;
  onSubmit: (values: ProfileFormValues) => Promise<void>;
  submitLabel: string;
};

export function ProfileForm({ initialProfile, onSubmit, submitLabel }: Props) {
  const [values, setValues] = useState<ProfileFormValues>(
    initialProfile
      ? {
          display_name: initialProfile.display_name,
          notes: initialProfile.notes,
          language_preference: initialProfile.language_preference,
          tags: initialProfile.tags.join(", "),
          avatar_color: initialProfile.avatar_color,
          synthesis_defaults: initialProfile.synthesis_defaults,
        }
      : defaultValues,
  );
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const update = <K extends keyof ProfileFormValues>(key: K, next: ProfileFormValues[K]) => {
    setValues((current) => ({ ...current, [key]: next }));
  };

  const updateDefaults = (key: keyof ProfileDefaults, next: string | number | boolean) => {
    setValues((current) => ({
      ...current,
      synthesis_defaults: {
        ...current.synthesis_defaults,
        [key]: next,
      },
    }));
  };

  return (
    <form
      className="form-grid"
      onSubmit={async (event) => {
        event.preventDefault();
        if (!values.display_name.trim()) {
          setError("Display name is required.");
          return;
        }
        setError("");
        setSaving(true);
        try {
          await onSubmit(values);
          if (!initialProfile) {
            setValues(defaultValues);
          }
        } catch (submissionError) {
          setError(submissionError instanceof Error ? submissionError.message : "Unable to save profile.");
        } finally {
          setSaving(false);
        }
      }}
    >
      <div className="form-grid two">
        <div className="field">
          <label htmlFor="display_name">Display name</label>
          <input
            id="display_name"
            value={values.display_name}
            onChange={(event) => update("display_name", event.target.value)}
            placeholder="Studio narration"
          />
        </div>
        <div className="field">
          <label htmlFor="language_preference">Language</label>
          <input
            id="language_preference"
            value={values.language_preference}
            onChange={(event) => update("language_preference", event.target.value)}
            placeholder="en"
          />
        </div>
      </div>
      <div className="form-grid two">
        <div className="field">
          <label htmlFor="avatar_color">Avatar color</label>
          <input
            id="avatar_color"
            value={values.avatar_color}
            onChange={(event) => update("avatar_color", event.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="tags">Tags</label>
          <input
            id="tags"
            value={values.tags}
            onChange={(event) => update("tags", event.target.value)}
            placeholder="warm, narration, demo"
          />
        </div>
      </div>
      <div className="field">
        <label htmlFor="notes">Notes</label>
        <textarea
          id="notes"
          value={values.notes}
          onChange={(event) => update("notes", event.target.value)}
          placeholder="Reference source, tone notes, pronunciation quirks..."
        />
      </div>
      <details>
        <summary>Profile defaults</summary>
        <div className="advanced-grid">
          <div className="form-grid two">
            <div className="field">
              <label htmlFor="temperature">Temperature</label>
              <input
                id="temperature"
                type="number"
                step="0.05"
                value={values.synthesis_defaults.temperature}
                onChange={(event) => updateDefaults("temperature", Number(event.target.value))}
              />
            </div>
            <div className="field">
              <label htmlFor="speed">Speed</label>
              <input
                id="speed"
                type="number"
                step="0.05"
                value={values.synthesis_defaults.speed}
                onChange={(event) => updateDefaults("speed", Number(event.target.value))}
              />
            </div>
          </div>
          <div className="form-grid two">
            <div className="field">
              <label htmlFor="top_k">Top K</label>
              <input
                id="top_k"
                type="number"
                value={values.synthesis_defaults.top_k}
                onChange={(event) => updateDefaults("top_k", Number(event.target.value))}
              />
            </div>
            <div className="field">
              <label htmlFor="top_p">Top P</label>
              <input
                id="top_p"
                type="number"
                step="0.05"
                value={values.synthesis_defaults.top_p}
                onChange={(event) => updateDefaults("top_p", Number(event.target.value))}
              />
            </div>
          </div>
        </div>
      </details>
      {error ? <p className="error-text">{error}</p> : null}
      <div className="button-row">
        <button className="button primary" type="submit" disabled={saving}>
          {saving ? "Saving..." : submitLabel}
        </button>
      </div>
    </form>
  );
}
