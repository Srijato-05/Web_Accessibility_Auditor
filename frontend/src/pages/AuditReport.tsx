import { useEffect, useState } from 'react';
import { client } from '../api/client';
import { Target, Bug, FileCode2, ArrowLeft } from 'lucide-react';

export default function AuditReport() {
  const [session, setSession] = useState<any>(null);

  // Hardcode ID from mock data for prototyping
  const sessionId = "12345678-1234-5678-1234-567812345678";

  useEffect(() => {
    client.get(`/sessions/${sessionId}`)
      .then(res => setSession(res.data))
      .catch(console.error);
  }, []);

  if (!session) return <div className="p-8 text-on-surface-variant">Decrypting session data...</div>;

  return (
    <div className="min-h-screen bg-surface-dim p-8">
      {/* Header */}
      <div className="mb-8">
        <button className="secondary-btn flex items-center gap-2 mb-6">
          <ArrowLeft size={16} /> Return to Mission Control
        </button>
        <h1 className="text-4xl font-heading tracking-tight mb-2 flex items-center gap-3">
          <Target className="text-primary" /> {session.target_url}
        </h1>
        <p className="text-outline uppercase text-xs tracking-widest font-bold">
           Session {session.id} • Completed {new Date(session.completed_at).toLocaleString()}
        </p>
      </div>

      <div className="grid grid-cols-12 gap-8">
        {/* Core Content */}
        <section className="col-span-12 lg:col-span-8 flex flex-col gap-4">
           {session.violations.map((violation: any, idx: number) => (
             <div key={idx} className="bg-surface-container rounded-md ghost-border relative overflow-hidden">
                {/* Decorative border matching severity */}
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-error"></div>
                
                <div className="p-6 pl-8">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="font-heading text-xl text-on-surface tracking-tight mb-1">{violation.description}</h3>
                    <div className="bg-error-container/30 text-error px-3 py-1 rounded-full text-xs font-bold uppercase ring-1 ring-error/20 flex items-center gap-1">
                      <Bug size={14} /> {violation.impact}
                    </div>
                  </div>
                  
                  <div className="bg-surface-container-highest p-4 rounded text-sm text-outline-variant font-mono mb-4 ring-1 ring-white/5">
                    <div className="flex items-center gap-2 mb-2 text-on-surface-variant font-body text-xs font-bold uppercase tracking-wide">
                      <FileCode2 size={16}/> Dom Selector
                    </div>
                    {violation.selector}
                  </div>

                  <a href={violation.help_url} target="_blank" className="text-primary hover:text-primary-fixed hover:underline text-sm font-medium">
                    View Deque Documentation
                  </a>
                </div>
             </div>
           ))}
        </section>

        {/* Sidebar Info */}
        <section className="col-span-12 lg:col-span-4">
           <div className="glass-panel p-6 shadow-ambient">
             <h2 className="text-xl font-heading mb-4 text-on-surface">Forensic Metatdata</h2>
             <ul className="text-sm space-y-3 text-on-surface-variant">
               <li className="flex justify-between border-b border-outline-variant/15 pb-2">
                 <span>Status</span> <span className="text-secondary font-bold uppercase">{session.status}</span>
               </li>
               <li className="flex justify-between border-b border-outline-variant/15 pb-2">
                 <span>Violations</span> <span className="text-error font-bold">{session.violations.length} Criticals</span>
               </li>
               <li className="flex justify-between border-b border-outline-variant/15 pb-2">
                 <span>Target Matrix</span> <span>WCAG 2.1 AA</span>
               </li>
             </ul>
           </div>
        </section>
      </div>
    </div>
  );
}
