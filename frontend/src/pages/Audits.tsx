import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { client } from '../api/client.ts';
import { Loader2, Download, Search, Shield, ChevronUp, ChevronDown, ArrowUpDown } from 'lucide-react';

export default function Audits() {
  const [scans, setScans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortKey, setSortKey] = useState<'url' | 'status' | 'date'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    client.get('/dashboard/summary')
      .then(res => {
        setScans(res.data.recent_scans || []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const filteredScans = scans.filter(scan => {
    const matchesSearch = scan.url.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || 
      (statusFilter === 'completed' && scan.status === 'completed') ||
      (statusFilter === 'failed' && scan.status === 'failed') ||
      (statusFilter === 'pending' && scan.status !== 'completed' && scan.status !== 'failed');
    return matchesSearch && matchesStatus;
  });

  const handleSort = (key: 'url' | 'status' | 'date') => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };

  const sortedScans = [...filteredScans].sort((a, b) => {
    let valA = a[sortKey];
    let valB = b[sortKey];
    if (sortKey === 'date') {
      valA = new Date(a.date).getTime();
      valB = new Date(b.date).getTime();
    }
    if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-background" aria-live="polite">
      <Loader2 className="animate-spin text-primary" size={48} aria-label="Decrypting ledger registry..." />
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 pb-32 min-h-screen">
      <header className="mb-10 border-b border-surface-border pb-8">
        <h1 className="text-3xl font-heading font-bold text-on-surface">Audits Ledger</h1>
        <p className="text-on-surface-variant mt-2 text-sm">Review full list of target domains and audit progress.</p>
      </header>

      {/* Quick counters grid */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">
        <div className="glass-panel p-4 flex flex-col justify-between min-h-[90px]">
          <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Total Targets</span>
          <span className="text-2xl font-heading font-bold text-on-surface mt-1">{scans.length}</span>
        </div>
        <div className="glass-panel p-4 flex flex-col justify-between min-h-[90px] border-l-4 border-l-primary">
          <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Completed</span>
          <span className="text-2xl font-heading font-bold text-primary mt-1">{scans.filter(s => s.status === 'completed').length}</span>
        </div>
        <div className="glass-panel p-4 flex flex-col justify-between min-h-[90px] border-l-4 border-l-error">
          <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Failed</span>
          <span className="text-2xl font-heading font-bold text-error mt-1">{scans.filter(s => s.status === 'failed').length}</span>
        </div>
        <div className="glass-panel p-4 flex flex-col justify-between min-h-[90px] border-l-4 border-l-warning">
          <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">In Progress</span>
          <span className="text-2xl font-heading font-bold text-warning mt-1">{scans.filter(s => s.status !== 'completed' && s.status !== 'failed').length}</span>
        </div>
      </div>

      {/* Filter and search deck */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center mb-6">
        <div className="relative flex-1 w-full max-w-md">
          <label htmlFor="ledger-search" className="sr-only">Search scans by domain</label>
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant" aria-hidden="true">
            <Search size={16} />
          </div>
          <input
            id="ledger-search"
            type="text"
            placeholder="Search targets by domain..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-surface border border-surface-border rounded-md pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary text-on-surface"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <label htmlFor="ledger-status-filter" className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Status:</label>
          <select
            id="ledger-status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-background text-on-surface border border-surface-border rounded-md px-3 py-2 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-primary cursor-pointer w-full md:w-auto"
          >
            <option value="all">All Audits</option>
            <option value="completed">Completed Scans</option>
            <option value="failed">Failed Scans</option>
            <option value="pending">Pending Scans</option>
          </select>
        </div>
      </div>

      {/* Ledger Table */}
      <div className="flat-panel overflow-hidden border-t-2 border-t-secondary">
        {sortedScans.length > 0 ? (
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-surface-border bg-surface-highlight/50 text-xs uppercase tracking-wider text-on-surface-variant font-bold select-none">
                <th 
                  scope="col" 
                  onClick={() => handleSort('url')}
                  className="px-6 py-4 cursor-pointer hover:text-on-surface transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    Target Website Domain
                    {sortKey === 'url' ? (
                      sortOrder === 'asc' ? <ChevronUp size={12} className="text-primary" /> : <ChevronDown size={12} className="text-primary" />
                    ) : <ArrowUpDown size={10} className="opacity-40" />}
                  </div>
                </th>
                <th 
                  scope="col" 
                  onClick={() => handleSort('status')}
                  className="px-6 py-4 text-center cursor-pointer hover:text-on-surface transition-colors"
                >
                  <div className="flex items-center justify-center gap-1.5">
                    Audit Status
                    {sortKey === 'status' ? (
                      sortOrder === 'asc' ? <ChevronUp size={12} className="text-primary" /> : <ChevronDown size={12} className="text-primary" />
                    ) : <ArrowUpDown size={10} className="opacity-40" />}
                  </div>
                </th>
                <th scope="col" className="px-6 py-4 text-center">PDF Report</th>
                <th 
                  scope="col" 
                  onClick={() => handleSort('date')}
                  className="px-6 py-4 text-right cursor-pointer hover:text-on-surface transition-colors"
                >
                  <div className="flex items-center justify-end gap-1.5">
                    Scanned Date
                    {sortKey === 'date' ? (
                      sortOrder === 'asc' ? <ChevronUp size={12} className="text-primary" /> : <ChevronDown size={12} className="text-primary" />
                    ) : <ArrowUpDown size={10} className="opacity-40" />}
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedScans.map((scan) => (
                <tr key={scan.id} className="border-b border-surface-border hover:bg-surface-highlight/50 transition-colors last:border-b-0 group">
                  <td className="px-6 py-4 text-sm font-medium text-on-surface">
                    <Link to={`/insights/${scan.id}`} className="hover:underline hover:text-primary outline-none focus:text-primary">
                      {scan.url}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`text-[10px] uppercase tracking-wider font-extrabold px-2.5 py-1 rounded-full ${
                      scan.status === 'completed' ? 'bg-primary/10 text-primary border border-primary/20' :
                      scan.status === 'failed' ? 'bg-error/10 text-error border border-error/20' :
                      'bg-on-surface/10 text-on-surface-variant border border-surface-border/50'
                    }`}>
                      {scan.status === 'completed' ? 'Completed' : scan.status === 'failed' ? 'Failed' : 'In Progress'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <button
                      onClick={() => {
                        const apiBase = client.defaults.baseURL || 'http://localhost:8000/api';
                        window.open(`${apiBase}/reports/${scan.id}/download`, '_blank');
                      }}
                      className="p-2 hover:bg-primary/10 rounded-full text-on-surface-variant hover:text-primary transition-all focus:ring-2 focus:ring-primary outline-none"
                      aria-label={`Download PDF report for ${scan.url}`}
                    >
                      <Download size={14} aria-hidden="true" />
                    </button>
                  </td>
                  <td className="px-6 py-4 text-right text-xs font-mono text-on-surface-variant uppercase">
                    {new Date(scan.date).toLocaleDateString()} {new Date(scan.date).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-16 text-center text-on-surface-variant flex flex-col items-center justify-center">
            <Shield size={36} className="opacity-20 mb-4" aria-hidden="true" />
            <p className="text-sm">No registry listings found matching active criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
}
