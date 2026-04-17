import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { GeneratePage } from "./GeneratePage";
import { renderWithProviders } from "../../test/render";

describe("GeneratePage", () => {
  it("polls generation status and shows output player", async () => {
    let generationPolls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input.toString();
      const method = init?.method ?? "GET";
      if (url === "/api/profiles") {
        return {
          ok: true,
          status: 200,
          json: async () => [
            {
              id: "profile-1",
              display_name: "Studio Voice",
              notes: "",
              language_preference: "en",
              tags: [],
              avatar_color: "#7dd3fc",
              synthesis_defaults: {
                temperature: 0.75,
                speed: 1,
                length_penalty: 1,
                repetition_penalty: 2,
                top_k: 50,
                top_p: 0.85,
                enable_text_splitting: true,
              },
              clip_count: 1,
              primary_clip_id: "clip-1",
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
        };
      }
      if (url === "/api/generations" && method === "POST") {
        return {
          ok: true,
          status: 202,
          json: async () => ({
            id: "gen-1",
            profile_id: "profile-1",
            input_text: "Hello",
            language: "en",
            parameters: {},
            output_file: null,
            output_url: null,
            duration_seconds: null,
            status: "queued",
            error_message: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        };
      }
      if (url === "/api/generations" && method === "GET") {
        return {
          ok: true,
          status: 200,
          json: async () => [],
        };
      }
      if (url.startsWith("/api/generations?profile_id=")) {
        return {
          ok: true,
          status: 200,
          json: async () => [],
        };
      }
      if (url === "/api/generations/gen-1") {
        generationPolls += 1;
        return {
          ok: true,
          status: 200,
          json: async () => ({
            id: "gen-1",
            profile_id: "profile-1",
            input_text: "Hello",
            language: "en",
            parameters: {},
            output_file: generationPolls > 1 ? "gen-1.wav" : null,
            output_url: generationPolls > 1 ? "/api/files/generated/gen-1.wav" : null,
            duration_seconds: generationPolls > 1 ? 1 : null,
            status: generationPolls > 1 ? "completed" : "running",
            error_message: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        };
      }
      return {
        ok: false,
        status: 404,
        json: async () => ({ detail: { code: "not_found", message: `Unhandled mock for ${url}` } }),
      };
    });

    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<GeneratePage />);

    await screen.findByRole("heading", { name: "Generate" });
    fireEvent.change(screen.getByLabelText(/text/i), { target: { value: "Hello" } });
    fireEvent.click(screen.getByRole("button", { name: /generate audio/i }));

    await waitFor(() => expect(screen.getByText(/download wav/i)).toBeInTheDocument(), { timeout: 4000 });
  });
});
