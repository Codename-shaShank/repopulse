import { NavLink, Route, Routes } from "react-router-dom";

import { AnalyticsHelpPage } from "./pages/AnalyticsHelpPage";
import { DashboardPage } from "./pages/DashboardPage";
import { RepositoryDetailPage } from "./pages/RepositoryDetailPage";

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>RepoPulse</h1>
        <nav>
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/analytics">Analytics</NavLink>
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route
            path="/repositories/:repositoryId"
            element={<RepositoryDetailPage />}
          />
          <Route path="/analytics" element={<AnalyticsHelpPage />} />
          <Route path="*" element={<p>That page does not exist.</p>} />
        </Routes>
      </main>
    </div>
  );
}
