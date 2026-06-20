import { SessionProvider } from "@/stores/sessionStore";
import { AppLayout } from "@/layouts/AppLayout";
import { A1Page } from "@/pages/agents/A1Page";
import { A2Page } from "@/pages/agents/A2Page";
import { A3Page } from "@/pages/agents/A3Page";
import { A4Page } from "@/pages/agents/A4Page";
import { A5Page } from "@/pages/agents/A5Page";
import { A6Page } from "@/pages/agents/A6Page";
import { OverviewPage } from "@/pages/OverviewPage";
import { PlaceholderPage } from "@/pages/PlaceholderPage";
import { RunsPage } from "@/pages/RunsPage";
import { createBrowserRouter } from "react-router-dom";

export const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <SessionProvider>
        <AppLayout />
      </SessionProvider>
    ),
    children: [
      { index: true, element: <OverviewPage /> },
      { path: "runs", element: <RunsPage /> },
      { path: "agents/A1", element: <A1Page /> },
      { path: "agents/A2", element: <A2Page /> },
      { path: "agents/A3", element: <A3Page /> },
      { path: "agents/A4", element: <A4Page /> },
      { path: "agents/A5", element: <A5Page /> },
      { path: "agents/A6", element: <A6Page /> },
      {
        path: "logs",
        element: (
          <PlaceholderPage
            title="Logs"
            description="Combined log stream coming next."
          />
        ),
      },
      {
        path: "settings",
        element: (
          <PlaceholderPage
            title="Settings"
            description="Theme and poll interval preferences coming next."
          />
        ),
      },
    ],
  },
]);
