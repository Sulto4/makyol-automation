import { useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardPage from './pages/DashboardPage';
import DocumentsPage from './pages/DocumentsPage';
import DocumentDetailPage from './pages/DocumentDetailPage';
import UploadPage from './pages/UploadPage';
import AlertsPage from './pages/AlertsPage';
import SettingsPage from './pages/SettingsPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import AdminUsersPage from './pages/AdminUsersPage';
import { useAuthStore } from './store/authStore';

const REGISTER_ENABLED = import.meta.env.VITE_REGISTER_ENABLED === 'true';

export default function App() {
  const refreshUser = useAuthStore((s) => s.refreshUser);
  const token = useAuthStore((s) => s.token);

  useEffect(() => {
    if (token) {
      void refreshUser();
    }
    // Only re-run when the persisted token changes
  }, [token, refreshUser]);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      {REGISTER_ENABLED && <Route path="/register" element={<RegisterPage />} />}

      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/documents/:id" element={<DocumentDetailPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute adminOnly />}>
        <Route element={<Layout />}>
          <Route path="/admin/users" element={<AdminUsersPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
