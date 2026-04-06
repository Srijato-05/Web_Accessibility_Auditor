import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { client } from '../api/client';
import { PieChart, Bug, AlertTriangle, Info, ArrowLeft, CheckCircle2 } from 'lucide-react';

interface Violation {
  id: string;
  type: string;
  severity: string;
  message: string;
  category: string;
}

const ALL_CATEGORIES = ["Color & Contrast", "ARIA & Semantics", "Keyboard Navigation", "Structure"];

export default function Insights() {
  const [violations, setViolations] = useState<Violation[]>([]);
  const { audit_id } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    client.get(`/audits/${audit_id || 'global'}/violations`)
      .then(res => {
         setViolations(res.data);
      })
      .catch(console.error);
  }, [audit_id]);

  const criticalCount = violations.filter(v => v.severity === 'Critical').length;
  const majorCount = violations.filter(v => v.severity === 'Major').length;
  const minorCount = violations.filter(v => v.severity === 'Minor').length;

  const total = violations.length || 1;

  const criticalPct = (criticalCount / total) * 100;
  const majorPct = (majorCount / total) * 100;
  const minorPct = (minorCount / total) * 100;

  const impactIcon = (severity: string) => {
    if (severity === 'Critical') return <Bug size={16} className="text-error" />;
    if (severity === 'Major') return <AlertTriangle size={16} className="text-warning" />;
    return <Info size={16} className="text-secondary" />;
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
        <div className="flex items-center gap-3">
             <h1 className="text-3xl font-heading font-bold text-on-surface">Audit Insights</h1>
        </div>
        <p className="text-on-surface-variant mt-2 text-sm">Detailed vulnerability intelligence for audit {audit_id}</p>
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
                  <div className="flex justify-between items-center text-sm">
                     <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-error"></span> Critical</span>
                     <span className="font-heading font-medium">{criticalCount}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                     <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-warning"></span> Major</span>
                     <span className="font-heading font-medium">{majorCount}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                     <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-secondary"></span> Minor</span>
                     <span className="font-heading font-medium">{minorCount}</span>
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

      <div className="flat-panel overflow-hidden mt-8">
         <div className="p-6 border-b border-surface-border">
            <h2 className="text-lg font-bold text-on-surface">Violations Log</h2>
         </div>
         <div className="w-full p-6 space-y-8 bg-surface-highlight/30">
            {ALL_CATEGORIES.map(category => {
               const cats = violations.filter(v => v.category === category);
               
               if (cats.length === 0) {
                  return (
                     <div key={category} className="mb-2">
                        <h3 className="text-sm uppercase tracking-widest font-bold text-on-surface-variant mb-4">{category}</h3>
                        <div className="bg-surface rounded-md border border-surface-border p-4 flex items-center justify-between shadow-flat">
                           <div className="flex items-center gap-3">
                              <div className="bg-secondary/10 text-secondary p-2 rounded"><CheckCircle2 size={16} /></div>
                              <span className="text-on-surface-variant text-sm font-medium">Validation Passed (100% Compliant)</span>
                           </div>
                           <span className="text-secondary text-xs uppercase tracking-widest font-bold border border-secondary/20 px-2 py-1 rounded bg-secondary/5">CLEARED</span>
                        </div>
                     </div>
                  );
               }

               return (
                  <div key={category}>
                     <h3 className="text-sm uppercase tracking-widest font-bold text-on-surface-variant mb-4">{category}</h3>
                     <div className="space-y-3">
                        {cats.map((v, idx) => (
                           <div key={idx} className="bg-surface rounded-md border border-surface-border overflow-hidden group hover:border-primary/50 transition-all shadow-flat">
                              <div className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                                 <div className="flex items-start md:items-center gap-4">
                                    <div className={`p-2 rounded-md border flex-shrink-0 ${impactColor(v.severity)}`}>
                                       {impactIcon(v.severity)}
                                    </div>
                                    <div>
                                       <h3 className="font-medium text-on-surface mb-1">{v.type}</h3>
                                       <p className="text-sm text-on-surface-variant leading-relaxed tracking-wide">{v.message}</p>
                                    </div>
                                 </div>
                                 <button 
                                    onClick={() => navigate(`/insights/${audit_id || 'global'}/issue/${v.id}`)}
                                    className="text-xs font-bold uppercase tracking-widest text-primary md:opacity-0 group-hover:opacity-100 transition-all cursor-pointer bg-primary/10 px-4 py-2 rounded-md hover:bg-primary hover:text-on-primary flex-shrink-0 border border-primary/20">
                                    Investigate
                                 </button>
                              </div>
                           </div>
                        ))}
                     </div>
                  </div>
               );
            })}
         </div>
      </div>
    </div>
  );
}
