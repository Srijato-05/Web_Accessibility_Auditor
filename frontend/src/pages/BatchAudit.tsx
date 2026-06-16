import { useState, useEffect, useRef } from 'react';
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
  Settings,
  X,
  RefreshCw,
  FileText,
  Download,
  Search,
  SlidersHorizontal,
  Zap,
  Check,
  ChevronUp,
  ChevronDown,
  AlertCircle,
  Upload,
  ListPlus
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
  const strategy = 'fast';
  const [discoverUrl, setDiscoverUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  // Interactive Panel Settings
  const [activeTab, setActiveTab] = useState<'register' | 'discover' | 'import'>('register');
  const [showConfig, setShowConfig] = useState(false);
  
  // Import Site Lists State
  const [importText, setImportText] = useState('');
  const [importUrls, setImportUrls] = useState<string[]>([]);
  const [importProgress, setImportProgress] = useState<{ current: number; total: number } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Filtering, Sorting & Selection
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'url' | 'priority' | 'last_audit' | 'status'>('url');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [selectedUrls, setSelectedUrls] = useState<string[]>([]);

  // Edit Target State
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
      setSelectedUrls(prev => prev.filter(u => u !== url));
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

  // Bulk Operations
  const handleBulkToggle = async (pause: boolean) => {
    setLoading(true);
    try {
      for (const url of selectedUrls) {
        const target = targets.find(t => t.url === url);
        if (target) {
          const isCurrentlyPaused = target.status === 'paused';
          if ((pause && !isCurrentlyPaused) || (!pause && isCurrentlyPaused)) {
            await client.post('/targets/toggle', { url });
          }
        }
      }
      setActionMessage({ type: 'success', text: `Successfully toggled status for ${selectedUrls.length} targets.` });
      fetchAllData();
    } catch (err) {
      console.error("Bulk status toggle error:", err);
    }
    setLoading(false);
  };

  const handleBulkDelete = async () => {
    if (!confirm(`Are you sure you want to remove the ${selectedUrls.length} selected targets?`)) return;
    setLoading(true);
    try {
      for (const url of selectedUrls) {
        await client.delete('/targets', { params: { url } });
      }
      setActionMessage({ type: 'success', text: `Deregistered ${selectedUrls.length} selected targets.` });
      setSelectedUrls([]);
      fetchAllData();
    } catch (err) {
      console.error("Bulk delete error:", err);
    }
    setLoading(false);
  };

  // Local site list parsing
  const parseUrlsFromText = (text: string) => {
    const lines = text.split(/[\n,]/);
    const valid = lines
      .map(line => line.trim())
      .filter(line => {
        try {
          if (!line) return false;
          // Simple URL structure check
          new URL(line.startsWith('http') ? line : `https://${line}`);
          return true;
        } catch {
          return false;
        }
      })
      .map(line => line.startsWith('http') ? line : `https://${line}`);
    
    // De-duplicate
    return Array.from(new Set(valid));
  };

  useEffect(() => {
    const urls = parseUrlsFromText(importText);
    setImportUrls(urls);
  }, [importText]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      setImportText(text);
    };
    reader.readAsText(file);
  };

  const handleBulkImport = async () => {
    if (importUrls.length === 0) return;
    setLoading(true);
    setImportProgress({ current: 0, total: importUrls.length });
    
    let successCount = 0;
    let failCount = 0;

    for (let i = 0; i < importUrls.length; i++) {
      const url = importUrls[i];
      setImportProgress({ current: i + 1, total: importUrls.length });
      try {
        const payload = {
          url,
          priority,
          frequency_hours: frequency,
          scan_profile: {
            depth: maxDepth,
            max_pages: maxPages,
            strategy
          }
        };
        await client.post('/targets', payload);
        successCount++;
      } catch (err) {
        failCount++;
      }
    }

    setActionMessage({
      type: 'success',
      text: `Import completed: Registered ${successCount} targets successfully. Failed: ${failCount}`
    });

    setImportText('');
    setImportUrls([]);
    setImportProgress(null);
    setLoading(false);
    fetchAllData();
  };

  // Helper formatting styles
  const getPriorityConfig = (priorityVal: number) => {
    switch (priorityVal) {
      case 1: return { text: 'Critical', textStyle: 'text-error border-error/25 bg-error/5', borderStyle: 'border-l-error' };
      case 2: return { text: 'High', textStyle: 'text-warning border-warning/25 bg-warning/5', borderStyle: 'border-l-warning' };
      case 3: return { text: 'Medium', textStyle: 'text-secondary border-secondary/25 bg-secondary/5', borderStyle: 'border-l-secondary' };
      case 4: return { text: 'Low', textStyle: 'text-primary border-primary/25 bg-primary/5', borderStyle: 'border-l-primary' };
      default: return { text: 'Minimal', textStyle: 'text-on-surface-variant border-surface-border bg-background', borderStyle: 'border-l-surface-border' };
    }
  };

  const getStatusConfig = (statusStr: string) => {
    switch (statusStr.toLowerCase()) {
      case 'active':
        return {
          bg: 'bg-primary/10 text-primary border border-primary/25',
          dot: 'bg-primary shadow-[0_0_8px_rgba(var(--primary-rgb),0.5)]',
          label: 'Active'
        };
      case 'crawling':
        return {
          bg: 'bg-warning/10 text-warning border border-warning/25 animate-pulse',
          dot: 'bg-warning shadow-[0_0_8px_rgba(var(--warning-rgb),0.5)] animate-ping',
          label: 'Crawling'
        };
      case 'failed':
        return {
          bg: 'bg-error/10 text-error border border-error/25',
          dot: 'bg-error',
          label: 'Failed'
        };
      case 'paused':
        return {
          bg: 'bg-on-surface/10 text-on-surface-variant border border-surface-border/40',
          dot: 'bg-on-surface-variant/40',
          label: 'Paused'
        };
      default:
        return {
          bg: 'bg-secondary/10 text-secondary border border-secondary/25',
          dot: 'bg-secondary',
          label: 'Pending'
        };
    }
  };

  // Filtered & Sorted targets list
  const filteredSortedTargets = targets
    .filter(t => {
      const matchesSearch = t.url.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesPriority = selectedPriority === 'all' || t.priority.toString() === selectedPriority;
      const matchesStatus = selectedStatus === 'all' || t.status.toLowerCase() === selectedStatus;
      return matchesSearch && matchesPriority && matchesStatus;
    })
    .sort((a, b) => {
      let comparison = 0;
      if (sortBy === 'url') {
        comparison = a.url.localeCompare(b.url);
      } else if (sortBy === 'priority') {
        comparison = a.priority - b.priority;
      } else if (sortBy === 'status') {
        comparison = a.status.localeCompare(b.status);
      } else if (sortBy === 'last_audit') {
        const dateA = a.last_audit_at ? new Date(a.last_audit_at).getTime() : 0;
        const dateB = b.last_audit_at ? new Date(b.last_audit_at).getTime() : 0;
        comparison = dateA - dateB;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedUrls(filteredSortedTargets.map(t => t.url));
    } else {
      setSelectedUrls([]);
    }
  };

  const handleSelectRow = (url: string, checked: boolean) => {
    if (checked) {
      setSelectedUrls(prev => [...prev, url]);
    } else {
      setSelectedUrls(prev => prev.filter(u => u !== url));
    }
  };

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  return (
    <div className="min-h-screen bg-background text-on-surface p-8 max-w-7xl mx-auto pb-32 fade-in-up">
      {/* 1. Header Control Deck */}
      <header className="mb-8 border-b border-surface-border/40 pb-6 flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6">
        <div>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gradient-to-tr from-primary/10 to-secondary/15 border border-primary/25 flex items-center justify-center rounded-xl shadow-[0_0_15px_rgba(var(--primary-rgb),0.08)]">
              <Database size={24} className="text-primary" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-heading font-black tracking-tight text-on-surface uppercase">Batch Audit Dashboard</h1>
                <span className="w-2 h-2 rounded-full bg-primary animate-pulse" title="Engine Online"></span>
              </div>
              <p className="text-on-surface-variant text-[11px] font-mono tracking-widest mt-1 uppercase">
                Host Scheduler & Queue Management Operations
              </p>
            </div>
          </div>
        </div>

        {/* Action controls */}
        <div className="flex flex-wrap items-center gap-3 w-full xl:w-auto">
          {/* Dispatcher Actions */}
          <div className="flex items-center bg-surface border border-surface-border rounded-xl p-1 gap-1 shadow-inner w-full sm:w-auto">
            <button 
              onClick={() => handleRunBatchAudit(false)}
              disabled={loading}
              className="flex-1 sm:flex-initial px-4 py-2 hover:bg-surface-highlight text-on-surface text-xs font-bold font-heading uppercase tracking-wider rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer outline-none"
            >
              <Play size={13} className="text-primary" /> Run Local
            </button>
            <button 
              onClick={() => handleRunBatchAudit(true)}
              disabled={loading}
              className="flex-1 sm:flex-initial px-4 py-2 bg-primary hover:bg-primary/95 text-background text-xs font-bold font-heading uppercase tracking-wider rounded-lg transition-all flex items-center justify-center gap-2 cursor-pointer shadow-md"
            >
              <Zap size={13} /> Queue Redis
            </button>
          </div>

          {/* Export Deck */}
          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <button 
              onClick={handleExportBatchCSV}
              disabled={loading}
              className="px-3.5 py-2 bg-surface hover:bg-surface-highlight border border-surface-border hover:border-primary/45 text-on-surface-variant hover:text-primary text-xs font-bold font-heading uppercase tracking-wider rounded-lg transition-all cursor-pointer flex items-center gap-1.5"
            >
              <Download size={13} /> Summary
            </button>
            <button 
              onClick={handleExportViolationsCSV}
              disabled={loading}
              className="px-3.5 py-2 bg-surface hover:bg-surface-highlight border border-surface-border hover:border-secondary/45 text-on-surface-variant hover:text-secondary text-xs font-bold font-heading uppercase tracking-wider rounded-lg transition-all cursor-pointer flex items-center gap-1.5"
            >
              <FileText size={13} /> Details
            </button>
            <button 
              onClick={handlePruneFailed}
              disabled={loading}
              title="Prune Failed Items"
              className="p-2 bg-surface hover:bg-error/10 border border-surface-border hover:border-error/35 text-on-surface-variant hover:text-error rounded-lg transition-all cursor-pointer flex items-center justify-center"
            >
              <Trash2 size={13} />
            </button>
          </div>
        </div>
      </header>

      {/* Action Logs Banner */}
      {actionMessage && (
        <div className={`p-4 rounded-xl mb-6 border flex items-center gap-3 text-xs font-semibold tracking-wide shadow-md animate-scaleUp ${
          actionMessage.type === 'success' 
            ? 'bg-primary/5 border-primary/25 text-primary' 
            : 'bg-error/5 border-error/25 text-error'
        }`}>
          {actionMessage.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          <span className="flex-1 font-mono">{actionMessage.text}</span>
          <button onClick={() => setActionMessage(null)} className="text-on-surface-variant hover:text-on-surface p-1 rounded-md hover:bg-surface-highlight transition-colors">
            <X size={12} />
          </button>
        </div>
      )}

      {/* 2. System Load Indicators */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8" aria-label="System Metrics">
        {/* Metric 1 */}
        <div className="glass-panel p-6 border-t-2 border-t-secondary flex flex-col justify-between min-h-[125px]">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Monitored Domains</span>
            <div className="text-3xl font-heading font-black text-on-surface">{status?.batch_summary.total ?? targets.length}</div>
          </div>
          <div className="text-[9px] text-on-surface-variant mt-2 font-mono flex items-center justify-between border-t border-surface-border/20 pt-2">
            <span>Pending: <strong className="text-secondary">{status?.batch_summary.pending ?? 0}</strong></span>
            <span>Failed: <strong className="text-error">{status?.batch_summary.failed ?? 0}</strong></span>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="glass-panel p-6 border-t-2 border-t-warning flex flex-col justify-between min-h-[125px]">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Queue Size</span>
            <div className="text-3xl font-heading font-black text-warning flex items-center gap-2">
              {status?.batch_summary.crawling ?? targets.filter(t => t.status === 'crawling').length}
              { (status?.batch_summary.crawling ?? 0) > 0 && <RefreshCw className="animate-spin text-warning" size={16} /> }
            </div>
          </div>
          <div className="text-[9px] text-on-surface-variant mt-2 font-mono flex items-center justify-between border-t border-surface-border/20 pt-2">
            <span>Avg Priority: <strong className="text-on-surface">{status?.avg_priority ?? '3.0'}</strong></span>
            <span>Uptime: <strong className="text-primary">{status?.uptime_percentage ?? 100}%</strong></span>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="glass-panel p-6 border-t-2 border-t-primary flex flex-col justify-between min-h-[125px]">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">CPU Load</span>
            <div className="flex items-baseline justify-between">
              <span className="text-3xl font-heading font-black text-primary">
                {status?.cpu_percent ? `${Math.round(status.cpu_percent)}%` : '0%'}
              </span>
              <Cpu className="text-primary/40" size={15} />
            </div>
          </div>
          <div className="w-full bg-background border border-surface-border/30 h-1.5 rounded-full mt-2 overflow-hidden">
            <div className="bg-primary h-full rounded-full transition-all duration-500" style={{ width: `${status?.cpu_percent ?? 0}%` }} />
          </div>
        </div>

        {/* Metric 4 */}
        <div className="glass-panel p-6 border-t-2 border-t-secondary flex flex-col justify-between min-h-[125px]">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">RAM Utilization</span>
            <div className="flex items-baseline justify-between">
              <span className="text-3xl font-heading font-black text-secondary">
                {status?.ram_percent ? `${Math.round(status.ram_percent)}%` : '0%'}
              </span>
              <Activity className="text-secondary/40" size={15} />
            </div>
          </div>
          <div className="w-full bg-background border border-surface-border/30 h-1.5 rounded-full mt-2 overflow-hidden">
            <div className="bg-secondary h-full rounded-full transition-all duration-500" style={{ width: `${status?.ram_percent ?? 0}%` }} />
          </div>
        </div>
      </section>

      {/* 3. Operational Forms */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-8 items-start">
        <div className="glass-panel bg-surface-container-low shadow-sm lg:col-span-8 overflow-hidden flex flex-col border border-surface-border/50">
          {/* Form Navigation Tabs */}
          <div className="flex border-b border-surface-border/40 bg-surface-highlight/20">
            <button
              onClick={() => setActiveTab('register')}
              className={`flex-1 py-3.5 px-6 text-xs font-bold font-heading uppercase tracking-wider border-b-2 transition-all flex items-center justify-center gap-2 cursor-pointer outline-none ${
                activeTab === 'register'
                  ? 'border-primary text-primary bg-background/20'
                  : 'border-transparent text-on-surface-variant hover:text-on-surface'
              }`}
            >
              <Plus size={14} /> Domain Registration
            </button>
            <button
              onClick={() => setActiveTab('discover')}
              className={`flex-1 py-3.5 px-6 text-xs font-bold font-heading uppercase tracking-wider border-b-2 transition-all flex items-center justify-center gap-2 cursor-pointer outline-none ${
                activeTab === 'discover'
                  ? 'border-secondary text-secondary bg-background/20'
                  : 'border-transparent text-on-surface-variant hover:text-on-surface'
              }`}
            >
              <Compass size={14} /> Autonomous Discovery
            </button>
            <button
              onClick={() => setActiveTab('import')}
              className={`flex-1 py-3.5 px-6 text-xs font-bold font-heading uppercase tracking-wider border-b-2 transition-all flex items-center justify-center gap-2 cursor-pointer outline-none ${
                activeTab === 'import'
                  ? 'border-primary text-primary bg-background/20'
                  : 'border-transparent text-on-surface-variant hover:text-on-surface'
              }`}
            >
              <ListPlus size={14} /> Bulk List Import
            </button>
          </div>

          <div className="p-6">
            {activeTab === 'register' ? (
              <form onSubmit={handleAddTarget} className="space-y-4">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-xs font-bold text-on-surface uppercase tracking-wider">Register Target Node</h3>
                    <p className="text-[10px] text-on-surface-variant mt-0.5">Seed a web domain registry into the automated scanner network.</p>
                  </div>
                  <button 
                    type="button"
                    onClick={() => setShowConfig(!showConfig)}
                    className={`text-[9px] font-bold uppercase tracking-wider font-heading px-2.5 py-1.5 rounded-lg border transition-all flex items-center gap-1 cursor-pointer outline-none ${
                      showConfig 
                        ? 'bg-primary/10 text-primary border-primary/20 shadow-sm' 
                        : 'bg-surface text-on-surface-variant border-surface-border hover:text-on-surface'
                    }`}
                  >
                    <SlidersHorizontal size={11} /> {showConfig ? 'Lock Config' : 'Customize Target'}
                  </button>
                </div>

                <div className="flex gap-2">
                  <input 
                    type="url" 
                    placeholder="https://example.com"
                    value={newUrl}
                    onChange={(e) => setNewUrl(e.target.value)}
                    className="flex-1 bg-surface border border-surface-border rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary/30 focus:border-primary/45 text-on-surface transition-colors shadow-inner font-mono"
                    required
                  />
                  <button 
                    type="submit" 
                    disabled={loading || !newUrl}
                    className="px-6 bg-primary hover:bg-primary/95 text-background text-xs font-bold font-heading uppercase tracking-wider rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                  >
                    {loading ? <Loader2 className="animate-spin" size={13} /> : <Plus size={13} />} Register
                  </button>
                </div>

                {/* Collapsible config values */}
                {showConfig && (
                  <div className="p-4 bg-background/50 rounded-xl border border-surface-border/40 space-y-4 animate-scaleUp">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Priority Classification</label>
                        <select 
                          value={priority} 
                          onChange={(e) => setPriority(Number(e.target.value))}
                          className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-xs text-on-surface focus:outline-none focus:border-primary/45"
                        >
                          <option value={1}>1 - Critical Service</option>
                          <option value={2}>2 - High Priority</option>
                          <option value={3}>3 - Medium Priority</option>
                          <option value={4}>4 - Low Priority</option>
                          <option value={5}>5 - Minimal Sandbox</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Check Intervals</label>
                        <select 
                          value={frequency} 
                          onChange={(e) => setFrequency(Number(e.target.value))}
                          className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-xs text-on-surface focus:outline-none focus:border-primary/45"
                        >
                          <option value={6}>Every 6 Hours</option>
                          <option value={12}>Every 12 Hours</option>
                          <option value={24}>Every 24 Hours</option>
                          <option value={72}>Every 3 Days</option>
                          <option value={168}>Every Week</option>
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Crawl Depth Limit</label>
                        <input 
                          type="number" 
                          min={1} 
                          max={5} 
                          value={maxDepth} 
                          onChange={(e) => setMaxDepth(Number(e.target.value))}
                          className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-xs text-on-surface"
                        />
                      </div>
                      <div>
                        <label className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Max Scanned Pages</label>
                        <input 
                          type="number" 
                          min={1} 
                          max={200} 
                          value={maxPages} 
                          onChange={(e) => setMaxPages(Number(e.target.value))}
                          className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-xs text-on-surface"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </form>
            ) : activeTab === 'discover' ? (
              <form onSubmit={handleDiscoverTargets} className="space-y-4">
                <div>
                  <h3 className="text-xs font-bold text-on-surface uppercase tracking-wider">Autonomous Sitemap Parser</h3>
                  <p className="text-[10px] text-on-surface-variant mt-0.5">Parse Sitemap URL or robots.txt to autonomously discover and auto-register sub-page targets.</p>
                </div>
                <div className="flex gap-2">
                  <input 
                    type="url" 
                    placeholder="https://example.com/sitemap.xml"
                    value={discoverUrl}
                    onChange={(e) => setDiscoverUrl(e.target.value)}
                    className="flex-1 bg-surface border border-surface-border rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-secondary/30 focus:border-secondary/45 text-on-surface transition-colors shadow-inner font-mono"
                    required
                  />
                  <button 
                    type="submit" 
                    disabled={loading || !discoverUrl}
                    className="px-6 bg-secondary hover:bg-secondary/95 text-background text-xs font-bold font-heading uppercase tracking-wider rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                  >
                    {loading ? <Loader2 className="animate-spin" size={13} /> : <Compass size={13} />} Seed Target
                  </button>
                </div>
              </form>
            ) : (
              /* BULK LIST IMPORT FORM */
              <div className="space-y-4">
                <div className="flex justify-between items-start flex-wrap gap-2">
                  <div>
                    <h3 className="text-xs font-bold text-on-surface uppercase tracking-wider">Bulk Target List Import</h3>
                    <p className="text-[10px] text-on-surface-variant mt-0.5">Paste list of URLs (one per line / comma-separated) or drag-and-drop a `.txt` or `.csv` file.</p>
                  </div>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="px-3 py-1.5 bg-surface hover:bg-surface-highlight border border-surface-border hover:border-primary/40 text-on-surface text-[10px] font-bold uppercase tracking-wider rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer outline-none"
                  >
                    <Upload size={12} /> Upload File
                  </button>
                  <input
                    type="file"
                    accept=".txt,.csv"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </div>

                <div className="space-y-3">
                  <textarea
                    placeholder="https://google.com&#10;https://github.com,https://npmjs.com"
                    value={importText}
                    onChange={(e) => setImportText(e.target.value)}
                    rows={4}
                    className="w-full bg-surface border border-surface-border rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary/30 focus:border-primary/45 text-on-surface font-mono shadow-inner leading-normal"
                  />
                  
                  {importUrls.length > 0 && (
                    <div className="text-[10px] font-mono text-primary flex items-center gap-1 bg-primary/5 p-2 rounded-lg border border-primary/15 max-w-fit">
                      <Check size={12} /> Detected {importUrls.length} valid target URL(s) to import.
                    </div>
                  )}

                  {importProgress && (
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-[10px] text-primary font-mono font-bold">
                        <span>Importing targets...</span>
                        <span>{importProgress.current} / {importProgress.total}</span>
                      </div>
                      <div className="w-full bg-surface border border-surface-border/50 h-2 rounded-full overflow-hidden p-0.5">
                        <div 
                          className="bg-primary h-full rounded-full transition-all duration-300"
                          style={{ width: `${(importProgress.current / importProgress.total) * 100}%` }}
                        />
                      </div>
                    </div>
                  )}

                  <div className="flex justify-between items-center pt-2 border-t border-surface-border/20">
                    <button
                      type="button"
                      onClick={() => setShowConfig(!showConfig)}
                      className={`text-[9px] font-bold uppercase tracking-wider font-heading px-2.5 py-1.5 rounded-lg border transition-all flex items-center gap-1 cursor-pointer outline-none ${
                        showConfig 
                          ? 'bg-primary/10 text-primary border-primary/20 shadow-sm' 
                          : 'bg-surface text-on-surface-variant border-surface-border hover:text-on-surface'
                      }`}
                    >
                      <SlidersHorizontal size={11} /> {showConfig ? 'Hide Config' : 'Default Profile'}
                    </button>

                    <button
                      onClick={handleBulkImport}
                      disabled={loading || importUrls.length === 0}
                      className="px-6 py-2 bg-primary hover:bg-primary/95 text-background text-xs font-bold font-heading uppercase tracking-wider rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 shadow-md"
                    >
                      {loading ? <Loader2 className="animate-spin" size={13} /> : <ListPlus size={13} />} Import List
                    </button>
                  </div>
                </div>

                {/* Collapsible config values for import */}
                {showConfig && (
                  <div className="p-4 bg-background/50 rounded-xl border border-surface-border/40 space-y-4 animate-scaleUp">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Import Default Priority</label>
                        <select 
                          value={priority} 
                          onChange={(e) => setPriority(Number(e.target.value))}
                          className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-xs text-on-surface focus:outline-none"
                        >
                          <option value={1}>1 - Critical Service</option>
                          <option value={2}>2 - High Priority</option>
                          <option value={3}>3 - Medium Priority</option>
                          <option value={4}>4 - Low Priority</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Import Default Interval</label>
                        <select 
                          value={frequency} 
                          onChange={(e) => setFrequency(Number(e.target.value))}
                          className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-xs text-on-surface focus:outline-none"
                        >
                          <option value={6}>Every 6 Hours</option>
                          <option value={12}>Every 12 Hours</option>
                          <option value={24}>Every 24 Hours</option>
                          <option value={72}>Every 3 Days</option>
                        </select>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* System guide card */}
        <div className="glass-panel p-6 bg-surface-container-low border-l-2 border-l-primary/45 lg:col-span-4 self-stretch flex flex-col justify-between border border-surface-border/50">
          <div className="space-y-4">
            <h3 className="text-[10px] font-black uppercase tracking-widest text-primary font-mono">Control Desk System</h3>
            <div className="space-y-3.5 text-[11px] leading-relaxed text-on-surface-variant">
              <div>
                <span className="font-bold text-on-surface block mb-0.5">Bulk Operations</span>
                Select multiple hosts in the ledger below to apply bulk commands (Run, Pause, Activate, Delete) in parallel.
              </div>
              <div className="border-t border-surface-border/25 pt-2.5">
                <span className="font-bold text-on-surface block mb-0.5">Redis Concurrency</span>
                Recommended for active crawls. Operates background browser sessions asynchronously.
              </div>
            </div>
          </div>
          <div className="pt-3 border-t border-surface-border/25 text-[9px] text-on-surface-variant/80 font-mono flex items-center gap-1.5 uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-ping"></span>
            System Engine is active
          </div>
        </div>
      </section>

      {/* 4. Refined Interactive List Ledger */}
      <section className="space-y-4">
        {/* Ledger Header Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-surface border border-surface-border/50 p-5 rounded-2xl shadow-sm">
          <div>
            <h2 className="text-base font-black tracking-tight text-on-surface uppercase">Network Registry Ledger</h2>
            <p className="text-[9px] text-on-surface-variant font-mono uppercase tracking-widest mt-0.5">
              Scheduled target lists ({filteredSortedTargets.length} targets)
            </p>
          </div>

          {/* Interactive Filters & Sorts */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Search */}
            <div className="relative">
              <input
                type="text"
                placeholder="Search Domain..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-background text-on-surface border border-surface-border rounded-xl pl-9 pr-3 py-2 text-xs focus:ring-1 focus:ring-primary focus:outline-none w-44 placeholder:text-on-surface-variant/40 font-mono"
              />
              <Search className="absolute left-3 top-2.5 text-on-surface-variant/40" size={12} />
            </div>

            {/* Filter Priority */}
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="bg-background border border-surface-border rounded-xl px-2.5 py-2 text-xs text-on-surface focus:outline-none"
            >
              <option value="all">All Priorities</option>
              <option value="1">Critical</option>
              <option value="2">High</option>
              <option value="3">Medium</option>
              <option value="4">Low</option>
            </select>

            {/* Filter Status */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-background border border-surface-border rounded-xl px-2.5 py-2 text-xs text-on-surface focus:outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active</option>
              <option value="crawling">Crawling</option>
              <option value="paused">Paused</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>

        {/* Dynamic Bulk Action Bar */}
        {selectedUrls.length > 0 && (
          <div className="flex flex-wrap items-center justify-between gap-4 bg-primary/5 border border-primary/20 p-4 rounded-xl shadow-sm animate-scaleUp">
            <div className="flex items-center gap-2 text-xs font-semibold text-primary">
              <CheckCircle2 size={16} />
              <span>{selectedUrls.length} targets selected for bulk actions</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleBulkToggle(false)}
                disabled={loading}
                className="px-3 py-1.5 bg-surface border border-primary/25 hover:bg-surface-highlight text-primary text-xs font-bold rounded-lg cursor-pointer flex items-center gap-1 transition-all"
              >
                <Play size={11} /> Activate All
              </button>
              <button
                onClick={() => handleBulkToggle(true)}
                disabled={loading}
                className="px-3 py-1.5 bg-surface border border-surface-border hover:bg-surface-highlight text-on-surface text-xs font-bold rounded-lg cursor-pointer flex items-center gap-1 transition-all"
              >
                <Pause size={11} /> Pause All
              </button>
              <button
                onClick={handleBulkDelete}
                disabled={loading}
                className="px-3 py-1.5 bg-error/10 hover:bg-error/15 border border-error/25 text-error text-xs font-bold rounded-lg cursor-pointer flex items-center gap-1 transition-all"
              >
                <Trash2 size={11} /> Delete Selected
              </button>
              <button
                onClick={() => setSelectedUrls([])}
                className="p-1.5 text-on-surface-variant hover:text-on-surface hover:bg-surface-highlight rounded-lg transition-colors cursor-pointer"
                title="Deselect All"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        )}

        {/* Ledger Column Headings & Sort Actions */}
        <div className="bg-surface-highlight/35 border border-surface-border/40 rounded-xl px-6 py-3 flex items-center text-[10px] font-bold uppercase tracking-wider text-on-surface-variant gap-4">
          <div className="flex items-center gap-3 w-8">
            <input
              type="checkbox"
              checked={filteredSortedTargets.length > 0 && selectedUrls.length === filteredSortedTargets.length}
              onChange={(e) => handleSelectAll(e.target.checked)}
              className="w-4.5 h-4.5 rounded bg-background border border-surface-border text-primary cursor-pointer focus:ring-0 focus:outline-none"
            />
          </div>
          
          <button 
            onClick={() => handleSort('url')}
            className="flex items-center gap-1 hover:text-on-surface transition-colors cursor-pointer w-[40%] text-left"
          >
            Domain Host Config {sortBy === 'url' && (sortOrder === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
          </button>
          
          <button 
            onClick={() => handleSort('priority')}
            className="flex items-center gap-1 hover:text-on-surface transition-colors cursor-pointer justify-center w-[12%]"
          >
            Priority {sortBy === 'priority' && (sortOrder === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
          </button>

          <button 
            onClick={() => handleSort('status')}
            className="flex items-center gap-1 hover:text-on-surface transition-colors cursor-pointer justify-center w-[12%]"
          >
            Status {sortBy === 'status' && (sortOrder === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
          </button>

          <button 
            onClick={() => handleSort('last_audit')}
            className="flex items-center gap-1 hover:text-on-surface transition-colors cursor-pointer w-[18%]"
          >
            Last Sweep {sortBy === 'last_audit' && (sortOrder === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
          </button>

          <div className="w-[12%] text-right">Operations</div>
        </div>

        {/* Interactive List Cards */}
        <div className="space-y-3.5">
          {filteredSortedTargets.length === 0 ? (
            <div className="glass-panel p-16 text-center border border-surface-border/50">
              <AlertCircle className="text-on-surface-variant/40 mx-auto mb-2" size={32} />
              <p className="text-xs text-on-surface-variant">No monitored host nodes match your query parameters.</p>
            </div>
          ) : (
            filteredSortedTargets.map((target) => {
              const pConfig = getPriorityConfig(target.priority);
              const sConfig = getStatusConfig(target.status);
              const isSelected = selectedUrls.includes(target.url);
              return (
                <div 
                  key={target.id}
                  className={`glass-panel bg-surface-container-low border-y border-r border-surface-border/50 border-l-4 ${pConfig.borderStyle} p-4 flex flex-col md:flex-row items-stretch md:items-center gap-4 transition-all duration-200 hover:shadow-sm ${
                    isSelected ? 'bg-primary/5 border-primary/20 shadow-[0_0_8px_rgba(var(--primary-rgb),0.05)]' : ''
                  }`}
                >
                  {/* Select Checkbox */}
                  <div className="flex items-center w-8 shrink-0">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => handleSelectRow(target.url, e.target.checked)}
                      className="w-4.5 h-4.5 rounded bg-background border border-surface-border text-primary cursor-pointer focus:ring-0 focus:outline-none"
                    />
                  </div>

                  {/* Domain Host & settings */}
                  <div className="w-full md:w-[40%] space-y-1.5 pr-4">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-bold text-on-surface hover:text-primary transition-colors font-mono tracking-tight break-all">
                        {target.url}
                      </span>
                    </div>

                    {target.scan_profile && (target.scan_profile.depth || target.scan_profile.max_pages) && (
                      <div className="text-[9px] text-on-surface-variant font-mono bg-background/40 p-1.5 rounded border border-surface-border/15 flex flex-wrap gap-x-3 gap-y-1 max-w-fit">
                        <span>Depth: {target.scan_profile.depth || 2}</span>
                        <span>Pages: {target.scan_profile.max_pages || 20}</span>
                        <span>Strategy: {target.scan_profile.strategy || 'fast'}</span>
                      </div>
                    )}

                    {target.scan_profile && (target.scan_profile as any).checkpoint && (
                      <div className="text-[9px] text-warning bg-warning/5 border border-warning/15 px-2 py-1 rounded font-semibold flex items-center gap-1.5 animate-pulse max-w-fit">
                        <Activity size={9} />
                        <span>Checkpoint Active ({((target.scan_profile as any).checkpoint.visited_urls || []).length} done)</span>
                      </div>
                    )}
                  </div>

                  {/* Priority Tag */}
                  <div className="w-full md:w-[12%] flex justify-start md:justify-center items-center">
                    <span className={`px-2.5 py-0.5 rounded text-[9px] font-mono font-bold uppercase tracking-wider border ${pConfig.textStyle}`}>
                      {pConfig.text}
                    </span>
                  </div>

                  {/* Status Indicator Pill */}
                  <div className="w-full md:w-[12%] flex justify-start md:justify-center items-center">
                    <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[10px] font-bold font-heading uppercase tracking-wider font-mono ${sConfig.bg}`}>
                      <span className={`w-1 h-1 rounded-full ${sConfig.dot}`}></span>
                      {sConfig.label}
                    </span>
                  </div>

                  {/* Last Sweep Time & Error logs inline */}
                  <div className="w-full md:w-[18%] flex flex-col justify-center gap-1 text-xs text-on-surface-variant font-mono">
                    <span>{target.last_audit_at ? new Date(target.last_audit_at).toLocaleString() : 'Never Scanned'}</span>
                    {target.retry_count > 0 && (
                      <span className="text-[9px] text-error">Retries: {target.retry_count}</span>
                    )}
                  </div>

                  {/* Actions Deck */}
                  <div className="w-full md:w-[12%] flex justify-end items-center">
                    <div className="inline-flex items-center gap-1.5 bg-background p-1.5 rounded-lg border border-surface-border/40 shadow-sm">
                      {target.last_session_id && (
                        <>
                          <Link 
                            to={`/insights/${target.last_session_id}`}
                            title="Interactive Insights Report"
                            className="p-1.5 bg-surface hover:bg-surface-highlight border border-surface-border rounded text-primary hover:text-primary transition-colors cursor-pointer"
                          >
                            <FileText size={11} />
                          </Link>
                          <a 
                            href={`${client.defaults.baseURL || ''}/reports/${target.last_session_id}/download`}
                            download
                            title="Download PDF Summary"
                            className="p-1.5 bg-surface hover:bg-surface-highlight border border-surface-border rounded text-green-400 hover:text-green-350 transition-colors cursor-pointer"
                          >
                            <Download size={11} />
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
                        title="Edit Target Configuration"
                        className="p-1.5 bg-surface hover:bg-surface-highlight border border-surface-border rounded text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
                      >
                        <Settings size={11} />
                      </button>
                      <button 
                        onClick={() => handleToggleTarget(target.url)}
                        title={target.status === 'paused' ? 'Activate Target' : 'Pause Target'}
                        className="p-1.5 bg-surface hover:bg-surface-highlight border border-surface-border rounded text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
                      >
                        {target.status === 'paused' ? <Play size={11} className="text-primary" /> : <Pause size={11} />}
                      </button>
                      <button 
                        onClick={() => handleDeleteTarget(target.url)}
                        title="Deregister Target"
                        className="p-1.5 bg-surface hover:bg-surface-highlight border border-surface-border rounded text-error hover:bg-error/10 transition-colors cursor-pointer"
                      >
                        <Trash2 size={11} />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </section>

      {/* Editing Dialog Modal */}
      {editingTarget && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleUpdateTarget} className="glass-panel p-6 bg-surface-container-low max-w-md w-full shadow-2xl border border-surface-border relative animate-scaleUp">
            <button 
              type="button" 
              onClick={() => setEditingTarget(null)}
              className="absolute top-4 right-4 text-on-surface-variant hover:text-on-surface p-1 rounded hover:bg-surface-highlight transition-colors cursor-pointer"
            >
              <X size={16} />
            </button>
            <h3 className="text-sm font-bold font-heading uppercase tracking-wider text-on-surface mb-1 flex items-center gap-2">
              <Settings size={16} className="text-primary" /> Edit Scan Profile
            </h3>
            <p className="text-[10px] text-on-surface-variant mb-6 font-mono break-all bg-background px-2 py-1.5 rounded border border-surface-border/40">{editingTarget.url}</p>

            <div className="space-y-4 mb-6">
              <div>
                <label className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Priority Hierarchy</label>
                <select 
                  value={editPriority} 
                  onChange={(e) => setEditPriority(Number(e.target.value))}
                  className="w-full bg-surface border border-surface-border rounded p-2 text-xs text-on-surface focus:outline-none focus:border-primary/50"
                >
                  <option value={1}>1 - Critical Service</option>
                  <option value={2}>2 - High Priority</option>
                  <option value={3}>3 - Standard (Medium)</option>
                  <option value={4}>4 - Low Priority</option>
                  <option value={5}>5 - Minimal/Sandbox</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Crawl Depth Limit</label>
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
                  <label className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">Max Scanned Pages</label>
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
                className="flex-1 py-3 bg-primary hover:bg-primary/95 text-background text-xs font-bold font-heading uppercase tracking-wider rounded transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-sm"
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
