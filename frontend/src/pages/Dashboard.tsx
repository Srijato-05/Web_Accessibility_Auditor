import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { client } from '../api/client.ts';
import { Activity, Play, Loader2, Download } from 'lucide-react';
import { GraphView } from '../components/GraphView.tsx';
import { Tooltip } from '../components/Tooltip.tsx';

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
    compliance_level?: string;
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

  const getOverallCompliance = (scansList: any[]) => {
    const activeScans = scansList.filter((s: any) => s.status === 'completed' && s.compliance_level);
    if (activeScans.length === 0) return 'N/A';
    if (activeScans.some((s: any) => s.compliance_level === 'Below A')) return 'Below A';
    if (activeScans.some((s: any) => s.compliance_level === 'A')) return 'A';
    if (activeScans.some((s: any) => s.compliance_level === 'AA')) return 'AA';
    if (activeScans.every((s: any) => s.compliance_level === 'AAA')) return 'AAA';
    return 'N/A';
  };

  // Dynamically calculate statistics from the active filtered scans
  const getDynamicStats = () => {
    const defaultStats = {
      monitored_hosts: 0,
      critical: 0,
      major: 0,
      minor: 0,
      total_violations: 0,
      total_scanned_links: 0,
      categories: {
        color_contrast: 0,
        aria_semantics: 0,
        keyboard_navigation: 0,
        structure: 0
      }
    };

    if (!summary) return defaultStats;

    // Filter to scans matching the search term
    const allMatching = (summary.recent_scans || []).filter((scan: any) => 
      scan.url.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    // Only count completed scans for violation stats
    const searchFiltered = allMatching.filter((scan: any) => scan.status === 'completed');

    if (!searchTerm.trim()) {
      return {
        monitored_hosts: new Set((summary.recent_scans || []).map(s => s.url)).size,
        critical: summary.issues?.critical || 0,
        major: summary.issues?.major || 0,
        minor: summary.issues?.minor || 0,
        total_violations: (summary.issues?.critical || 0) + (summary.issues?.major || 0) + (summary.issues?.minor || 0),
        total_scanned_links: (summary.recent_scans || []).length,
        categories: summary.categories || {
          color_contrast: 0,
          aria_semantics: 0,
          keyboard_navigation: 0,
          structure: 0
        }
      };
    }

    const stats = {
      monitored_hosts: new Set(allMatching.map(s => s.url)).size,
      critical: 0,
      major: 0,
      minor: 0,
      total_violations: 0,
      total_scanned_links: allMatching.length,
      categories: {
        color_contrast: 0,
        aria_semantics: 0,
        keyboard_navigation: 0,
        structure: 0
      }
    };

    searchFiltered.forEach((scan: any) => {
      if (scan.issues) {
        stats.critical += scan.issues.critical || 0;
        stats.major += scan.issues.major || 0;
        stats.minor += scan.issues.minor || 0;
      }
      if (scan.categories) {
        stats.categories.color_contrast += scan.categories.color_contrast || 0;
        stats.categories.aria_semantics += scan.categories.aria_semantics || 0;
        stats.categories.keyboard_navigation += scan.categories.keyboard_navigation || 0;
        stats.categories.structure += scan.categories.structure || 0;
      }
    });

    stats.total_violations = stats.critical + stats.major + stats.minor;
    return stats;
  };

  const dynamicStats = getDynamicStats();

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 pb-32 min-h-screen fade-in-up">
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
                {dynamicStats.monitored_hosts}
              </span>
              <span className="text-sm font-mono text-on-surface-variant">Domains</span>
            </div>
            <p className="text-[10px] text-on-surface-variant mt-2 leading-relaxed">Unique target host endpoints registered in network.</p>
          </div>

          <div className="glass-panel p-6 border-t-4 border-t-error flex flex-col justify-between min-h-[140px]">
            <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Critical & Major Violations</span>
            <div className="flex items-baseline gap-2 mt-4">
              <span className="text-4xl font-heading font-bold text-error">
                {dynamicStats.critical + dynamicStats.major}
              </span>
              <span className="text-xs font-mono text-on-surface-variant">High-Risk</span>
            </div>
            <p className="text-[10px] text-on-surface-variant mt-2 leading-relaxed">Combined count of Critical and Major severity bugs.</p>
          </div>

          <div className="glass-panel p-6 border-t-4 border-t-secondary flex flex-col justify-between min-h-[140px]">
            <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Total Violations</span>
            <div className="flex items-baseline gap-2 mt-4">
              <span className="text-4xl font-heading font-bold text-secondary">
                {dynamicStats.total_violations}
              </span>
              <span className="text-xs font-mono text-on-surface-variant">All Issues</span>
            </div>
            <p className="text-[10px] text-on-surface-variant mt-2 leading-relaxed">Total count of Critical, Major, and Minor accessibility bugs.</p>
          </div>

          <div className="glass-panel p-6 border-t-4 border-t-primary/50 flex flex-col justify-between min-h-[140px]">
            <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Total Scanned Links</span>
            <span className="text-4xl font-heading font-bold text-on-surface mt-4 block">{dynamicStats.total_scanned_links}</span>
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
                  { label: 'Critical Errors', count: dynamicStats.critical, color: 'bg-error', desc: 'Severe accessibility barriers preventing interactions.' },
                  { label: 'Major Disruptions', count: dynamicStats.major, color: 'bg-warning', desc: 'Substantial layout reflow, contrast, or navigation loops.' },
                  { label: 'Minor Advisories', count: dynamicStats.minor, color: 'bg-primary', desc: 'Missing meta descriptors, language codes, or structural nodes.' }
                ].map((item) => {
                  const total = dynamicStats.total_violations || 1;
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


        {/* WCAG Compliance Checklist Deck (Idea 4) */}
        <section aria-labelledby="wcag-checklist-deck-title" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 id="wcag-checklist-deck-title" className="text-xl font-heading font-bold text-on-surface">WCAG Conformance Checklist Deck</h2>
              <p className="text-xs text-on-surface-variant mt-1">Status of core criteria compiled from active crawler scans</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                id: '1.4.3',
                title: 'Contrast (Minimum)',
                desc: 'Text elements must meet minimum contrast thresholds.',
                violations: dynamicStats.categories.color_contrast,
                color: 'text-secondary',
                strokeColor: '#00f2fe',
                level: 'AA/AAA'
              },
              {
                id: '2.1.1',
                title: 'Keyboard Access',
                desc: 'All interactive elements must respond to keyboard tabs.',
                violations: dynamicStats.categories.keyboard_navigation,
                color: 'text-primary',
                strokeColor: '#39ff14',
                level: 'A/AAA'
              },
              {
                id: '1.3.1',
                title: 'ARIA & Semantics',
                desc: 'Assistive tech needs proper label roles & descriptors.',
                violations: dynamicStats.categories.aria_semantics,
                color: 'text-warning',
                strokeColor: '#ffb703',
                level: 'A/AA'
              },
              {
                id: '2.4.1',
                title: 'HTML Structure',
                desc: 'Landmark hierarchy and skips should guide traversals.',
                violations: dynamicStats.categories.structure,
                color: 'text-error',
                strokeColor: '#ff0055',
                level: 'A/AA'
              }
            ].map((card) => {
              const score = Math.max(0, 100 - (card.violations * 10));
              // SVG Circle parameters
              const radius = 24;
              const circumference = 2 * Math.PI * radius;
              const offset = circumference - (score / 100) * circumference;

              return (
                <div key={card.id} className="glass-panel p-5 flex flex-col justify-between min-h-[180px] hover:border-primary/40 transition-all group relative overflow-hidden bg-surface-container-low">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-on-surface-variant bg-surface-highlight/30 px-2 py-0.5 rounded border border-surface-border/50">WCAG {card.id} ({card.level})</span>
                      <h3 className="text-sm font-bold text-on-surface mt-2.5 group-hover:text-primary transition-colors">{card.title}</h3>
                    </div>
                    
                    {/* SVG Progress Ring */}
                    <div className="relative w-12 h-12 shrink-0 flex items-center justify-center">
                      <svg className="w-full h-full transform -rotate-90">
                        <circle
                          cx="24"
                          cy="24"
                          r={radius}
                          className="stroke-surface-border/30"
                          strokeWidth="3"
                          fill="transparent"
                        />
                        <circle
                          cx="24"
                          cy="24"
                          r={radius}
                          stroke={card.strokeColor}
                          strokeWidth="3"
                          fill="transparent"
                          strokeDasharray={circumference}
                          strokeDashoffset={offset}
                          className="transition-all duration-700 ease-out"
                          strokeLinecap="round"
                        />
                      </svg>
                      <span className="absolute text-[10px] font-mono font-bold text-on-surface">{score}%</span>
                    </div>
                  </div>
                  
                  <p className="text-[10px] text-on-surface-variant leading-relaxed mt-2">{card.desc}</p>
                  
                  <div className="flex items-center justify-between border-t border-surface-border/30 pt-3 mt-3">
                    <span className="text-[9px] font-mono uppercase tracking-wider text-on-surface-variant font-bold">
                      {card.violations === 0 ? '0 Violations' : `${card.violations} Violations`}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Mission History Table */}
        <section aria-labelledby="recent-history-title">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
            <div className="flex flex-wrap items-center gap-3">
              <h2 id="recent-history-title" className="text-xl font-heading font-bold text-on-surface">Recent Mission History</h2>
              {filteredScans.length > 0 && (
                <div className="flex items-center gap-2 bg-surface-highlight/40 px-3 py-1 rounded border border-surface-border text-xs">
                  <span className="text-on-surface-variant font-medium">Overall Combined Compliance:</span>
                  <span className={`text-[10px] uppercase tracking-wider font-extrabold px-2 py-0.5 rounded ${
                    getOverallCompliance(filteredScans) === 'AAA' ? 'bg-primary/10 text-primary border border-primary/20' :
                    getOverallCompliance(filteredScans) === 'AA' ? 'bg-secondary/10 text-secondary border border-secondary/20' :
                    getOverallCompliance(filteredScans) === 'A' ? 'bg-warning/10 text-warning border border-warning/20' :
                    getOverallCompliance(filteredScans) === 'Below A' ? 'bg-error/10 text-error border border-error/20' :
                    'bg-on-surface/10 text-on-surface-variant border border-surface-border/50'
                  }`}>
                    {getOverallCompliance(filteredScans)}
                  </span>
                </div>
              )}
            </div>
            
            {/* Filter controls */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 w-full md:w-auto mt-2 md:mt-0">
              <input
                type="text"
                placeholder="Search Domain..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-background text-on-surface border border-surface-border rounded-md px-3 py-1.5 text-xs focus:ring-1 focus:ring-primary focus:outline-none w-full md:w-48 placeholder:text-on-surface-variant/50 font-mono"
              />
              <div className="flex items-center gap-2" role="group" aria-label="Filter scans by execution status">
                <button
                  onClick={() => setStatusFilter('all')}
                  aria-pressed={statusFilter === 'all'}
                  className={`px-3 py-1.5 text-xs font-bold font-heading rounded-md border transition-all focus:ring-2 focus:ring-primary outline-none ${
                    statusFilter === 'all'
                      ? 'bg-primary text-background border-primary shadow-neon'
                      : 'bg-surface text-on-surface-variant border-surface-border hover:text-on-surface'
                  }`}
                >
                  All ({summary.recent_scans?.length || 0})
                </button>
                <button
                  onClick={() => setStatusFilter('completed')}
                  aria-pressed={statusFilter === 'completed'}
                  className={`px-3 py-1.5 text-xs font-bold font-heading rounded-md border transition-all focus:ring-2 focus:ring-primary outline-none ${
                    statusFilter === 'completed'
                      ? 'bg-primary text-background border-primary shadow-neon'
                      : 'bg-surface text-on-surface-variant border-surface-border hover:text-on-surface'
                  }`}
                >
                  Completed ({summary.recent_scans?.filter((s: any) => s.status === 'completed').length || 0})
                </button>
                <button
                  onClick={() => setStatusFilter('failed')}
                  aria-pressed={statusFilter === 'failed'}
                  className={`px-3 py-1.5 text-xs font-bold font-heading rounded-md border transition-all focus:ring-2 focus:ring-primary outline-none ${
                    statusFilter === 'failed'
                      ? 'bg-primary text-background border-primary shadow-neon'
                      : 'bg-surface text-on-surface-variant border-surface-border hover:text-on-surface'
                  }`}
                >
                  Failed ({summary.recent_scans?.filter((s: any) => s.status === 'failed').length || 0})
                </button>
              </div>
            </div>
          </div>
          <div className="flat-panel overflow-hidden border-t-2 border-t-secondary/30">
            {filteredScans.length > 0 ? (
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-surface-border bg-surface-highlight/50 text-xs uppercase tracking-wider text-on-surface-variant font-bold">
                    <th scope="col" className="px-6 py-4">Target Host</th>
                    <th scope="col" className="px-6 py-4 text-center">Status</th>
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
                        <Tooltip
                          id={`tooltip-${log.id}`}
                          content={
                            log.compliance_level === 'AAA' ? 'Meets full WCAG AAA requirements with optimal contrast and accessibility parameters.' :
                            log.compliance_level === 'AA' ? 'Meets standard WCAG AA guidelines. Some strict AAA contrast levels might not be reached.' :
                            log.compliance_level === 'A' ? 'Meets base Level A criteria only. Critical accessibility failures exist.' :
                            log.compliance_level === 'Below A' ? 'Below basic Level A standard. Critical accessibility disruptions detected.' :
                            'No compliance rating is assigned yet for this page.'
                          }
                        >
                          <span className={`text-[10px] uppercase tracking-wider font-extrabold px-2.5 py-1 rounded-full cursor-help ${
                            log.compliance_level === 'AAA' ? 'bg-primary/10 text-primary border border-primary/20' :
                            log.compliance_level === 'AA' ? 'bg-secondary/10 text-secondary border border-secondary/20' :
                            log.compliance_level === 'A' ? 'bg-warning/10 text-warning border border-warning/20' :
                            log.compliance_level === 'Below A' ? 'bg-error/10 text-error border border-error/20' :
                            'bg-on-surface/10 text-on-surface-variant border border-surface-border/50'
                          }`}>
                            {log.compliance_level || 'N/A'}
                          </span>
                        </Tooltip>
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
