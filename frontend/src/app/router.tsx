import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "./AppShell";
import { DashboardPage } from "./DashboardPage";
import { GeneratePage } from "../features/generation/GeneratePage";
import { HistoryPage } from "../features/history/HistoryPage";
import { ProfileDetailPage } from "../features/profiles/ProfileDetailPage";
import { ProfilesPage } from "../features/profiles/ProfilesPage";
import { SettingsPage } from "../features/settings/SettingsPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "profiles", element: <ProfilesPage /> },
      { path: "profiles/:profileId", element: <ProfileDetailPage /> },
      { path: "generate", element: <GeneratePage /> },
      { path: "history", element: <HistoryPage /> },
      { path: "settings", element: <SettingsPage /> },
    ],
  },
]);
