import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { client } from '../api/client.ts';
import { Activity, Play, Loader2, Download } from 'lucide-react';
import { GraphView } from '../components/GraphView.tsx';

interface DashboardSummary {
  health_score: number;
  rating: string;
  issues: {
    critical: number;
    major: number;
    minor: number;
  };
  categories?: {
    color_contrast: number;
    aria_semantics: number;
    keyboard_navigation: number;
    structure: number;
  };
  agent_insights?: {
    total_missions: number;
    breakdown: {
      visual: number;
      motor: number;
      cognitive: number;
      neural: number;
    };
    neural_active: boolean;
  };
  recent_scans: {
    id: string;
    url: string;
    score: number;
    status: string;
    date: string;
  }[];
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    client.get('/dashboard/summary')
      .then((res: any) => setSummary(res.data))
      .catch((e: any) => {
        console.error(e);
        setSummary({ health_score: 0, rating: "-", issues: { critical: 0, major: 0, minor: 0 }, recent_scans: [] });
      });
  }, []);

  if (!summary) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background" aria-live="polite" aria-busy="true">
        <Loader2 className="animate-spin text-primary" size={48} aria-label="Loading Dashboard Data" />
      </div>
    );
  }

  const filteredScans = (summary.recent_scans || []).filter((scan: any) => {
    const matchesSearch = scan.url.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || scan.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 pb-32 min-h-screen">
      <header className="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-surface-border pb-8">
        <div>
          <h1 className="text-3xl font-heading font-bold text-on-surface">Dashboard</h1>
          <p className="text-on-surface-variant mt-2 text-sm">Overview of tracking application status and health.</p>
        </div>
        <div>
          <button onClick={() => navigate('/')} className="primary-btn flex items-center gap-2 relative focus:ring-2 focus:ring-primary outline-none" aria-label="Start a new accessibility scan">
            <Play size={16} className="fill-current" aria-hidden="true" /> New Scan
          </button>
        </div>
      </header>
 
      <div className="space-y-10">
        {/* Summary Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="glass-panel p-6 border-t-4 border-t-primary flex flex-col justify-between min-h-[140px]">
            <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Monitored Hosts</span>
            <div className="flex items-baseline gap-2 mt-4">
              <span className="text-5xl font-heading font-bold text-primary">
                {summary.recent_scans ? new Set(summary.recent_scans.map(s => s.url)).size : 0}
              </span>
              <span className="text-sm font-mono text-on-surface-variant">Domains</span>
            </div>
            <p className="text-[10px] text-on-surface-variant mt-2 leading-relaxed">Unique target host endpoints registered in network.</p>
          </div>

          <div className="glass-panel p-6 border-t-4 border-t-secondary flex flex-col justify-between min-h-[140px]">
            <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">AI Agent Missions</span>
            <div className="flex items-baseline gap-2 mt-4">
              <span className="text-5xl font-heading font-bold text-secondary">
                {summary.agent_insights?.total_missions || 0}
              </span>
              <span className="text-sm font-mono text-on-surface-variant">
                Missions
              </span>
            </div>
            <p className="text-[10px] text-on-surface-variant mt-2 leading-relaxed">Simulated accessibility agent audits executed.</p>
          </div>

          <div className="glass-panel p-6 border-t-4 border-t-error flex flex-col justify-between min-h-[140px]">
            <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Active Violations</span>
            <div className="flex items-baseline gap-2 mt-4">
              <span className="text-4xl font-heading font-bold text-error">
                {summary.issues ? (summary.issues.critical + summary.issues.major) : 0}
              </span>
              <span className="text-xs font-mono text-on-surface-variant">Unresolved</span>
            </div>
            <p className="text-[10px] text-on-surface-variant mt-2 leading-relaxed">Combined count of Critical and Major severity bugs.</p>
          </div>

          <div className="glass-panel p-6 border-t-4 border-t-primary/50 flex flex-col justify-between min-h-[140px]">
            <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Total Scanned Links</span>
            <span className="text-4xl font-heading font-bold text-on-surface mt-4 block">{summary.recent_scans ? summary.recent_scans.length : 0}</span>
            <p className="text-[10px] text-on-surface-variant mt-2 leading-relaxed">Number of structural paths crawler completed.</p>
          </div>
        </div>

        {/* Visual Analytics Widgets */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Issue Severity Distribution */}
          <div className="glass-panel p-6 border-t-2 border-t-error flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-heading font-bold text-on-surface uppercase tracking-wider mb-4">Heuristic Severity Distribution</h3>
              <div className="space-y-4">
                {[
                  { label: 'Critical Errors', count: summary.issues ? summary.issues.critical : 0, color: 'bg-error', desc: 'Severe accessibility barriers preventing interactions.' },
                  { label: 'Major Disruptions', count: summary.issues ? summary.issues.major : 0, color: 'bg-warning', desc: 'Substantial layout reflow, contrast, or navigation loops.' },
                  { label: 'Minor Advisories', count: summary.issues ? summary.issues.minor : 0, color: 'bg-primary', desc: 'Missing meta descriptors, language codes, or structural nodes.' }
                ].map((item) => {
                  const total = (summary.issues ? (summary.issues.critical + summary.issues.major + summary.issues.minor) : 0) || 1;
                  const percentage = Math.min(100, Math.max(8, (item.count / total) * 100));
                  const testId = `severity-count-${item.label.toLowerCase().replace(/\s+/g, '-')}`;
                  return (
                    <div key={item.label} className="space-y-1">
                      <div className="flex justify-between items-center text-xs font-mono">
                        <span className="text-on-surface font-semibold">{item.label}</span>
                        <span data-testid={testId} className="text-on-surface-variant">{item.count} items ({Math.round((item.count/total)*100)}%)</span>
                      </div>
                      <div className="w-full bg-background h-2 rounded-full overflow-hidden border border-surface-border/30">
                        <div className={`h-full ${item.color} transition-all duration-500`} style={{ width: `${percentage}%` }}></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <p className="text-[10px] text-on-surface-variant mt-4">Calculated from total registered database violation instances.</p>
          </div>

          {/* Audit Coverage Progress */}
          <div className="glass-panel p-6 border-t-2 border-t-primary flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-heading font-bold text-on-surface uppercase tracking-wider mb-2">Audit Verification Status</h3>
              <p className="text-xs text-on-surface-variant leading-relaxed">
                Dynamic category compliance levels compiled from heuristics gathered across registered domain scans.
              </p>
            </div>
            
            <div className="grid grid-cols-2 gap-3 mt-6">
              <div className="p-3 bg-background rounded border border-surface-border/50 text-center space-y-2">
                <span className="text-[9px] uppercase font-bold text-on-surface-variant block truncate">Keyboard Navigation</span>
                <span className="text-2xl font-heading font-bold text-primary block">
                  {summary.categories?.keyboard_navigation || 0}
                </span>
                <span className="text-[9px] text-on-surface-variant block font-mono">violations</span>
              </div>

              <div className="p-3 bg-background rounded border border-surface-border/50 text-center space-y-2">
                <span className="text-[9px] uppercase font-bold text-on-surface-variant block truncate">Color & Contrast</span>
                <span className="text-2xl font-heading font-bold text-secondary block">
                  {summary.categories?.color_contrast || 0}
                </span>
                <span className="text-[9px] text-on-surface-variant block font-mono">violations</span>
              </div>

              <div className="p-3 bg-background rounded border border-surface-border/50 text-center space-y-2">
                <span className="text-[9px] uppercase font-bold text-on-surface-variant block truncate">ARIA & Semantics</span>
                <span className="text-2xl font-heading font-bold text-warning block">
                  {summary.categories?.aria_semantics || 0}
                </span>
                <span className="text-[9px] text-on-surface-variant block font-mono">violations</span>
              </div>

              <div className="p-3 bg-background rounded border border-surface-border/50 text-center space-y-2">
                <span className="text-[9px] uppercase font-bold text-on-surface-variant block truncate">Structure & HTML</span>
                <span className="text-2xl font-heading font-bold text-on-surface block">
                  {summary.categories?.structure || 0}
                </span>
                <span className="text-[9px] text-on-surface-variant block font-mono">violations</span>
              </div>
            </div>
          </div>
        </div>

        {/* Immersive Forensic Graph */}
        <section aria-labelledby="network-viz-title">
          <div className="flex justify-between items-center mb-4">
            <h2 id="network-viz-title" className="text-xl font-heading font-bold text-on-surface">Audit Network Visualization</h2>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse" aria-hidden="true"></div>
              <span className="text-[10px] uppercase tracking-widest font-bold text-primary">Live Forensic Stream</span>
            </div>
          </div>
          <span className="sr-only">Interactive network visualization showing connections between audited web targets. Tab to the recent history table below for detailed scanning lists.</span>
          <div className="flat-panel p-6 h-[500px] flex items-center justify-center overflow-hidden border-t-2 border-t-primary">
            {summary.recent_scans.length > 0 ? (
              <GraphView />
            ) : (
              <div className="text-center">
                <Activity size={48} className="mx-auto text-surface-highlight mb-4 opacity-20" aria-hidden="true" />
                <p className="text-xs text-on-surface-variant uppercase tracking-widest font-bold">Awaiting Tactical Data</p>
              </div>
            )}
          </div>
        </section>

        {/* Mission History Table */}
        <section aria-labelledby="recent-history-title">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
            <h2 id="recent-history-title" className="text-xl font-heading font-bold text-on-surface">Recent Mission History</h2>
            
            {/* Filter controls */}
            <div className="flex items-center gap-3 w-full md:w-auto">
              <input
                type="text"
                placeholder="Search Domain..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-background text-on-surface border border-surface-border rounded-md px-3 py-1.5 text-xs focus:ring-1 focus:ring-primary focus:outline-none w-full md:w-48 placeholder:text-on-surface-variant/50 font-mono"
              />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-background text-on-surface border border-surface-border rounded-md px-3 py-1.5 text-xs focus:ring-1 focus:ring-primary focus:outline-none cursor-pointer font-mono"
              >
                <option value="all">All Logs</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
              </select>
            </div>
          </div>
          <div className="flat-panel overflow-hidden border-t-2 border-t-secondary/30">
            {filteredScans.length > 0 ? (
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-surface-border bg-surface-highlight/50 text-xs uppercase tracking-wider text-on-surface-variant font-bold">
                    <th scope="col" className="px-6 py-4">Target Host</th>
                    <th scope="col" className="px-6 py-4 text-center">Compliance Level</th>
                    <th scope="col" className="px-6 py-4 text-center">Advice Report</th>
                    <th scope="col" className="px-6 py-4 text-right">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredScans.map((log: any) => (
                    <tr key={log.id} className="border-b border-surface-border hover:bg-surface-highlight transition-colors last:border-b-0 group">
                      <td className="px-6 py-4 text-sm font-medium text-on-surface group-hover:text-primary transition-colors">
                        <div className="flex items-center gap-3">
                          <div className="w-1.5 h-1.5 rounded-full bg-surface-highlight group-hover:bg-primary transition-all" aria-hidden="true"></div>
                          <Link to={'/insights/' + log.id} className="hover:underline focus:underline focus:text-primary outline-none">
                            {log.url}
                          </Link>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className={`text-[10px] uppercase tracking-wider font-extrabold px-2.5 py-1 rounded-full ${
                          log.status === 'completed' ? 'bg-primary/10 text-primary border border-primary/20' :
                          log.status === 'failed' ? 'bg-error/10 text-error border border-error/20' :
                          'bg-on-surface/10 text-on-surface-variant border border-surface-border/50'
                        }`}>
                          {log.status === 'completed' ? 'Completed' : log.status === 'failed' ? 'Failed' : 'In Progress'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={(e: any) => {
                            e.stopPropagation();
                            const apiBase = client.defaults.baseURL || 'http://localhost:8000/api';
                            window.open(`${apiBase}/reports/${log.id}/download`, '_blank');
                          }}
                          className="p-2 hover:bg-primary/10 rounded-full text-on-surface-variant hover:text-primary transition-all group/btn focus:ring-2 focus:ring-primary outline-none"
                          title={`Download PDF report for ${log.url}`}
                          aria-label={`Download PDF report for ${log.url}`}
                        >
                          <Download size={14} aria-hidden="true" />
                        </button>
                      </td>
                      <td className="px-6 py-4 text-right text-[10px] font-mono text-on-surface-variant uppercase">
                        {new Date(log.date).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-16 text-center text-on-surface-variant flex flex-col items-center justify-center">
                <Activity size={32} className="opacity-20 mb-4" aria-hidden="true" />
                <p className="text-sm">No analysis history logs match your search.</p>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
