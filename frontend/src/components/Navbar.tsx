import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, ScanLine, Clock, Shield } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();

  if (location.pathname === '/') return null;

  const isActive = (path: string) => 
    location.pathname === path ? 'text-primary border-b-2 border-primary' : 'text-on-surface-variant hover:text-on-surface';

  return (
    <nav className="bg-surface border-b border-surface-border sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center gap-2">
              <Shield className="text-primary" size={24} />
              <span className="font-heading font-bold text-lg hidden sm:block tracking-tight text-on-surface">Sentinel</span>
            </div>
            <div className="ml-8 flex space-x-8">
              <Link to="/dashboard" className={`inline-flex items-center px-1 pt-1 text-sm font-medium transition-colors ${isActive('/dashboard')}`}>
                <LayoutDashboard className="mr-2" size={18} />
                Dashboard
              </Link>
              <Link to="/scan" className={`inline-flex items-center px-1 pt-1 text-sm font-medium transition-colors ${isActive('/scan')}`}>
                <ScanLine className="mr-2" size={18} />
                New Scan
              </Link>
              <Link to="/history" className={`inline-flex items-center px-1 pt-1 text-sm font-medium transition-colors ${isActive('/history')}`}>
                <Clock className="mr-2" size={18} />
                History
              </Link>
            </div>
          </div>
          <div className="flex items-center">
            <span className="text-sm text-on-surface-variant font-medium">Global AI Auditor</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
