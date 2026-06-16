import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { client } from '../api/client.ts';
import { ArrowLeft, Loader2, GitMerge } from 'lucide-react';

interface ViolationDetail {
  id: string;
  rule_id: string;
  impact: string;
  description: string;
  help_url: string;
  impact_score: number;
  occurrences: number;
  selector: string;
  current_fragment: string;
  suggested_fix: string;
  confidence_score?: number;
  verification_status?: string;
}

export default function IssueDetail() {
  const { audit_id, violation_id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<ViolationDetail | null>(null);

  useEffect(() => {
    client.get(`/violations/${violation_id}`)
      .then(res => setData(res.data))
      .catch(console.error);
  }, [violation_id]);

  if (!data) return <div className="min-h-screen flex items-center justify-center text-on-surface bg-background"><Loader2 className="animate-spin text-primary" size={48} aria-label="Loading violation source..." /></div>;

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 pb-32 min-h-screen fade-in-up">
      <header className="mb-8 border-b border-surface-border pb-8">
        <button onClick={() => navigate(`/insights/${audit_id || 'global'}`)} className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors mb-6 text-sm font-bold focus:ring-2 focus:ring-primary outline-none">
           <ArrowLeft size={16} aria-hidden="true" /> Back to Insights
        </button>
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
           <div>
               <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-3xl font-heading font-bold capitalize text-on-surface">{data.rule_id}</h1>
               </div>
               <p className="text-on-surface-variant mt-2 max-w-2xl text-sm leading-relaxed">{data.description}</p>
           </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         {/* Technical Root Cause */}
         <div className="flat-panel p-6 col-span-1 border-error/50 flex flex-col justify-between">
            <div>
              <h2 className="text-sm text-on-surface-variant uppercase tracking-widest font-bold mb-6">Technical Root Cause</h2>
              
              <div className="flex items-center gap-8 mb-8 mt-2">
                 <div className="flex flex-col">
                    <span className="text-3xl font-heading font-bold text-error uppercase">{data.impact.toUpperCase()}</span>
                    <span className="text-xs uppercase tracking-widest text-on-surface-variant mt-2 font-bold">Severity Level</span>
                 </div>
                 <div className="h-16 w-px bg-surface-border"></div>
                 <div className="flex flex-col">
                    <span className="text-5xl font-heading font-bold text-on-surface">{data.occurrences}</span>
                    <span className="text-xs uppercase tracking-widest text-on-surface-variant mt-2 font-bold">Occurrences</span>
                 </div>
                 {data.confidence_score !== undefined && data.confidence_score !== null && (
                   <>
                     <div className="h-16 w-px bg-surface-border"></div>
                     <div className="flex flex-col">
                        <span className="text-3xl font-heading font-mono font-bold text-primary">{(data.confidence_score * 100).toFixed(1)}%</span>
                        <span className="text-xs uppercase tracking-widest text-on-surface-variant mt-2 font-bold">AI Confidence</span>
                     </div>
                   </>
                 )}
                 {data.verification_status && data.verification_status !== 'unverified' && (
                   <>
                     <div className="h-16 w-px bg-surface-border"></div>
                     <div className="flex flex-col">
                        <span className={`text-xl font-heading font-bold uppercase ${data.verification_status === 'true_positive' ? 'text-[#38a169]' : 'text-error line-through'}`}>{data.verification_status.replace('_', ' ')}</span>
                        <span className="text-xs uppercase tracking-widest text-on-surface-variant mt-2 font-bold">Ground Truth</span>
                     </div>
                   </>
                 )}
              </div>
            </div>

            <div className="space-y-4 text-xs bg-surface-highlight p-4 rounded-md border border-surface-border mt-auto">
               <div>
                  <span className="text-primary font-bold block mb-1">DOM Target</span>
                  <code className="bg-surface px-2 py-1 rounded text-[10px] block text-on-surface-variant whitespace-pre-wrap border border-surface-border font-mono">{data.selector}</code>
               </div>
               <div>
                  <span className="text-primary font-bold block mb-1">Documentation</span>
                  <a href={data.help_url} target="_blank" rel="noreferrer" className="text-primary hover:underline block truncate break-all bg-surface border border-surface-border px-2 py-1 rounded text-[10px] font-mono">{data.help_url}</a>
               </div>
            </div>
         </div>

         {/* Code Comparison */}
         <div className="flat-panel p-6 col-span-1 lg:col-span-2 flex flex-col h-full">
            <h2 className="text-sm text-on-surface-variant uppercase tracking-widest font-bold mb-6 flex items-center gap-2"><GitMerge size={16} className="text-primary"/> Code Comparison</h2>
            
            <div className="space-y-6 flex-1">
               <div className="relative border border-surface-border rounded-md overflow-hidden bg-[#1E1E1E] shadow-flat">
                  <div className="absolute top-0 left-0 bg-error/20 text-error text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded-br-md z-10 border-b border-r border-[#1E1E1E]">Issue Context</div>
                  <pre className="font-mono text-xs text-on-surface p-6 pt-10 overflow-x-auto whitespace-pre-wrap bg-[#1E1E1E] leading-relaxed">
                    <code>{data.current_fragment}</code>
                  </pre>
               </div>

               <div className="relative border border-secondary/50 rounded-md overflow-hidden bg-[#1E1E1E] shadow-flat">
                  <div className="absolute top-0 left-0 bg-secondary/20 text-secondary text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded-br-md z-10 border-b border-r border-[#1E1E1E]">Suggested Pattern</div>
                  <pre className="font-mono text-xs text-primary p-6 pt-10 overflow-x-auto whitespace-pre-wrap bg-[#1E1E1E] leading-relaxed">
                    <code>{data.suggested_fix}</code>
                  </pre>
               </div>
            </div>
         </div>
      </div>
    </div>
  );
}
