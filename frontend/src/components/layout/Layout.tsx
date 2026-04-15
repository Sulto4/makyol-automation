import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useTheme } from '../../hooks/useTheme';

export default function Layout() {
  useTheme();

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
