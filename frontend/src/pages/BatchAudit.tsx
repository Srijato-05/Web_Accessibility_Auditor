import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { client } from '../api/client.ts';
import { 
  Play, 
  Trash2, 
  Pause, 
  Activity, 
  Cpu, 
  Database, 
  Compass, 
  Plus, 
  Loader2, 
  CheckCircle2, 
  AlertTriangle,
  Sliders,
  Settings,
  X,
  RefreshCw,
  FileText,
  Download
} from 'lucide-react';

interface Target {
  id: string;
  url: string;
  status: string;
  created_at: string | null;
  last_audit_at: string | null;
  frequency_hours: number;
  priority: number;
  retry_count: number;
  last_error: string | null;
  scan_profile: {
    depth?: number;
    max_pages?: number;
    concurrency?: number;
    strategy?: string;
  };
  last_session_id?: string | null;
}

interface BatchStatus {
  timestamp: string;
  process_status: string;
  batch_summary: {
    active: number;
    crawling: number;
    failed: number;
    paused: number;
    pending: number;
    total: number;
  };
  avg_priority: number;
  uptime_percentage: number;
  telemetry: {
    batch_start: string;
    domains_analyzed: number;
    success_count: number;
    failure_count: number;
    last_sweep_duration_seconds: number;
    average_processing_time: number;
  };
  cpu_percent: number;
  ram_percent: number;
}

export default function BatchAudit() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [status, setStatus] = useState<BatchStatus | null>(null);
  const [newUrl, setNewUrl] = useState('');
  const [priority, setPriority] = useState(3);
  const [frequency, setFrequency] = useState(24);
  const [maxDepth, setMaxDepth] = useState(2);
  const [maxPages, setMaxPages] = useState(20);
  const [strategy, setStrategy] = useState('fast');
  const [discoverUrl, setDiscoverUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  // Custom Profile Options sliding toggle
  const [showConfig, setShowConfig] = useState(false);
  
  // Edit State
  const [editingTarget, setEditingTarget] = useState<Target | null>(null);
  const [editPriority, setEditPriority] = useState(3);
  const [editDepth, setEditDepth] = useState(2);
  const [editPages, setEditPages] = useState(20);

  // Poll for targets and status
  const fetchAllData = async () => {
    try {
      const targetsRes = await client.get('/targets');
      setTargets(targetsRes.data);
      
      const statusRes = await client.get('/batch/status');
      setStatus(statusRes.data);
    } catch (err) {
      console.error("Failed to fetch batch console data:", err);
    }
  };

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAddTarget = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUrl) return;
    setLoading(true);
    setActionMessage(null);
    try {
      const payload = {
        url: newUrl,
        priority,
        frequency_hours: frequency,
        scan_profile: {
          depth: maxDepth,
          max_pages: maxPages,
          strategy
        }
      };
      const res = await client.post('/targets', payload);
      if (res.data.status === 'already_exists') {
        setActionMessage({ type: 'error', text: 'Target domain is already registered.' });
      } else {
        setActionMessage({ type: 'success', text: 'Target domain registered successfully!' });
        setNewUrl('');
        fetchAllData();
      }
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to add target.' });
    }
    setLoading(false);
  };

  const handleUpdateTarget = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTarget) return;
    setLoading(true);
    try {
      const payload = {
        url: editingTarget.url,
        priority: editPriority,
        scan_profile: {
          ...editingTarget.scan_profile,
          depth: editDepth,
          max_pages: editPages
        }
      };
      await client.post('/targets/update', payload);
      setActionMessage({ type: 'success', text: `Target config updated for ${editingTarget.url}` });
      setEditingTarget(null);
      fetchAllData();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to update config.' });
    }
    setLoading(false);
  };

  const handleDiscoverTargets = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!discoverUrl) return;
    setLoading(true);
    setActionMessage(null);
    try {
      await client.post('/targets/discover', { url: discoverUrl });
      setActionMessage({ type: 'success', text: 'Discovery session started in the background.' });
      setDiscoverUrl('');
      fetchAllData();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.response?.data?.detail || 'Discovery initialization failed.' });
    }
    setLoading(false);
  };

  const handleToggleTarget = async (url: string) => {
    try {
      await client.post('/targets/toggle', { url });
      fetchAllData();
    } catch (err) {
      console.error("Failed to toggle target:", err);
    }
  };

  const handleDeleteTarget = async (url: string) => {
    if (!confirm(`Are you sure you want to remove target: ${url}?`)) return;
    try {
      await client.delete('/targets', { params: { url } });
      fetchAllData();
    } catch (err) {
      console.error("Failed to delete target:", err);
    }
  };

  const handlePruneFailed = async () => {
    if (!confirm("Are you sure you want to prune all failed domains?")) return;
    setLoading(true);
    try {
      const res = await client.post('/targets/prune');
      setActionMessage({ type: 'success', text: `Successfully pruned ${res.data.pruned_count} failed target(s).` });
      fetchAllData();
    } catch (err) {
      console.error("Failed to prune targets:", err);
    }
    setLoading(false);
  };

  const handleRunBatchAudit = async (useQueue: boolean) => {
    setLoading(true);
    setActionMessage(null);
    try {
      const res = await client.post('/batch/run', { use_queue: useQueue });
      if (res.data.status === 'dispatched') {
        setActionMessage({ type: 'success', text: `Dispatched ${res.data.count} tasks to Redis queue.` });
      } else {
        setActionMessage({ type: 'success', text: 'Parallel local batch run initiated.' });
      }
      fetchAllData();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to run batch audit.' });
    }
    setLoading(false);
  };

  const handleExportBatchCSV = async () => {
    setLoading(true);
    try {
      const downloadUrl = `${client.defaults.baseURL || ''}/batch/export/csv`;
      window.open(downloadUrl, '_blank');
      setActionMessage({ type: 'success', text: 'Aggregated CSV summary compiled and downloaded.' });
    } catch (err) {
      console.error("Failed to export batch CSV:", err);
      setActionMessage({ type: 'error', text: 'Failed to compile batch CSV.' });
    }
    setLoading(false);
  };

  const handleExportViolationsCSV = async () => {
    setLoading(true);
    try {
      const downloadUrl = `${client.defaults.baseURL || ''}/batch/export/violations/csv`;
      window.open(downloadUrl, '_blank');
      setActionMessage({ type: 'success', text: 'Detailed violations CSV compiled and downloaded.' });
    } catch (err) {
      console.error("Failed to export violations CSV:", err);
      setActionMessage({ type: 'error', text: 'Failed to compile violations CSV.' });
    }
    setLoading(false);
  };

  const getStatusStyle = (statusStr: string) => {
    switch (statusStr.toLowerCase()) {
      case 'active':
        return 'bg-green-500/10 text-green-400 border border-green-500/30 shadow-[0_0_8px_rgba(34,197,94,0.1)]';
      case 'crawling':
        return 'bg-amber-500/10 text-amber-400 border border-amber-500/30 animate-pulse';
      case 'failed':
        return 'bg-red-500/10 text-red-400 border border-red-500/30';
      case 'paused':
        return 'bg-gray-500/10 text-gray-400 border border-gray-500/30';
      default:
        return 'bg-blue-500/10 text-blue-400 border border-blue-500/30';
    }
  };

  const getPriorityLabel = (priorityVal: number) => {
    switch (priorityVal) {
      case 1: return { text: 'Critical', style: 'bg-red-500/10 text-red-400 border-red-500/30' };
      case 2: return { text: 'High', style: 'bg-orange-500/10 text-orange-400 border-orange-500/30' };
      case 3: return { text: 'Medium', style: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30' };
      case 4: return { text: 'Low', style: 'bg-green-500/10 text-green-400 border-green-500/30' };
      default: return { text: 'Minimal', style: 'bg-blue-500/10 text-blue-400 border-blue-500/30' };
    }
  };

  return (
    <div className="min-h-screen bg-background text-on-surface p-8 max-w-7xl mx-auto pb-32">
      {/* Header */}
      <header className="mb-8 border-b border-surface-border pb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="bg-primary/10 text-primary p-2 rounded-md border border-primary/40 shadow-ambient animate-pulse">
              <Database size={24} />
            </div>
            <h1 className="text-3xl font-heading font-bold text-on-surface">Batch Audit Console</h1>
          </div>
          <p className="text-on-surface-variant text-sm mt-2">
            Orchestrate priority-scheduled batch surveillance audits across registered domains.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button 
            onClick={handleExportBatchCSV}
            disabled={loading}
            className="px-4 py-3 bg-surface hover:bg-surface-highlight border border-primary/30 hover:border-primary text-primary text-xs font-bold font-heading uppercase tracking-widest rounded-md transition-all flex items-center gap-2 cursor-pointer"
          >
            <Download size={14} /> Export CSV Summary
          </button>
          <button 
            onClick={handleExportViolationsCSV}
            disabled={loading}
            className="px-4 py-3 bg-surface hover:bg-surface-highlight border border-secondary border-blue-500/30 hover:border-blue-500 text-blue-400 text-xs font-bold font-heading uppercase tracking-widest rounded-md transition-all flex items-center gap-2 cursor-pointer"
          >
            <Download size={14} /> Export Violations Detail
          </button>
          <button 
            onClick={handlePruneFailed}
            disabled={loading}
            className="px-4 py-3 bg-surface hover:bg-surface-highlight border border-red-500/30 hover:border-red-500 text-red-400 text-xs font-bold font-heading uppercase tracking-widest rounded-md transition-all flex items-center gap-2 cursor-pointer"
          >
            <Trash2 size={14} /> Prune Failed
          </button>
          <button 
            onClick={() => handleRunBatchAudit(false)}
            disabled={loading}
            className="px-4 py-3 bg-surface hover:bg-surface-highlight border border-surface-border text-on-surface text-xs font-bold font-heading uppercase tracking-widest rounded-md transition-colors flex items-center gap-2 cursor-pointer"
          >
            <Play size={14} /> Run Local Batch
          </button>
          <button 
            onClick={() => handleRunBatchAudit(true)}
            disabled={loading}
            className="px-4 py-3 bg-primary hover:bg-primary-hover text-background text-xs font-bold font-heading uppercase tracking-widest rounded-md transition-colors flex items-center gap-2 cursor-pointer shadow-ambient"
          >
            <Activity size={14} /> Dispatch Redis Queue
          </button>
        </div>
      </header>

      {/* Action Messages */}
      {actionMessage && (
        <div className={`p-4 rounded-md mb-6 border flex items-center gap-3 text-sm font-heading ${
          actionMessage.type === 'success' 
            ? 'bg-green-500/10 border-green-500/30 text-green-400' 
            : 'bg-red-500/10 border-red-500/30 text-red-400'
        }`}>
          {actionMessage.type === 'success' ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
          <span className="flex-1">{actionMessage.text}</span>
          <button onClick={() => setActionMessage(null)} className="text-on-surface-variant hover:text-on-surface">
            <X size={14} />
          </button>
        </div>
      )}

      {/* Metric Cards */}
      <section className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 mb-8" aria-label="System Metrics">
        <div className="glass-panel p-6 bg-surface-container-low shadow-ambient">
          <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Network Hosts</span>
          <div className="text-3xl font-heading font-bold text-on-surface">
            {status?.batch_summary.total ?? targets.length}
          </div>
          <div className="text-[10px] text-on-surface-variant mt-1 flex justify-between">
            <span>Pending: {status?.batch_summary.pending ?? 0}</span>
            <span>Failed: {status?.batch_summary.failed ?? 0}</span>
          </div>
        </div>

        <div className="glass-panel p-6 bg-surface-container-low shadow-ambient">
          <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Queue Load Index</span>
          <div className="text-3xl font-heading font-bold text-amber-400 flex items-center gap-2">
            {status?.batch_summary.crawling ?? targets.filter(t => t.status === 'crawling').length}
            { (status?.batch_summary.crawling ?? 0) > 0 && <RefreshCw className="animate-spin text-amber-400" size={18} /> }
          </div>
          <div className="text-[10px] text-on-surface-variant mt-1">
            Avg Priority Level: {status?.avg_priority ?? '3.0'}
          </div>
        </div>

        <div className="glass-panel p-6 bg-surface-container-low shadow-ambient">
          <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">CPU Load</span>
          <div className="flex items-end justify-between">
            <span className="text-3xl font-heading font-bold text-primary">
              {status?.cpu_percent ? `${Math.round(status.cpu_percent)}%` : '0%'}
            </span>
            <Cpu className="text-primary/50 mb-1" size={16} />
          </div>
          <div className="w-full bg-surface-highlight h-1.5 rounded-full mt-2 overflow-hidden">
            <div 
              className="bg-primary h-full transition-all duration-500" 
              style={{ width: `${status?.cpu_percent ?? 0}%` }}
            />
          </div>
        </div>

        <div className="glass-panel p-6 bg-surface-container-low shadow-ambient">
          <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">RAM Utilization</span>
          <div className="flex items-end justify-between">
            <span className="text-3xl font-heading font-bold text-secondary">
              {status?.ram_percent ? `${Math.round(status.ram_percent)}%` : '0%'}
            </span>
            <Activity className="text-secondary/50 mb-1" size={16} />
          </div>
          <div className="w-full bg-surface-highlight h-1.5 rounded-full mt-2 overflow-hidden">
            <div 
              className="bg-secondary h-full transition-all duration-500" 
              style={{ width: `${status?.ram_percent ?? 0}%` }}
            />
          </div>
        </div>
      </section>

      {/* Target Registration Panel */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        <form onSubmit={handleAddTarget} className="glass-panel p-6 bg-surface-container-low shadow-ambient flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-sm font-bold font-heading uppercase tracking-wider text-on-surface flex items-center gap-2">
                <Plus size={16} className="text-primary" /> Register New Target Domain
              </h2>
              <button 
                type="button"
                onClick={() => setShowConfig(!showConfig)}
                className="text-xs text-primary hover:text-primary-hover flex items-center gap-1 cursor-pointer font-bold uppercase tracking-wider font-heading"
              >
                <Sliders size={12} /> {showConfig ? 'Hide Config' : 'Custom Config'}
              </button>
            </div>
            <p className="text-xs text-on-surface-variant mb-4">
              Add a new web target to the surveillance registry database for automated audit routines.
            </p>
            <input 
              type="url" 
              placeholder="https://example.com"
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              className="w-full bg-surface border border-surface-border rounded-md px-4 py-3 text-sm focus:outline-none focus:border-primary/50 text-on-surface transition-colors shadow-inner"
              required
            />

            {/* Custom config slider/collapsible block */}
            {showConfig && (
              <div className="mt-4 p-4 bg-surface rounded-md border border-surface-border space-y-4 animate-fadeIn">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Priority Level</label>
                    <select 
                      value={priority} 
                      onChange={(e) => setPriority(Number(e.target.value))}
                      className="w-full bg-surface-container-low border border-surface-border rounded p-2 text-xs text-on-surface"
                    >
                      <option value={1}>1 - Critical</option>
                      <option value={2}>2 - High</option>
                      <option value={3}>3 - Medium</option>
                      <option value={4}>4 - Low</option>
                      <option value={5}>5 - Minimal</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Scan Frequency</label>
                    <select 
                      value={frequency} 
                      onChange={(e) => setFrequency(Number(e.target.value))}
                      className="w-full bg-surface-container-low border border-surface-border rounded p-2 text-xs text-on-surface"
                    >
                      <option value={6}>Every 6 Hours</option>
                      <option value={12}>Every 12 Hours</option>
                      <option value={24}>Every 24 Hours</option>
                      <option value={72}>Every 3 Days</option>
                      <option value={168}>Every Week</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Crawl Depth Limit</label>
                    <input 
                      type="number" 
                      min={1} 
                      max={5} 
                      value={maxDepth} 
                      onChange={(e) => setMaxDepth(Number(e.target.value))}
                      className="w-full bg-surface-container-low border border-surface-border rounded p-2 text-xs text-on-surface"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Max Pages Scanned</label>
                    <input 
                      type="number" 
                      min={1} 
                      max={200} 
                      value={maxPages} 
                      onChange={(e) => setMaxPages(Number(e.target.value))}
                      className="w-full bg-surface-container-low border border-surface-border rounded p-2 text-xs text-on-surface"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Execution Speed Strategy</label>
                  <div className="flex gap-4 mt-1">
                    <label className="flex items-center gap-1.5 text-xs text-on-surface-variant cursor-pointer">
                      <input type="radio" name="strategy" value="fast" checked={strategy === 'fast'} onChange={() => setStrategy('fast')} />
                      Fast (High Concurrency)
                    </label>
                    <label className="flex items-center gap-1.5 text-xs text-on-surface-variant cursor-pointer">
                      <input type="radio" name="strategy" value="safe" checked={strategy === 'safe'} onChange={() => setStrategy('safe')} />
                      Polite (Slow / Throttled)
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>
          <button 
            type="submit" 
            disabled={loading || !newUrl}
            className="mt-4 w-full px-4 py-3 bg-primary/10 text-primary border border-primary/45 hover:bg-primary/20 text-xs font-bold font-heading uppercase tracking-wider rounded-md transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {loading ? <Loader2 className="animate-spin" size={14} /> : <Plus size={14} />} Register Target
          </button>
        </form>

        <form onSubmit={handleDiscoverTargets} className="glass-panel p-6 bg-surface-container-low shadow-ambient flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-bold font-heading uppercase tracking-wider text-on-surface mb-2 flex items-center gap-2">
              <Compass size={16} className="text-secondary" /> Autonomously Discover Targets
            </h2>
            <p className="text-xs text-on-surface-variant mb-4">
              Extract sitemaps and robots.txt paths to autonomously discover and bulk-register targets.
            </p>
            <input 
              type="url" 
              placeholder="https://example.com"
              value={discoverUrl}
              onChange={(e) => setDiscoverUrl(e.target.value)}
              className="w-full bg-surface border border-surface-border rounded-md px-4 py-3 text-sm focus:outline-none focus:border-secondary/50 text-on-surface transition-colors shadow-inner"
              required
            />
          </div>
          <button 
            type="submit" 
            disabled={loading || !discoverUrl}
            className="mt-4 w-full px-4 py-3 bg-secondary/10 text-secondary border border-secondary/45 hover:bg-secondary/20 text-xs font-bold font-heading uppercase tracking-wider rounded-md transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {loading ? <Loader2 className="animate-spin" size={14} /> : <Compass size={14} />} Discover & Seed
          </button>
        </form>
      </section>

      {/* Target Registry Table */}
      <section className="glass-panel bg-surface-container-low shadow-ambient overflow-hidden">
        <div className="p-6 border-b border-surface-border flex justify-between items-center">
          <h2 className="text-sm font-bold font-heading uppercase tracking-wider text-on-surface">
            Network Registry Ledger
          </h2>
          <span className="text-[10px] text-on-surface-variant font-mono">
            Uptime Check: Stable • Auto-Sync: 5s
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-surface-border bg-surface-highlight text-left">
                <th className="py-4 px-6 text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Domain URL</th>
                <th className="py-4 px-6 text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Priority</th>
                <th className="py-4 px-6 text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Status</th>
                <th className="py-4 px-6 text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Retries</th>
                <th className="py-4 px-6 text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Last Audit</th>
                <th className="py-4 px-6 text-[10px] font-bold uppercase tracking-wider text-on-surface-variant text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {targets.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-xs text-on-surface-variant">
                    No target networks registered yet. Seed a domain to begin.
                  </td>
                </tr>
              ) : (
                targets.map((target) => {
                  const pBadge = getPriorityLabel(target.priority);
                  return (
                    <tr key={target.id} className="border-b border-surface-border hover:bg-surface-highlight/50 transition-colors">
                      <td className="py-4 px-6">
                        <div className="text-xs font-bold text-on-surface">{target.url}</div>
                        {target.last_error && (
                          <div className="text-[10px] text-red-400 mt-1 max-w-md font-mono flex items-center gap-1.5">
                            <AlertTriangle size={10} /> {target.last_error}
                          </div>
                        )}
                        {target.scan_profile && (target.scan_profile.depth || target.scan_profile.max_pages) && (
                          <div className="text-[10px] text-on-surface-variant mt-0.5 flex gap-2">
                            <span>Depth Limit: {target.scan_profile.depth || 2}</span>
                            <span>Max Pages: {target.scan_profile.max_pages || 20}</span>
                            <span>Strategy: {target.scan_profile.strategy || 'fast'}</span>
                          </div>
                        )}
                        {target.scan_profile && (target.scan_profile as any).checkpoint && (
                          <div className="text-[10px] text-amber-400 mt-1 flex items-center gap-1 font-semibold">
                            <Activity size={10} className="animate-pulse" />
                            <span>
                              Checkpoint Active: {((target.scan_profile as any).checkpoint.visited_urls || []).length} audited, {((target.scan_profile as any).checkpoint.pending_queue || []).length} pending
                            </span>
                          </div>
                        )}
                      </td>
                      <td className="py-4 px-6">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border ${pBadge.style}`}>
                          {pBadge.text}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <span className={`px-2.5 py-1 rounded text-[10px] font-bold font-heading uppercase tracking-wider ${getStatusStyle(target.status)}`}>
                          {target.status}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-xs text-on-surface-variant font-mono">
                        {target.retry_count ?? 0}
                      </td>
                      <td className="py-4 px-6 text-xs text-on-surface-variant">
                        {target.last_audit_at ? new Date(target.last_audit_at).toLocaleString() : 'Never Scanned'}
                      </td>
                      <td className="py-4 px-6 text-right space-x-2">
                        {target.last_session_id && (
                          <>
                            <Link 
                              to={`/insights/${target.last_session_id}`}
                              title="View Interactive Report"
                              className="inline-flex p-2 bg-surface hover:bg-surface-highlight border border-primary/30 rounded-md text-primary hover:text-primary-hover transition-colors cursor-pointer"
                            >
                              <FileText size={12} />
                            </Link>
                            <a 
                              href={`${import.meta.env.VITE_API_URL || ''}/reports/${target.last_session_id}/download`}
                              download
                              title="Download Stakeholder PDF"
                              className="inline-flex p-2 bg-surface hover:bg-surface-highlight border border-green-500/30 rounded-md text-green-400 hover:text-green-300 transition-colors cursor-pointer"
                            >
                              <Download size={12} />
                            </a>
                          </>
                        )}
                        <button 
                          onClick={() => {
                            setEditingTarget(target);
                            setEditPriority(target.priority);
                            setEditDepth(target.scan_profile?.depth || 2);
                            setEditPages(target.scan_profile?.max_pages || 20);
                          }}
                          title="Edit Config Profile"
                          className="p-2 bg-surface hover:bg-surface-highlight border border-surface-border rounded-md text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
                        >
                          <Settings size={12} />
                        </button>
                        <button 
                          onClick={() => handleToggleTarget(target.url)}
                          title={target.status === 'paused' ? 'Activate Target' : 'Pause Target'}
                          className="p-2 bg-surface hover:bg-surface-highlight border border-surface-border rounded-md text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
                        >
                          {target.status === 'paused' ? <Play size={12} /> : <Pause size={12} />}
                        </button>
                        <button 
                          onClick={() => handleDeleteTarget(target.url)}
                          title="Deregister Target"
                          className="p-2 bg-surface hover:bg-surface-highlight border border-surface-border rounded-md text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                        >
                          <Trash2 size={12} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Editing Dialog Modal */}
      {editingTarget && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleUpdateTarget} className="glass-panel p-6 bg-surface-container-low max-w-md w-full shadow-2xl border border-surface-border relative animate-scaleUp">
            <button 
              type="button" 
              onClick={() => setEditingTarget(null)}
              className="absolute top-4 right-4 text-on-surface-variant hover:text-on-surface cursor-pointer"
            >
              <X size={16} />
            </button>
            <h3 className="text-sm font-bold font-heading uppercase tracking-wider text-on-surface mb-2 flex items-center gap-2">
              <Settings size={16} className="text-primary" /> Edit Scan Profile
            </h3>
            <p className="text-xs text-on-surface-variant mb-6 font-mono break-all">{editingTarget.url}</p>

            <div className="space-y-4 mb-6">
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Priority Level</label>
                <select 
                  value={editPriority} 
                  onChange={(e) => setEditPriority(Number(e.target.value))}
                  className="w-full bg-surface border border-surface-border rounded p-2 text-xs text-on-surface focus:outline-none focus:border-primary/50"
                >
                  <option value={1}>1 - Critical</option>
                  <option value={2}>2 - High</option>
                  <option value={3}>3 - Medium</option>
                  <option value={4}>4 - Low</option>
                  <option value={5}>5 - Minimal</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Crawl Depth Limit</label>
                  <input 
                    type="number" 
                    min={1} 
                    max={5} 
                    value={editDepth} 
                    onChange={(e) => setEditDepth(Number(e.target.value))}
                    className="w-full bg-surface border border-surface-border rounded p-2 text-xs text-on-surface focus:outline-none focus:border-primary/50"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Max Pages Scanned</label>
                  <input 
                    type="number" 
                    min={1} 
                    max={200} 
                    value={editPages} 
                    onChange={(e) => setEditPages(Number(e.target.value))}
                    className="w-full bg-surface border border-surface-border rounded p-2 text-xs text-on-surface focus:outline-none focus:border-primary/50"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button 
                type="button" 
                onClick={() => setEditingTarget(null)}
                className="flex-1 py-3 bg-surface hover:bg-surface-highlight border border-surface-border text-on-surface text-xs font-bold font-heading uppercase tracking-wider rounded transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button 
                type="submit" 
                disabled={loading}
                className="flex-1 py-3 bg-primary hover:bg-primary-hover text-background text-xs font-bold font-heading uppercase tracking-wider rounded transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-ambient"
              >
                {loading ? <Loader2 className="animate-spin" size={14} /> : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
