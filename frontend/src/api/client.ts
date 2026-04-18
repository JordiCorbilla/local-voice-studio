import type {
  ApiErrorPayload,
  GenerationRecord,
  HealthStatus,
  ProfileDetail,
  ProfileSummary,
  ReferenceClip,
  RuntimeInfo,
} from "../types/api";

export type ProfileInput = {
  display_name: string;
  notes: string;
  language_preference: string;
  tags: string[];
  avatar_color: string;
  synthesis_defaults: {
    temperature: number;
    speed: number;
    length_penalty: number;
    repetition_penalty: number;
    top_k: number;
    top_p: number;
    enable_text_splitting: boolean;
  };
};

export type GenerationInput = {
  profile_id: string;
  input_text: string;
  language?: string;
  delivery_instructions?: string;
  seed?: number;
  parameters?: ProfileInput["synthesis_defaults"];
};

class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, payload: ApiErrorPayload) {
    super(payload.message);
    this.status = status;
    this.code = payload.code;
  }
}

async function request<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({
      code: "unknown_error",
      message: "Unexpected API error.",
    }))) as ApiErrorPayload | { detail?: ApiErrorPayload };
    let detail: ApiErrorPayload;
    if ("detail" in payload && payload.detail) {
      detail = payload.detail;
    } else {
      detail = payload as ApiErrorPayload;
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  getProfiles: () => request<ProfileSummary[]>("/api/profiles"),
  getProfile: (profileId: string) => request<ProfileDetail>(`/api/profiles/${profileId}`),
  createProfile: (payload: ProfileInput) =>
    request<ProfileDetail>("/api/profiles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  updateProfile: (profileId: string, payload: Partial<ProfileInput>) =>
    request<ProfileDetail>(`/api/profiles/${profileId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  deleteProfile: (profileId: string) =>
    request<void>(`/api/profiles/${profileId}`, { method: "DELETE" }),
  uploadClip: (profileId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<ReferenceClip>(`/api/profiles/${profileId}/clips/upload`, {
      method: "POST",
      body: formData,
    });
  },
  uploadRecording: (profileId: string, file: File) => {
    const formData = new FormData();
    formData.append("recording", file);
    return request<ReferenceClip>(`/api/profiles/${profileId}/clips/recording`, {
      method: "POST",
      body: formData,
    });
  },
  deleteClip: (profileId: string, clipId: string) =>
    request<void>(`/api/profiles/${profileId}/clips/${clipId}`, {
      method: "DELETE",
    }),
  setPrimaryClip: (profileId: string, clipId: string) =>
    request<ProfileDetail>(`/api/profiles/${profileId}/clips/${clipId}/set-primary`, {
      method: "POST",
    }),
  updateClipTranscript: (profileId: string, clipId: string, referenceText: string) =>
    request<ReferenceClip>(`/api/profiles/${profileId}/clips/${clipId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reference_text: referenceText }),
    }),
  transcribeClip: (profileId: string, clipId: string) =>
    request<ReferenceClip>(`/api/profiles/${profileId}/clips/${clipId}/transcribe`, {
      method: "POST",
    }),
  getGenerations: (profileId?: string) =>
    request<GenerationRecord[]>(profileId ? `/api/generations?profile_id=${profileId}` : "/api/generations"),
  createGeneration: (payload: GenerationInput) =>
    request<GenerationRecord>("/api/generations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  getGeneration: (generationId: string) => request<GenerationRecord>(`/api/generations/${generationId}`),
  deleteGeneration: (generationId: string) =>
    request<void>(`/api/generations/${generationId}`, { method: "DELETE" }),
  getRuntime: () => request<RuntimeInfo>("/api/runtime"),
  getHealth: () => request<HealthStatus>("/api/health"),
};

export { ApiError };
