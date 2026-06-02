import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { client } from '../api/client.ts';
import { Loader2, ArrowLeft, Download, ShieldAlert, Network, ChevronRight } from 'lucide-react';

interface AuditDetail {
  id: string;
  url: string;
  status: string;
  date: string;
  violations: {
    id: string;
    rule_id: string;
    impact: string;
    description: string;
    help_url: string;
    impact_score: number;
    occurrences: number;
    target?: string;
    agent?: string;
    category?: string;
    nodes?: {
      html: string;
      target: string;
      failure_summary: string;
      impact?: string;
    }[];
  }[];
  focus_path?: {
    tag: string;
    id: string;
    x: number;
    y: number;
    text: string;
  }[];
}

export default function Insights() {
  const { audit_id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<AuditDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('all');

  useEffect(() => {
    client.get(`/audits/${audit_id}`)
      .then(res => {
        setData(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [audit_id]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-background" aria-live="polite">
      <Loader2 className="animate-spin text-primary" size={48} aria-label="Parsing heuristic findings..." />
    </div>
  );

  if (!data) return (
    <div className="min-h-screen flex flex-col items-center justify-center text-on-surface bg-background">
      <ShieldAlert size={48} className="text-error mb-4" />
      <p className="font-bold">Failed to load target insights.</p>
      <button onClick={() => navigate('/dashboard')} className="secondary-btn mt-4">Back to Dashboard</button>
    </div>
  );

  // Group duplicate violations to prevent duplicate React keys and compute occurrences
  const groupedViolationsMap = data.violations.reduce((acc, v) => {
    const key = v.id || `${v.rule_id}-${v.target || ''}`;
    if (!acc[key]) {
      acc[key] = {
        ...v,
        occurrences: v.occurrences || 1
      };
    } else {
      acc[key].occurrences = (acc[key].occurrences || 1) + (v.occurrences || 1);
    }
    return acc;
  }, {} as Record<string, typeof data.violations[0]>);

  const violationsList = Object.values(groupedViolationsMap);

  let totalOccurrences = 0;
  let criticalCount = 0;
  let seriousCount = 0;
  let moderateCount = 0;
  let minorCount = 0;

  violationsList.forEach(v => {
    if (v.nodes && v.nodes.length > 0) {
      v.nodes.forEach((node: any) => {
        totalOccurrences++;
        const imp = (node.impact || v.impact || '').toLowerCase();
        if (imp === 'critical') criticalCount++;
        else if (imp === 'serious' || imp === 'major') seriousCount++;
        else if (imp === 'moderate') moderateCount++;
        else if (imp === 'minor') minorCount++;
      });
    } else {
      totalOccurrences++;
      const imp = (v.impact || '').toLowerCase();
      if (imp === 'critical') criticalCount++;
      else if (imp === 'serious' || imp === 'major') seriousCount++;
      else if (imp === 'moderate') moderateCount++;
      else if (imp === 'minor') minorCount++;
    }
  });

  const filteredViolations = violationsList.filter(v => {
    return severityFilter === 'all' || v.impact.toLowerCase() === severityFilter.toLowerCase();
  });

  const focusPathNodes = (data.focus_path || []).map((node, index, arr) => {
    let focusState: 'valid' | 'trap-warning' | 'broken' = 'valid';
    
    // Check for Keyboard Trap (Consecutive duplicates in tag and text/id)
    if (index > 0) {
      const prev = arr[index - 1];
      if (prev.tag === node.tag && prev.id === node.id && prev.text === node.text) {
        focusState = 'broken';
      }
    }
    
    // Check for Focus Loop (element tag/text matches an earlier index in the chain)
    if (focusState === 'valid') {
      for (let j = 0; j < index; j++) {
        const earlier = arr[j];
        if (earlier.tag === node.tag && earlier.id === node.id && earlier.text === node.text) {
          focusState = 'trap-warning';
          break;
        }
      }
    }
    
    const label = node.text ? node.text.trim().substring(0, 30) : (node.id ? `#${node.id}` : `<${node.tag.toLowerCase()}>`);
    return {
      id: index + 1,
      label: label || 'Interactive Element',
      role: node.tag.toLowerCase(),
      focus: focusState
    };
  });

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 pb-32 min-h-screen">
      {/* Header */}
      <header className="mb-10 border-b border-surface-border pb-8">
        <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors mb-6 text-sm font-bold focus:ring-2 focus:ring-primary outline-none">
          <ArrowLeft size={16} aria-hidden="true" /> Back to Dashboard
        </button>
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div>
            <h1 className="text-3xl font-heading font-bold text-on-surface truncate max-w-xl">{data.url}</h1>
            <p className="text-on-surface-variant mt-2 text-sm">Full accessibility breakdown and AST remediation fixes.</p>
            <div className="flex flex-wrap gap-x-6 gap-y-2 mt-4 text-xs font-mono text-on-surface-variant">
              <div>
                <span className="text-on-surface-variant/70 font-bold uppercase">Status:</span>{' '}
                <span className="font-bold text-on-surface capitalize">{data.status}</span>
              </div>
              <div className="md:border-l md:border-surface-border md:pl-6">
                <span className="text-on-surface-variant/70 font-bold uppercase">Scan Executed:</span>{' '}
                <span className="font-bold text-on-surface">
                  {new Date(data.date).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}
                </span>
              </div>
            </div>
          </div>
          <div className="flex gap-3 shrink-0">
            <button
              onClick={() => navigate(`/audits/${data.id}/graph-insights`)}
              className="secondary-btn border-primary/50 text-primary hover:bg-primary hover:text-background flex items-center gap-2"
            >
              <Network size={14} /> Traverse Component Graph
            </button>
            <button
              onClick={() => {
                const apiBase = client.defaults.baseURL || 'http://localhost:8000/api';
                window.open(`${apiBase}/reports/${data.id}/download`, '_blank');
              }}
              className="primary-btn flex items-center gap-2"
            >
              <Download size={14} /> Download PDF
            </button>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-10">
        <div className="glass-panel p-4 border-t-4 border-t-primary flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Total Findings</span>
            <span data-testid="total-violations" className="text-2xl font-heading font-bold text-primary mt-1 block">{totalOccurrences}</span>
          </div>
        </div>
        <div className="glass-panel p-4 border-t-4 border-t-error flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Critical</span>
            <span data-testid="critical-bugs" className="text-2xl font-heading font-bold text-error mt-1 block">{criticalCount}</span>
          </div>
        </div>
        <div className="glass-panel p-4 border-t-4 border-t-warning flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Serious</span>
            <span className="text-2xl font-heading font-bold text-warning mt-1 block">{seriousCount}</span>
          </div>
        </div>
        <div className="glass-panel p-4 border-t-4 border-t-secondary flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Moderate</span>
            <span className="text-2xl font-heading font-bold text-secondary mt-1 block">{moderateCount}</span>
          </div>
        </div>
        <div className="glass-panel p-4 border-t-4 border-t-on-surface-variant flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Minor</span>
            <span className="text-2xl font-heading font-bold text-on-surface-variant mt-1 block">{minorCount}</span>
          </div>
        </div>
      </div>

      {/* Interactive Keyboard Focus Traversal Map */}
      <section aria-labelledby="focus-map-title" className="mb-10">
        <div className="flex justify-between items-center mb-4">
          <h2 id="focus-map-title" className="text-xl font-heading font-bold text-on-surface">Keyboard Navigation Sequence Map</h2>
          <span className="text-[10px] uppercase tracking-widest font-bold text-secondary">Tab Index Focus Chain</span>
        </div>
        <div className="glass-panel p-6 bg-surface-container-low border-t-2 border-t-secondary">
          <p className="text-xs text-on-surface-variant mb-6 leading-relaxed">
            Visual map representing sequential keyboard Focus vectors (tab order hierarchy). Highlights where lack of semantic ordering or focus traps are detected.
          </p>
          {focusPathNodes.length > 0 ? (
            <div className="flex flex-wrap items-center gap-3 p-4 bg-background rounded-md border border-surface-border/50 overflow-x-auto min-h-[100px]">
              {focusPathNodes.map((node, i, arr) => (
                <div key={node.id} className="flex items-center gap-2">
                  <div className={`flex flex-col p-3 rounded border text-[11px] font-mono min-w-[130px] transition-all shadow-ambient ${
                    node.focus === 'valid' ? 'border-primary/30 bg-primary/5 text-on-surface' :
                    node.focus === 'trap-warning' ? 'border-warning/50 bg-warning/10 text-warning' :
                    'border-error/50 bg-error/10 text-error'
                  }`}>
                    <div className="flex justify-between items-center mb-1 text-[9px] uppercase tracking-wider text-on-surface-variant font-bold">
                      <span>Node #{node.id}</span>
                      <span className="opacity-80">[{node.role}]</span>
                    </div>
                    <span className="font-semibold truncate">{node.label}</span>
                    <span className="text-[8px] uppercase tracking-wide mt-1.5 opacity-80 font-bold">
                      {node.focus === 'valid' ? 'Standard Focus' : node.focus === 'trap-warning' ? 'Focus Loop Warn' : 'Keyboard Trap'}
                    </span>
                  </div>
                  {i < arr.length - 1 && (
                    <span className="text-on-surface-variant font-mono font-bold text-sm">➔</span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center p-8 bg-background rounded-md border border-surface-border/50 text-xs text-on-surface-variant italic">
              No keyboard focus path telemetry recorded for this audit.
            </div>
          )}
        </div>
      </section>

      {/* Findings deck */}
      <div className="space-y-6">
        <div className="flex justify-between items-center border-b border-surface-border/50 pb-4">
          <h2 className="text-lg font-heading font-bold text-on-surface">Forensic Findings Ledger</h2>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Filter Impact:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-background text-on-surface border border-surface-border rounded px-2 py-1 text-xs focus:ring-1 focus:ring-primary focus:outline-none"
            >
              <option value="all">All Findings</option>
              <option value="critical">Critical</option>
              <option value="serious">Serious</option>
              <option value="moderate">Moderate</option>
              <option value="minor">Minor</option>
            </select>
          </div>
        </div>

        {filteredViolations.length > 0 ? (
          <div className="grid grid-cols-1 gap-4">
            {filteredViolations.map((v) => (
              <Link
                key={v.id}
                to={`/insights/${data.id}/violations/${v.id}`}
                className="flat-panel p-5 hover:border-primary/50 hover:bg-surface-highlight/30 transition-all flex justify-between items-center group outline-none focus:border-primary"
              >
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <span className={`text-[10px] uppercase font-extrabold px-2.5 py-0.5 rounded-full border ${
                      v.impact === 'critical' ? 'bg-error/15 text-error border-error/30' :
                      v.impact === 'serious' ? 'bg-warning/15 text-warning border-warning/30' : 'bg-primary/10 text-primary border-primary/20'
                    }`}>
                      {v.impact}
                    </span>
                    <span className="font-mono text-xs text-on-surface-variant">Occurrences: <strong className="text-on-surface">{v.occurrences}</strong></span>
                  </div>
                  <h3 className="font-heading font-bold text-sm text-on-surface group-hover:text-primary transition-colors">{v.rule_id}</h3>
                  <p className="text-xs text-on-surface-variant max-w-3xl leading-relaxed">{v.description}</p>
                </div>
                <ChevronRight size={20} className="text-on-surface-variant group-hover:text-primary transition-colors shrink-0" />
              </Link>
            ))}
          </div>
        ) : (
          <div className="p-16 text-center text-on-surface-variant flex flex-col items-center justify-center">
            <p className="text-sm">No violations registered matching filter.</p>
          </div>
        )}
      </div>
    </div>
  );
}
