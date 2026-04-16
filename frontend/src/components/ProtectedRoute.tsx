import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

// Dev bypass: set VITE_AUTH_DISABLED=true in frontend/.env.local to skip the login wall.
const AUTH_DISABLED = import.meta.env.VITE_AUTH_DISABLED === 'true';

export default function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const location = useLocation();

  if (AUTH_DISABLED) return <Outlet />;

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <Outlet />;
}
