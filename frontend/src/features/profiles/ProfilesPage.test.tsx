import { fireEvent, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { ProfilesPage } from "./ProfilesPage";
import { renderWithProviders } from "../../test/render";

describe("ProfilesPage", () => {
  it("validates profile creation form", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => [],
      }),
    );

    renderWithProviders(<ProfilesPage />);

    fireEvent.click(screen.getByRole("button", { name: /create profile/i }));
    expect(await screen.findByText(/display name is required/i)).toBeInTheDocument();
  });
});
