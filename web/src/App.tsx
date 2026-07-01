import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./lib/auth";
import Layout from "./components/Layout";
import { Spinner } from "./components/ui";
import LoginPage from "./pages/LoginPage";
import DirectoryPage from "./pages/DirectoryPage";
import ProfilePage from "./pages/ProfilePage";
import OrgChartPage from "./pages/OrgChartPage";
import LeavePage from "./pages/LeavePage";
import ApprovalsPage from "./pages/ApprovalsPage";
import AgentPage from "./pages/AgentPage";
import type { RBACRole } from "./lib/types";

function Protected({ children, minRole }: { children: JSX.Element; minRole?: RBACRole }) {
  const { me, loading, hasRole } = useAuth();
  if (loading)
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg">
        <Spinner label="starting session…" />
      </div>
    );
  if (!me) return <Navigate to="/login" replace />;
  if (minRole && !hasRole(minRole)) return <Navigate to="/directory" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <Protected>
            <Layout />
          </Protected>
        }
      >
        <Route path="/directory" element={<DirectoryPage />} />
        <Route path="/directory/:id" element={<ProfilePage />} />
        <Route path="/org-chart" element={<OrgChartPage />} />
        <Route path="/leave" element={<LeavePage />} />
        <Route
          path="/approvals"
          element={
            <Protected minRole="manager">
              <ApprovalsPage />
            </Protected>
          }
        />
        <Route path="/agent" element={<AgentPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/directory" replace />} />
    </Routes>
  );
}
