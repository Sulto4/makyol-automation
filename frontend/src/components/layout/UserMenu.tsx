import { useNavigate } from 'react-router-dom';
import { LogOut, ShieldCheck } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

export default function UserMenu() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  if (!user) return null;

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="px-3 py-2 space-y-2 text-sm">
      <div className="flex items-center gap-2 text-gray-700 dark:text-gray-200">
        {user.is_admin && (
          <ShieldCheck size={14} className="text-blue-600 dark:text-blue-400" aria-label="Admin" />
        )}
        <span className="truncate" title={user.email}>
          {user.email}
        </span>
      </div>
      <button
        onClick={handleLogout}
        className="flex items-center gap-2 w-full px-2 py-1.5 rounded-md text-sm font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
      >
        <LogOut size={16} />
        Ieșire din cont
      </button>
    </div>
  );
}
