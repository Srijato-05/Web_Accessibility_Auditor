import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { client } from '../api/client';
import { PieChart, ArrowLeft, Download, Activity, Loader2 } from 'lucide-react';

interface Violation {
  id: string;
  type: string;
  severity: string;
  message: string;
  category: string;
}

// Forensic Categories decommissioned in favor of Advice Hub

export default function Insights() {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [recentScans, setRecentScans] = useState<any[]>([]);
  const { audit_id } = useParams();
  const navigate = useNavigate();
  const [regenerating, setRegenerating] = useState(false);
  const [sessionStatus, setSessionStatus] = useState<string>('loading');
  const [remediationPlan, setRemediationPlan] = useState<string>('');

  useEffect(() => {
    if (!audit_id) return;
    
    let interval: any;
    
    const fetchAllData = async () => {
      try {
        const res = await client.get(`/sessions/${audit_id}`);
        setSessionStatus(res.data.status);
        setRemediationPlan(res.data.remediation_plan || '');
        setViolations(res.data.violations || []);
        
        if (res.data.status === 'completed' || res.data.status === 'failed') {
          clearInterval(interval);
        }
      } catch (e) {
        console.error("Data fetch failed", e);
      }
    };

    const fetchSummary = () => {
       client.get('/dashboard/summary')
         .then(res => setRecentScans(res.data.recent_scans || []))
         .catch(e => console.error(e));
    };

    fetchAllData();
    fetchSummary();
    interval = setInterval(fetchAllData, 3000); 

    return () => clearInterval(interval);
  }, [audit_id]);

  const handleDownloadPDF = () => {
    window.open(`http://localhost:8000/api/reports/${audit_id}/download`, '_blank');
  };

  const handleRegenerate = async () => {
    if (regenerating) return;
    setRegenerating(true);
    try {
      await client.post(`/reports/${audit_id}/generate`);
      alert("Report regenerated successfully.");
    } catch (err) {
      console.error(err);
      alert("Report regeneration failed.");
    } finally {
      setRegenerating(false);
    }
  };

  const criticalCount = violations.filter(v => v.severity === 'Critical').length;
  const majorCount = violations.filter(v => v.severity === 'Major').length;
  const minorCount = violations.filter(v => v.severity === 'Minor').length;
  
  const agentCount = violations.filter(v => v.type && v.type.startsWith('AGENT-')).length;
  const standardCount = violations.length - agentCount;

  const total = violations.length || 1;

  const criticalPct = (criticalCount / total) * 100;
  const majorPct = (majorCount / total) * 100;
  const minorPct = (minorCount / total) * 100;

  const impactIcon = (_severity: string) => {
    return null;
  };

  const impactColor = (severity: string) => {
    if (severity === 'Critical') return 'text-error bg-error-bg border-error/50';
    if (severity === 'Major') return 'text-warning bg-warning-bg border-warning/50';
    return 'text-secondary border-secondary/50 bg-secondary/10';
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 pb-32">
      <header className="mb-10">
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors mb-6 text-sm font-bold">
           <ArrowLeft size={16} /> Back
        </button>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-3">
               <h1 className="text-3xl font-heading font-bold text-on-surface">Audit Insights</h1>
          </div>
          
          <div className="flex items-center gap-4">
             <button 
                onClick={handleRegenerate}
                disabled={regenerating}
                className="secondary-btn flex items-center gap-2 text-xs"
             >
                {regenerating ? <Loader2 size={14} className="animate-spin" /> : <Activity size={14} />}
                {regenerating ? 'Synthesizing...' : 'Regenerate'}
             </button>
             
             <button 
                onClick={handleDownloadPDF}
                className="primary-btn flex items-center gap-2 text-xs"
             >
                <Download size={14} /> Download PDF
             </button>
          </div>
        </div>
        <p className="text-on-surface-variant mt-2 text-sm">High-fidelity forensic report for session {audit_id}</p>
        
        {sessionStatus !== 'completed' && sessionStatus !== 'failed' && (
          <div className="mt-6 p-4 bg-primary/10 border border-primary/20 rounded-md flex items-center justify-between animate-pulse">
            <div className="flex items-center gap-3 text-primary">
              <Loader2 size={18} className="animate-spin" />
              <span className="text-sm font-bold uppercase tracking-widest">Mission Context: {sessionStatus.replace('_', ' ')}</span>
            </div>
            <span className="text-[10px] text-primary/70 font-mono">Engaging Specialized Forensic Agents...</span>
          </div>
        )}
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        {/* Severities */}
        <div className="flat-panel p-6 flex flex-col justify-between">
           <div>
               <h2 className="text-sm uppercase tracking-widest font-bold text-on-surface-variant mb-6">Severity Distribution</h2>
               
               <div className="flex w-full h-3 rounded-full overflow-hidden mb-6 bg-surface-highlight">
                  <div className="bg-error transition-all" style={{width: `${criticalPct}%`}}></div>
                  <div className="bg-warning transition-all" style={{width: `${majorPct}%`}}></div>
                  <div className="bg-secondary transition-all" style={{width: `${minorPct}%`}}></div>
               </div>
               
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-primary/10 border border-primary/30 rounded-lg">
                     <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full bg-primary animate-pulse"></div>
                        <span className="text-sm font-bold uppercase tracking-wider text-primary">Agentic Findings</span>
                     </div>
                     <span className="text-2xl font-heading font-bold text-primary">{agentCount}</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-4 bg-surface-highlight border border-surface-border rounded-lg">
                     <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full bg-on-surface-variant/40"></div>
                        <span className="text-sm font-bold uppercase tracking-wider text-on-surface-variant">Axe Engine findings</span>
                     </div>
                     <span className="text-2xl font-heading font-bold text-on-surface">{standardCount}</span>
                  </div>
               </div>
           </div>
        </div>

        {/* Total issues card */}
        <div className="flat-panel p-6 flex flex-col items-center justify-center text-center">
            <PieChart size={48} className="text-primary mb-4 opacity-50" />
            <h2 className="text-6xl font-heading font-bold text-on-surface mb-2">{violations.length}</h2>
            <p className="text-sm font-bold uppercase tracking-widest text-on-surface-variant">Total Issues Found</p>
        </div>
      </div>

      {/* Bottom section removed per user request */}
    </div>
  );
}
