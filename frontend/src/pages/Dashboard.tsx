import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { client } from '../api/client';
import { Activity, Play, Loader2, Download } from 'lucide-react';
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

       <div className="space-y-10">
          {/* Immersive Forensic Graph */}
          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-heading font-bold text-on-surface">Audit Network Visualization</h2>
              <div className="flex items-center gap-2">
                 <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
                 <span className="text-[10px] uppercase tracking-widest font-bold text-primary">Live Forensic Stream</span>
              </div>
            </div>
            <div className="flat-panel p-6 h-[500px] flex items-center justify-center overflow-hidden border-t-2 border-t-primary">
              {summary.recent_scans.length > 0 ? (
                 <GraphView />
              ) : (
                <div className="text-center">
                  <Activity size={48} className="mx-auto text-surface-highlight mb-4 opacity-20" />
                  <p className="text-xs text-on-surface-variant uppercase tracking-widest font-bold">Awaiting Tactical Data</p>
                </div>
              )}
            </div>
          </section>

          {/* Mission History Table */}
          <section>
             <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-heading font-bold text-on-surface">Recent Mission History</h2>
             </div>
             <div className="flat-panel overflow-hidden border-t-2 border-t-secondary/30">
                {summary.recent_scans.length > 0 ? (
                  <table className="w-full text-left">
                    <thead>
                      <tr className="border-b border-surface-border bg-surface-highlight/50 text-xs uppercase tracking-wider text-on-surface-variant font-bold">
                        <th className="px-6 py-4">Target Target</th>
                        <th className="px-6 py-4 text-center">Score</th>
                        <th className="px-6 py-4 text-center">Advice</th>
                        <th className="px-6 py-4 text-right">Timestamp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.recent_scans.map((log) => (
                        <tr key={log.id} onClick={() => navigate('/insights/' + log.id)} className="border-b border-surface-border hover:bg-surface-highlight cursor-pointer transition-colors last:border-b-0 group">
                          <td className="px-6 py-4 text-sm font-medium text-on-surface group-hover:text-primary transition-colors flex items-center gap-3">
                             <div className="w-1.5 h-1.5 rounded-full bg-surface-highlight group-hover:bg-primary transition-all"></div>
                             {log.url}
                          </td>
                          <td className="px-6 py-4 text-center">
                            <span className="text-sm font-mono font-bold text-on-surface">{log.score}</span>
                          </td>
                          <td className="px-6 py-4 text-center">
                              <button 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  window.open(`http://localhost:8000/api/reports/${log.id}/download`, '_blank');
                                }}
                                className="p-2 hover:bg-primary/10 rounded-full text-on-surface-variant hover:text-primary transition-all group/btn"
                                title="Download forensic pdf"
                              >
                                <Download size={14} />
                              </button>
                          </td>
                          <td className="px-6 py-4 text-right text-[10px] font-mono text-on-surface-variant uppercase">
                            {new Date(log.date).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                   <div className="p-16 text-center text-on-surface-variant flex flex-col items-center justify-center">
                      <Activity size={32} className="opacity-20 mb-4" />
                      <p className="text-sm">No analysis history available.</p>
                   </div>
                )}
             </div>
          </section>
       </div>
    </div>
  )
}
