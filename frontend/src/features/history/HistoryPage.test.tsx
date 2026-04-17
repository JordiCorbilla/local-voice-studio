import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { HistoryPage } from "./HistoryPage";
import { renderWithProviders } from "../../test/render";

describe("HistoryPage", () => {
  it("renders stored outputs and deletes one", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => [],
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => [
          {
            id: "gen-1",
            profile_id: "profile-1",
            input_text: "Hello world",
            language: "en",
            parameters: {},
            output_file: "gen-1.wav",
            output_url: "/api/files/generated/gen-1.wav",
            duration_seconds: 1,
            status: "completed",
            error_message: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => undefined,
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => [
          {
            id: "gen-1",
            profile_id: "profile-1",
            input_text: "Hello world",
            language: "en",
            parameters: {},
            output_file: "gen-1.wav",
            output_url: "/api/files/generated/gen-1.wav",
            duration_seconds: 1,
            status: "completed",
            error_message: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => [
          {
            id: "gen-1",
            profile_id: "profile-1",
            input_text: "Hello world",
            language: "en",
            parameters: {},
            output_file: "gen-1.wav",
            output_url: "/api/files/generated/gen-1.wav",
            duration_seconds: 1,
            status: "completed",
            error_message: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
      });

    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<HistoryPage />);

    expect(await screen.findByText(/hello world/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /delete/i }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/generations/gen-1", { method: "DELETE" }));
  });
});
