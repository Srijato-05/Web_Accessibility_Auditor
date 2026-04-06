import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { client } from '../api/client';
import { ArrowLeft, Network, AlertTriangle, Layers, Combine, Zap, ShieldCheck, Loader2, CheckCircle2 } from 'lucide-react';

interface GraphData {
  impact_probability: string;
  top_node: string;
  component_id: string;
  reach: number;
  violations_prevented: number;
  structural_complexity: string;
  recommended: boolean;
  specific_fix: string;
}

export default function GraphInsights() {
  const { audit_id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<GraphData | null>(null);
  const [isFixing, setIsFixing] = useState(false);
  const [isResolved, setIsResolved] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  useEffect(() => {
    client.get(`/audits/${audit_id}/graph-insights`)
      .then(res => setData(res.data))
      .catch(console.error);
  }, [audit_id]);

  const handleFix = async () => {
    if (!data) return;
    setIsFixing(true);
    try {
      const resp = await client.post('/graph/fix', { 
        top_node: data.top_node, 
        component_id: data.component_id 
      });
      if (resp.data.message) {
         setToastMsg(`${resp.data.message} - ${resp.data.patched_component || 'Global Fragment'}`);
         setTimeout(() => setToastMsg(null), 5000);
      }
      setIsResolved(true);
    } catch(e) {
      console.error(e);
    }
    setIsFixing(false);
  }

  if (!data) return <div className="min-h-screen bg-background flex items-center justify-center text-on-surface"><Loader2 className="animate-spin text-primary" size={48} /></div>;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 pb-32 relative">
      {toastMsg && (
        <div className="fixed top-8 left-1/2 -translate-x-1/2 bg-surface text-primary border border-surface-border px-6 py-3 rounded-md shadow-flat z-50 font-bold tracking-widest flex items-center gap-3 uppercase text-sm">
           <Zap size={18} /> {toastMsg}
        </div>
      )}
      <header className="mb-8 border-b border-surface-border pb-8">
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors mb-6 text-sm font-bold">
           <ArrowLeft size={16} /> Back
        </button>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
           <div>
               <div className="flex items-center gap-3 mb-2">
                  <div className="bg-primary/10 text-primary p-2 rounded-md border border-primary/20">
                     <Network size={24} />
                  </div>
                  <h1 className="text-3xl font-heading font-bold">Graph Insights</h1>
               </div>
               <p className="text-on-surface-variant text-sm mt-2">Blast radius traversal mapping the structural dependencies of this component.</p>
           </div>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
         {/* Top Node */}
         <div className="flat-panel p-6">
            <div className="flex items-center gap-3 mb-4">
               <Layers className="text-secondary" size={20} />
               <h3 className="font-bold text-sm tracking-widest uppercase text-on-surface-variant">Top Node</h3>
            </div>
            <p className="text-2xl font-heading mb-1 font-bold text-on-surface truncate">{data.top_node}</p>
         </div>

         {/* Reach */}
         <div className="flat-panel p-6">
            <div className="flex items-center gap-3 mb-4">
               <Combine className="text-primary" size={20} />
               <h3 className="font-bold text-sm tracking-widest uppercase text-on-surface-variant">Affected Pages</h3>
            </div>
            <p className="text-2xl font-heading mb-1 font-bold text-on-surface">{data.reach} Pages</p>
         </div>

         {/* Impact Probability */}
         <div className={`flat-panel p-6 transition-all duration-700 ${isResolved ? 'border-secondary/30' : 'border-error/30'}`}>
            <div className="flex items-center gap-3 mb-4">
               {isResolved ? <ShieldCheck className="text-secondary" size={20} /> : <AlertTriangle className="text-error" size={20} />}
               <h3 className={`font-bold text-sm tracking-widest uppercase transition-colors ${isResolved ? 'text-secondary' : 'text-error'}`}>Impact Prob.</h3>
            </div>
            <p className={`text-2xl font-heading mb-1 font-bold transition-colors ${isResolved ? 'text-secondary' : 'text-error'}`}>{isResolved ? 'Stable' : data.impact_probability}</p>
         </div>

         {/* Violations Prevented */}
         <div className={`flat-panel p-6 transition-all duration-700 ${isResolved ? 'border-secondary/80 bg-secondary/10' : 'border-secondary/30 bg-secondary/5'}`}>
            <div className="flex items-center gap-3 mb-4">
               <ShieldCheck className={`transition-colors ${isResolved ? 'text-secondary' : 'text-secondary/80'}`} size={20} />
               <h3 className={`font-bold text-sm tracking-widest uppercase transition-colors ${isResolved ? 'text-secondary' : 'text-secondary/80'}`}>A11y Fixed</h3>
            </div>
            <div className={`flex items-center gap-3 text-2xl font-heading font-bold mb-1 transition-colors ${isResolved ? 'text-secondary' : 'text-secondary/80'}`}>
               ~{data.violations_prevented} {isResolved && <CheckCircle2 size={24} />}
            </div>
         </div>
      </div>

      {/* Structural Auto Remediation */}
      <div className="flat-panel p-8 border-primary/20 bg-surface-highlight max-w-5xl mx-auto">
         <div className="flex justify-between items-start mb-6">
            <div>
               <h2 className="text-sm text-on-surface-variant uppercase tracking-widest font-bold flex items-center gap-2 mb-2">
                  <Zap size={18} className="text-primary" /> Structural Auto-Remediation
               </h2>
               <p className="text-on-surface-variant text-sm max-w-2xl leading-relaxed mt-2">
                  By patching the <strong>{data.top_node}</strong> component directly, the layout engine can propagate this fix across <strong>{data.reach}</strong> interconnected routes automatically based on graph traversal dependencies.
               </p>
            </div>
            <div className="flex gap-2">
               {data.recommended && <span className="text-xs bg-secondary/10 text-secondary border border-secondary/20 px-3 py-1 rounded-full uppercase tracking-widest font-bold">Recommended</span>}
            </div>
         </div>
         
         <div className="p-6 bg-[#111111] rounded-md border border-surface-border mb-6 text-sm text-on-surface-variant font-mono relative overflow-hidden">
            <p className="mb-3 text-[#E0E0E0]"><span className="text-secondary font-bold mr-2">{'>'} Vertex</span> <span className="bg-secondary/10 text-secondary px-2 py-0.5 rounded border border-secondary/20">{data.component_id}</span></p>
            <p className="mb-2"><span className="text-primary font-bold mr-2">{'>'} Traverse</span> MATCH (n:Component)-[:PAGE_HAS_COMPONENT]-(p:Page)</p>
            <p className="mb-4"><span className="text-primary font-bold mr-2">{'>'} Analyze</span> Found <span className="text-white font-bold">{data.reach}</span> inherited route layout dependencies triggering <span className="text-white font-bold">{data.violations_prevented}</span> downstream WCAG faults.</p>
            <p className="opacity-70 pt-3 border-t border-surface-border"><span className="text-primary font-bold mr-2">{'>'} Prepare</span> Awaiting patch instruction set targeting Component boundary.</p>
         </div>

         <button 
               onClick={handleFix}
               disabled={isFixing || isResolved}
               className={`primary-btn w-full flex justify-center items-center gap-2 py-4 z-10 cursor-pointer transition-all disabled:opacity-50 disabled:cursor-not-allowed ${isResolved ? 'bg-secondary border-secondary text-background hover:bg-secondary hover:text-background' : ''}`}>
               {isFixing ? <><Loader2 className="animate-spin" /> Resolving Subgraphs...</> : 
                isResolved ? <><ShieldCheck size={20} /> Graph Successfully Patched</> : "Execute Global Remediation"}
         </button>
      </div>

      {isResolved && (
        <div className="max-w-5xl mx-auto mt-8 flex flex-col gap-6">
          <div className="flat-panel p-6 border-secondary/30 bg-surface">
             <h2 className="text-xs uppercase tracking-widest text-on-surface-variant font-bold mb-4">Security Audit Log</h2>
             <div className="bg-surface-highlight p-4 rounded border border-surface-border flex items-center justify-between">
                <div className="flex items-center gap-4">
                   <div className="bg-secondary/10 p-2 text-secondary rounded">
                      <CheckCircle2 size={18} />
                   </div>
                   <div>
                      <p className="font-medium text-secondary text-sm">Global Patch Applied to {data.top_node} — {data.violations_prevented} Issues Resolved.</p>
                      <p className="text-xs text-on-surface-variant mt-1 font-mono tracking-widest">HASH_CHAIN: {audit_id}</p>
                   </div>
                </div>
                <span className="text-xs text-on-surface-variant tracking-widest border border-surface-border bg-surface px-2 py-1 rounded font-bold">JUST NOW</span>
             </div>
          </div>
          
          <div className="flex justify-end">
             <button onClick={() => navigate('/dashboard')} className="secondary-btn flex items-center gap-2 border-secondary/50 text-secondary hover:bg-secondary hover:text-white cursor-pointer text-sm">
                View Updated Dashboard <ArrowLeft size={16} className="rotate-180" />
             </button>
          </div>
        </div>
      )}

    </div>
  )
}
