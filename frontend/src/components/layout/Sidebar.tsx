import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, Upload, AlertTriangle, Settings, Moon, Sun } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

const navItems = [
  { to: '/', label: 'Panou de Control', icon: LayoutDashboard },
  { to: '/documents', label: 'Documente', icon: FileText },
  { to: '/upload', label: 'Încărcare', icon: Upload },
  { to: '/alerts', label: 'Alerte', icon: AlertTriangle },
  { to: '/settings', label: 'Setări', icon: Settings },
];

export default function Sidebar() {
  const { resolvedTheme, setMode } = useTheme();
  const isDark = resolvedTheme === 'dark';

  const toggleTheme = () => {
    setMode(isDark ? 'light' : 'dark');
  };

  return (
    <aside className="w-[200px] min-w-[200px] bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h1 className="text-xl font-bold text-gray-800 dark:text-gray-100">Makyol</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">Automatizare Documente</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={toggleTheme}
          className="flex items-center gap-3 px-3 py-2 w-full rounded-lg text-sm font-medium transition-colors text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
        >
          {isDark ? <Sun size={18} /> : <Moon size={18} />}
          {isDark ? 'Mod Luminos' : 'Mod Întunecat'}
        </button>
      </div>
    </aside>
  );
}
