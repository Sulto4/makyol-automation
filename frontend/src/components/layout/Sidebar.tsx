import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, Upload, AlertTriangle } from 'lucide-react';

const navItems = [
  { to: '/', label: 'Panou de Control', icon: LayoutDashboard },
  { to: '/documents', label: 'Documente', icon: FileText },
  { to: '/upload', label: 'Încărcare', icon: Upload },
  { to: '/alerts', label: 'Alerte', icon: AlertTriangle },
];

export default function Sidebar() {
  return (
    <aside className="w-[200px] min-w-[200px] bg-white border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-800">Makyol</h1>
        <p className="text-sm text-gray-500">Automatizare Documente</p>
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
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
