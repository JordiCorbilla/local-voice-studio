export type ProfileDefaults = {
  temperature: number;
  speed: number;
  length_penalty: number;
  repetition_penalty: number;
  top_k: number;
  top_p: number;
  enable_text_splitting: boolean;
};

export type ReferenceClip = {
  id: string;
  profile_id: string;
  original_filename: string;
  mime_type: string;
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  is_primary: boolean;
  created_at: string;
  original_file: string;
  normalized_file: string;
  audio_url: string;
};

export type GenerationRecord = {
  id: string;
  profile_id: string;
  input_text: string;
  language: string;
  parameters: ProfileDefaults;
  output_file: string | null;
  output_url: string | null;
  duration_seconds: number | null;
  status: "queued" | "running" | "completed" | "failed";
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type ProfileSummary = {
  id: string;
  display_name: string;
  notes: string;
  language_preference: string;
  tags: string[];
  avatar_color: string;
  synthesis_defaults: ProfileDefaults;
  clip_count: number;
  primary_clip_id: string | null;
  created_at: string;
  updated_at: string;
};

export type ProfileDetail = ProfileSummary & {
  clips: ReferenceClip[];
  recent_generations: GenerationRecord[];
};

export type RuntimeInfo = {
  model_name: string;
  engine_name: string;
  engine_ready: boolean;
  model_loaded: boolean;
  weights_available: boolean;
  runtime_device: string;
  gpu_detected: boolean;
  gpu_name: string | null;
  python_version: string;
  torch_version: string | null;
  tts_package_installed: boolean;
  ffmpeg_available: boolean;
  ffprobe_available: boolean;
  directories: Record<string, string>;
  last_error: string | null;
  extras: Record<string, unknown>;
};

export type HealthStatus = {
  status: string;
  database: string;
  ffmpeg_available: boolean;
  engine_ready: boolean;
};

export type ApiErrorPayload = {
  code: string;
  message: string;
};
