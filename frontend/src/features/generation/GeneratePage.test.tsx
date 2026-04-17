import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { GeneratePage } from "./GeneratePage";
import { renderWithProviders } from "../../test/render";

describe("GeneratePage", () => {
  it("polls generation status and shows output player", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
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
      })
      .mockResolvedValueOnce({
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
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => [],
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          id: "gen-1",
          profile_id: "profile-1",
          input_text: "Hello",
          language: "en",
          parameters: {},
          output_file: "gen-1.wav",
          output_url: "/api/files/generated/gen-1.wav",
          duration_seconds: 1,
          status: "completed",
          error_message: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });

    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<GeneratePage />);

    await screen.findByRole("heading", { name: "Generate" });
    fireEvent.change(screen.getByLabelText(/text/i), { target: { value: "Hello" } });
    fireEvent.click(screen.getByRole("button", { name: /generate audio/i }));

    await waitFor(() => expect(screen.getByText(/download wav/i)).toBeInTheDocument());
  });
});
