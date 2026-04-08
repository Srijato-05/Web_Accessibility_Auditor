import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { client } from '../api/client';
import { Activity, Bug, AlertTriangle, Info, Play, Loader2, ArrowRight, Download } from 'lucide-react';
import { GraphView } from '../components/GraphView';

interface DashboardSummary {
  health_score: number;
  rating: string;
  issues: {
    critical: number;
    major: number;
    minor: number;
  };
  recent_scans: {
    id: string;
    url: string;
    score: number;
    status: string;
    date: string;
  }[];
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    client.get('/dashboard/summary')
      .then(res => setSummary(res.data))
      .catch(e => {
        console.error(e);
        setSummary({ health_score: 0, rating: "-", issues: { critical: 0, major: 0, minor: 0 }, recent_scans: [] });
      });
  }, []);

  if (!summary) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="animate-spin text-primary" size={48} />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 pb-32">
       <header className="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-surface-border pb-8">
          <div>
              <h1 className="text-3xl font-heading font-bold text-on-surface">Dashboard</h1>
              <p className="text-on-surface-variant mt-2 text-sm">Overview of tracking application status and health.</p>
          </div>
          <div>
             <button onClick={() => navigate('/scan')} className="primary-btn flex items-center gap-2 relative">
                <Play size={16} className="fill-current" /> New Scan
             </button>
          </div>
       </header>

       <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
          <div className="flat-panel p-6 flex flex-col justify-center items-center relative text-center">
             <div className="absolute top-2 right-2 bg-surface-highlight text-on-surface-variant px-2 py-1 rounded text-[10px] font-bold tracking-widest">{summary.rating}</div>
             <h2 className="text-xs uppercase tracking-widest font-bold text-on-surface-variant mb-4">Health Score</h2>
             <span className="text-5xl font-heading font-bold text-on-surface mt-2">{summary.health_score}</span>
             <p className="text-xs font-medium text-on-surface-variant mt-4">{summary.health_score >= 80 ? 'Optimal' : summary.health_score >= 60 ? 'Needs Attention' : 'Critical'}</p>
          </div>

          <div className="flat-panel p-6 flex flex-col">
             <div className="flex items-center gap-2 mb-4">
                <Bug className="text-error" size={20} />
                <h2 className="text-xs uppercase tracking-widest font-bold text-on-surface-variant">Critical Issues</h2>
             </div>
             <span className="text-4xl font-heading font-bold text-on-surface mt-auto">{summary.issues.critical}</span>
          </div>

          <div className="flat-panel p-6 flex flex-col">
             <div className="flex items-center gap-2 mb-4">
                <AlertTriangle className="text-warning" size={20} />
                <h2 className="text-xs uppercase tracking-widest font-bold text-on-surface-variant">Major Issues</h2>
             </div>
             <span className="text-4xl font-heading font-bold text-on-surface mt-auto">{summary.issues.major}</span>
          </div>

          <div className="flat-panel p-6 flex flex-col">
             <div className="flex items-center gap-2 mb-4">
                <Info className="text-secondary" size={20} />
                <h2 className="text-xs uppercase tracking-widest font-bold text-on-surface-variant">Minor Issues</h2>
             </div>
             <span className="text-4xl font-heading font-bold text-on-surface mt-auto">{summary.issues.minor}</span>
          </div>
       </div>

       <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="col-span-1 lg:col-span-2 space-y-4">
               <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-bold text-on-surface">Recent Scans</h2>
                  <button onClick={() => navigate('/history')} className="text-primary text-sm font-medium hover:underline flex items-center gap-1">
                     View History <ArrowRight size={14} />
                  </button>
               </div>
               <div className="flat-panel overflow-hidden">
                  {summary.recent_scans.length > 0 ? (
                    <table className="w-full text-left">
                      <thead>
                        <tr className="border-b border-surface-border bg-surface-highlight text-xs uppercase tracking-wider text-on-surface-variant font-bold">
                          <th className="px-6 py-3">Target</th>
                          <th className="px-6 py-3 text-center">Score</th>
                          <th className="px-6 py-3 text-center">PDF</th>
                          <th className="px-6 py-3 text-right">Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {summary.recent_scans.map((log) => (
                          <tr key={log.id} onClick={() => navigate('/insights/' + log.id)} className="border-b border-surface-border hover:bg-surface-highlight cursor-pointer transition-colors last:border-b-0 group">
                            <td className="px-6 py-4 text-sm font-medium text-on-surface group-hover:text-primary transition-colors">{log.url}</td>
                            <td className="px-6 py-4 text-center">
                              <span className="text-sm font-mono font-bold text-on-surface">{log.score}</span>
                            </td>
                            <td className="px-6 py-4 text-center">
                                <button 
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    window.location.href = `http://localhost:8000/api/reports/${log.id}/download`;
                                  }}
                                  className="p-2 hover:bg-primary/10 rounded-full text-on-surface-variant hover:text-primary transition-all group/btn"
                                  title="Download Remediation PDF"
                                >
                                  <Download size={14} />
                                </button>
                            </td>
                            <td className="px-6 py-4 text-right text-xs text-on-surface-variant">
                              {new Date(log.date).toLocaleString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                     <div className="p-12 text-center text-on-surface-variant flex flex-col items-center justify-center">
                        <Activity size={32} className="opacity-20 mb-4" />
                        <p className="text-sm">No analysis history available.</p>
                     </div>
                  )}
               </div>
            </div>

            <div className="col-span-1">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold text-on-surface">Compliance Graph</h2>
              </div>
              <div className="flat-panel p-4 h-[350px] flex items-center justify-center overflow-hidden">
                {summary.recent_scans.length > 0 ? (
                   <GraphView />
                ) : (
                  <p className="text-xs text-on-surface-variant uppercase tracking-widest font-bold">Awaiting Data</p>
                )}
              </div>
            </div>
       </div>
    </div>
  )
}
