import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { client } from '../api/client.ts';
import { Loader2, Activity, ShieldAlert } from 'lucide-react';

export default function AuditReport() {
  const { audit_id } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('initializing');
  const [url, setUrl] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    let interval: any;
    
    const checkStatus = () => {
      client.get(`/audits/${audit_id}`)
        .then(res => {
          setUrl(res.data.url);
          if (res.data.status === 'completed') {
            setStatus('completed');
            clearInterval(interval);
            navigate(`/insights/${audit_id}`);
          } else if (res.data.status === 'failed') {
            setStatus('error');
            setErrorMsg(res.data.error_message || 'The scan failed due to a browser execution anomaly.');
            clearInterval(interval);
          } else {
            setStatus('scanning');
            // Mock scanner tracking updates to simulate real-time CLI output
            const mockLogs = [
              `[SYSTEM] Connecting to target ${res.data.url}`,
              `[CRAWLER] Traversing depth limits...`,
              `[AUDITOR] Executing Axe-Core heuristics rules...`,
              `[DATABASE] Writing subgraphs index nodes...`
            ];
            setLogs(mockLogs);
          }
        })
        .catch(err => {
          console.error(err);
          setStatus('error');
          clearInterval(interval);
        });
    };

    checkStatus();
    interval = setInterval(checkStatus, 3000);

    return () => clearInterval(interval);
  }, [audit_id, navigate]);

  return (
    <div className="max-w-4xl mx-auto px-6 py-20 pb-32 flex flex-col justify-center min-h-screen fade-in-up">
      <div className="glass-panel p-10 relative overflow-hidden border-t-4 border-t-primary">
         {/* Futuristic Scanning animation bar */}
         <div className="scan-line"></div>

         <div className="flex items-center gap-3 mb-6">
            <div className="bg-primary/10 text-primary p-2.5 rounded-md border border-primary/20 animate-pulse">
               <Activity size={24} />
            </div>
            <div>
               <h1 className="text-2xl font-heading font-bold text-on-surface">Compliance Scanning Console</h1>
               <span className="text-[10px] uppercase font-mono tracking-widest text-primary font-bold">Scanning Vector: {url}</span>
            </div>
         </div>

         {status === 'error' ? (
            <div className="p-4 bg-error/15 border border-error/30 text-error rounded text-xs flex items-center gap-2 mb-6" role="alert">
               <ShieldAlert size={16} /> {errorMsg || 'Error traversing target node list. Ensure target server is responsive.'}
            </div>
         ) : (
            <div className="flex items-center gap-3 text-xs text-on-surface mb-8 bg-surface-highlight/50 p-4 rounded border border-surface-border">
               <Loader2 className="animate-spin text-primary shrink-0" size={16} />
               <span>Executing deep accessibility heuristics... Please do not terminate secure connection session.</span>
            </div>
         )}

         {/* Console Logs Deck */}
         <div className="bg-black/80 rounded border border-surface-border p-5 text-xs text-on-surface-variant font-mono space-y-2 max-h-60 overflow-y-auto">
            {logs.map((log, idx) => (
               <div key={idx} className="flex gap-2">
                  <span className="text-primary font-bold">{`>`}</span>
                  <span className="text-on-surface-variant select-all">{log}</span>
               </div>
            ))}
            <div className="flex gap-2 text-primary animate-pulse">
               <span>{`>`}</span>
               <span>Awaiting pipeline feedback logs...</span>
            </div>
         </div>
      </div>
    </div>
  );
}
