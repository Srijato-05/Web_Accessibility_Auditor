import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { client } from '../api/client';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ArrowLeft, AlertTriangle, Loader2, GitMerge } from 'lucide-react';

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

  if (!data) return <div className="min-h-screen flex items-center justify-center text-on-surface bg-background"><Loader2 className="animate-spin text-primary" size={48} /></div>;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 pb-32">
      <header className="mb-8 border-b border-surface-border pb-8">
        <button onClick={() => navigate(`/insights/${audit_id || 'global'}`)} className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors mb-6 text-sm font-bold">
           <ArrowLeft size={16} /> Back
        </button>
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
           <div>
               <div className="flex items-center gap-3 mb-2">
                  <div className="bg-error-bg text-error p-2 rounded-md border border-error/20">
                     <AlertTriangle size={24} />
                  </div>
                  <h1 className="text-3xl font-heading font-bold capitalize text-on-surface">{data.rule_id}</h1>
               </div>
               <p className="text-on-surface-variant mt-2 max-w-2xl text-sm leading-relaxed">{data.description}</p>
           </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         {/* Technical Root Cause */}
         <div className="flat-panel p-6 col-span-1 border-error/50">
            <h2 className="text-sm text-on-surface-variant uppercase tracking-widest font-bold mb-6">Technical Root Cause</h2>
            
            <div className="flex items-center gap-8 mb-8 mt-2">
               <div className="flex flex-col">
                  <span className="text-5xl font-heading font-bold text-error">{data.impact_score}<span className="text-2xl text-on-surface-variant">/10</span></span>
                  <span className="text-xs uppercase tracking-widest text-on-surface-variant mt-2 font-bold">Impact Score</span>
               </div>
               <div className="h-16 w-px bg-surface-border"></div>
               <div className="flex flex-col">
                  <span className="text-5xl font-heading font-bold text-on-surface">{data.occurrences}</span>
                  <span className="text-xs uppercase tracking-widest text-on-surface-variant mt-2 font-bold">Occurrences</span>
               </div>
            </div>

            <div className="space-y-4 text-sm bg-surface-highlight p-4 rounded-md border border-surface-border mt-auto">
               <div>
                  <span className="text-primary font-bold block mb-1">DOM Target</span>
                  <code className="bg-surface px-2 py-1 rounded text-xs block text-on-surface-variant whitespace-pre-wrap border border-surface-border">{data.selector}</code>
               </div>
               <div>
                  <span className="text-primary font-bold block mb-1">Documentation</span>
                  <a href={data.help_url} target="_blank" rel="noreferrer" className="text-primary hover:underline block truncate break-all bg-surface border border-surface-border px-2 py-1 rounded text-xs">{data.help_url}</a>
               </div>
            </div>
         </div>

         {/* Code Comparison */}
         <div className="flat-panel p-6 col-span-1 lg:col-span-2 flex flex-col h-full">
            <h2 className="text-sm text-on-surface-variant uppercase tracking-widest font-bold mb-6 flex items-center gap-2"><GitMerge size={16} className="text-primary"/> Code Comparison</h2>
            
            <div className="space-y-6 flex-1">
               <div className="relative border border-surface-border rounded-md overflow-hidden bg-[#1E1E1E] shadow-flat">
                  <div className="absolute top-0 left-0 bg-error/20 text-error text-xs font-bold uppercase tracking-widest px-3 py-1 rounded-br-md z-10 border-b border-r border-[#1E1E1E]">Issue Context</div>
                  <SyntaxHighlighter language="html" style={vscDarkPlus} customStyle={{margin: 0, padding: '2.5rem 1rem 1rem 1rem', background: 'transparent', fontSize: '13px'}} wrapLongLines={true}>
                     {data.current_fragment}
                  </SyntaxHighlighter>
               </div>

               <div className="relative border border-secondary/50 rounded-md overflow-hidden bg-[#1E1E1E] shadow-flat">
                  <div className="absolute top-0 left-0 bg-secondary/20 text-secondary text-xs font-bold uppercase tracking-widest px-3 py-1 rounded-br-md z-10 border-b border-r border-[#1E1E1E]">Suggested Pattern</div>
                  <SyntaxHighlighter language="html" style={vscDarkPlus} customStyle={{margin: 0, padding: '2.5rem 1rem 1rem 1rem', background: 'transparent', fontSize: '13px'}} wrapLongLines={true}>
                     {data.suggested_fix}
                  </SyntaxHighlighter>
               </div>
            </div>
         </div>
      </div>
    </div>
  )
}
