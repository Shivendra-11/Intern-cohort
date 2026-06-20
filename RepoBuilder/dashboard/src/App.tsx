import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { Layout } from "./components/Layout";
import { RepoProvider } from "./context/RepoContext";
import { ThemeProvider } from "./context/ThemeContext";
import { GraphsPage } from "./pages/GraphsPage";
import { ArchitecturePage } from "./pages/ArchitecturePage";
import { InventoryPage } from "./pages/InventoryPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { RoutesPage } from "./pages/RoutesPage";
import { TestsPage } from "./pages/TestsPage";

function AppRoutes() {
  const { pathname } = useLocation();

  return (
    <Layout pathname={pathname}>
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        <Route path="/routes" element={<RoutesPage />} />
        <Route path="/tests" element={<TestsPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/graphs" element={<GraphsPage />} />
        <Route path="/architecture" element={<ArchitecturePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <RepoProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </RepoProvider>
    </ThemeProvider>
  );
}
