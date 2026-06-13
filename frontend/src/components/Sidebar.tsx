import { Link, useLocation } from 'react-router-dom';
import { useTheme, type Theme } from './ThemeContext.tsx';
import { LayoutDashboard, ScanLine, FileSpreadsheet, Settings, HelpCircle, Activity } from 'lucide-react';

export default function Sidebar() {
  const { theme, setTheme } = useTheme();
  const location = useLocation();

  const menuItems = [
    { name: 'Scan Console', path: '/', icon: ScanLine },
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Audits Ledger', path: '/audits', icon: FileSpreadsheet },
    { name: 'Settings', path: '/profile', icon: Settings },
    { name: 'Help Center', path: '/help', icon: HelpCircle },
  ];

  return (
    <nav className="w-64 bg-surface border-r border-surface-border flex flex-col h-screen sticky top-0 shrink-0 select-none z-30" aria-label="Main Navigation">
      <div className="p-6 border-b border-surface-border flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-primary/10 border border-primary flex items-center justify-center animate-pulse">
          <Activity className="text-primary" size={16} />
        </div>
        <div>
          <span className="font-heading font-bold text-sm tracking-wider block text-on-surface">Sentinel</span>
          <span className="text-[9px] uppercase tracking-widest text-primary font-mono font-bold">A11yAudit</span>
        </div>
      </div>

      <div className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-md text-xs font-heading font-bold uppercase tracking-wider transition-all duration-150 group outline-none ${
                isActive
                  ? 'bg-primary/10 text-primary border-l-2 border-primary'
                  : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-highlight'
              }`}
            >
              <Icon size={16} className={isActive ? 'text-primary' : 'text-on-surface-variant group-hover:text-primary transition-colors'} />
              {item.name}
            </Link>
          );
        })}
      </div>

      <div className="p-6 border-t border-surface-border space-y-4">
        <div>
          <label htmlFor="theme-select" className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-2">Theme Deck</label>
          <select
            id="theme-select"
            value={theme}
            onChange={(e) => setTheme(e.target.value as Theme)}
            className="w-full bg-background border border-surface-border rounded px-3 py-2 text-xs font-bold text-on-surface focus:outline-none focus:ring-2 focus:ring-primary cursor-pointer uppercase tracking-wider font-heading"
          >
            <option value="cyberpunk">Cyberpunk Default</option>
            <option value="hc-dark">High Contrast Dark</option>
            <option value="hc-light">High Contrast Light</option>
            <option value="colorblind">Colorblind Assist</option>
          </select>
        </div>
      </div>
    </nav>
  );
}
