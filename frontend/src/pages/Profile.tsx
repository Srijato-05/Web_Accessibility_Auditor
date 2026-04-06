import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { client } from '../api/client';
import { User, LogOut, Settings, Zap, FileText, Database, Shield, LifeBuoy, Loader2 } from 'lucide-react';

export default function Profile() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<any>(null);

  const [deepAudit, setDeepAudit] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState(false);
  const [emailAlerts, setEmailAlerts] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  useEffect(() => {
    client.get('/user/profile').then(res => {
       setProfile(res.data);
       setDeepAudit(res.data.settings.deep_audit_mode);
       setAiSuggestions(res.data.settings.ai_suggestions);
       setEmailAlerts(res.data.settings.email_alerts);
    }).catch(console.error);
  }, []);

  const handleDeepAuditToggle = () => {
     setDeepAudit(!deepAudit);
     client.patch('/user/settings', { deep_audit_mode: !deepAudit }).catch(console.error);
  }
  
  const handleAiSuggestionsToggle = () => {
     setAiSuggestions(!aiSuggestions);
     client.patch('/user/settings', { ai_suggestions: !aiSuggestions }).catch(console.error);
  }

  const handleEmailAlertsToggle = () => {
     setEmailAlerts(!emailAlerts);
     client.patch('/user/settings', { email_alerts: !emailAlerts }).catch(console.error);
  }

  const handleExportLogs = async () => {
     setIsExporting(true);
     setToastMsg('Generating Report...');
     try {
        const response = await client.get('/user/export-logs', { responseType: 'blob' });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'audit_logs.csv');
        document.body.appendChild(link);
        link.click();
        link.parentNode?.removeChild(link);
        setToastMsg('Audit Log Exported Successfully');
        setTimeout(() => setToastMsg(null), 3000);
     } catch(e) {
        console.error(e);
        setToastMsg('Failed to export logs');
        setTimeout(() => setToastMsg(null), 3000);
     }
     setIsExporting(false);
  }

  const handleLogout = () => {
    localStorage.clear();
    sessionStorage.clear();
    localStorage.removeItem('token');
    navigate('/');
  }

  if (!profile) return <div className="min-h-screen bg-background flex items-center justify-center text-on-surface"><Loader2 className="animate-spin text-primary" size={48} /></div>;

  const pct = (profile.tokens / profile.max_tokens) * 100;

  return (
    <div className="min-h-screen bg-background text-on-surface p-8 max-w-5xl mx-auto pb-32">
      <header className="mb-10 pt-4 flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-outline-variant/15 pb-8">
        <div className="flex items-center gap-6">
           <div className="w-20 h-20 bg-surface-container-highest rounded-full border-2 border-primary/30 flex items-center justify-center shadow-ambient overflow-hidden">
               {/* Mock Avatar placeholder using Lucide User icon if arbitrary avatar unavailable */}
               <User size={48} className="text-secondary opacity-80" />
           </div>
           <div>
              <div className="flex items-center gap-3 mb-1">
                 <h1 className="text-display font-medium">{profile.name}</h1>
                 <span className="bg-secondary/10 text-secondary border border-secondary/20 px-2 py-0.5 rounded-full text-xs uppercase tracking-widest font-bold">
                    {profile.tier} Tier
                 </span>
              </div>
              <p className="text-on-surface-variant font-body">{profile.role}</p>
           </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         {/* Token Balance */}
         <div className="glass-panel p-8 shadow-ambient flex flex-col justify-center border-secondary/20 col-span-1 border-t-4 border-t-secondary relative overflow-hidden group">
            <div className="absolute top-4 right-4 text-secondary/20 group-hover:text-secondary/40 transition-colors">
               <Database size={64} />
            </div>
            
            <h2 className="text-label text-on-surface-variant uppercase tracking-widest font-bold mb-6 relative z-10">Integrity Token Balance</h2>
            <div className="flex items-end gap-2 mb-4 relative z-10">
               <span className="text-5xl font-heading font-medium text-secondary shadow-glow">{profile.tokens.toLocaleString()}</span>
               <span className="text-on-surface-variant mb-1">/ {profile.max_tokens.toLocaleString()}</span>
            </div>
            
            <div className="w-full h-2 bg-surface-container-highest rounded-full overflow-hidden mt-2 border border-outline-variant/20 relative z-10">
               <div className="h-full bg-secondary shadow-glow transition-all duration-1000" style={{ width: `${pct}%` }}></div>
            </div>
            <p className="text-xs text-on-surface-variant mt-4 relative z-10 flex items-center gap-2">
               <Zap size={14} className="text-secondary" /> Scan consumption drops tokens by -50.
            </p>
         </div>

         {/* Preferences */}
         <div className="col-span-1 lg:col-span-2 space-y-6">
            <div className="glass-panel p-8 border-none bg-surface-container-low shadow-ambient">
               <h2 className="text-label text-on-surface-variant uppercase tracking-widest font-bold mb-6 flex items-center gap-2">
                  <Settings size={18} /> System Preferences
               </h2>

               <div className="space-y-6">
                  {/* Toggle: Deep Audit Mode */}
                  <div className="flex items-center justify-between">
                     <div>
                        <h3 className="font-bold text-on-surface">Deep Audit Mode</h3>
                        <p className="text-sm text-on-surface-variant">Perform exhaustive DOM layout analysis vs fast heuristic parsing.</p>
                     </div>
                     <button 
                        onClick={handleDeepAuditToggle}
                        className={`w-14 h-8 rounded-full flex items-center transition-colors p-1 cursor-pointer ${deepAudit ? 'bg-primary' : 'bg-surface-container-highest border border-outline-variant/30'}`}
                     >
                        <div className={`w-6 h-6 rounded-full bg-on-primary transition-transform ${deepAudit ? 'translate-x-6 shadow-glow' : 'translate-x-0'}`}></div>
                     </button>
                  </div>

                  {/* Toggle: AI Suggestions */}
                  <div className="flex items-center justify-between border-t border-outline-variant/10 pt-6">
                     <div>
                        <h3 className="font-bold text-on-surface">Sentinel AI Engine</h3>
                        <p className="text-sm text-on-surface-variant">Enable automated AST graph traversal logic recommendations in Insights.</p>
                     </div>
                     <button 
                        onClick={handleAiSuggestionsToggle}
                        className={`w-14 h-8 rounded-full flex items-center transition-colors p-1 cursor-pointer ${aiSuggestions ? 'bg-tertiary' : 'bg-surface-container-highest border border-outline-variant/30'}`}
                     >
                        <div className={`w-6 h-6 rounded-full bg-background transition-transform ${aiSuggestions ? 'translate-x-6 shadow-ambient border border-tertiary/50' : 'translate-x-0'}`}></div>
                     </button>
                  </div>
                  
                  {/* Toggle: Email Alerts */}
                  <div className="flex items-center justify-between border-t border-outline-variant/10 pt-6">
                     <div>
                        <h3 className="font-bold text-on-surface">Critcal Alert Relay</h3>
                        <p className="text-sm text-on-surface-variant">Send email notifications when domain health scores drop below automated thresholds.</p>
                     </div>
                     <button 
                        onClick={handleEmailAlertsToggle}
                        className={`w-14 h-8 rounded-full flex items-center transition-colors p-1 cursor-pointer ${emailAlerts ? 'bg-secondary' : 'bg-surface-container-highest border border-outline-variant/30'}`}
                     >
                        <div className={`w-6 h-6 rounded-full bg-background transition-transform ${emailAlerts ? 'translate-x-6' : 'translate-x-0'}`}></div>
                     </button>
                  </div>
               </div>
            </div>

            <div className="glass-panel p-2 border-none bg-surface-container-low shadow-ambient relative">
               {toastMsg && (
                 <div className="absolute top-0 right-0 transform translate-x-1/2 -translate-y-1/2 bg-surface-container-highest border border-primary/50 text-primary px-4 py-2 rounded-md shadow-glow z-20 font-medium tracking-wide flex items-center gap-2">
                    {isExporting && <Loader2 className="animate-spin" size={14} />} {toastMsg}
                 </div>
               )}
               <div className="flex flex-col">
                  <button onClick={() => navigate('/privacy')} className="flex items-center justify-between p-4 hover:bg-surface-container-highest transition-colors rounded-t-md group cursor-pointer text-left">
                     <div className="flex items-center gap-3">
                        <Shield className="text-on-surface-variant group-hover:text-primary transition-colors" size={20} />
                        <span className="font-medium">Privacy & Security Policies</span>
                     </div>
                  </button>
                  <button onClick={handleExportLogs} disabled={isExporting} className="flex items-center justify-between p-4 hover:bg-surface-container-highest transition-colors border-t border-outline-variant/10 group cursor-pointer text-left disabled:opacity-50">
                     <div className="flex items-center gap-3">
                        <FileText className="text-on-surface-variant group-hover:text-primary transition-colors" size={20} />
                        <span className="font-medium">Export Complete Organization Logs</span>
                     </div>
                  </button>
                  <button onClick={() => navigate('/support')} className="flex items-center justify-between p-4 hover:bg-surface-container-highest transition-colors border-t border-outline-variant/10 group cursor-pointer text-left rounded-b-md">
                     <div className="flex items-center gap-3">
                        <LifeBuoy className="text-on-surface-variant group-hover:text-primary transition-colors" size={20} />
                        <span className="font-medium">Support Center</span>
                     </div>
                  </button>
               </div>
            </div>

            <button 
               onClick={handleLogout}
               className="w-full primary-btn bg-error/10 text-error border-error/50 hover:bg-error hover:text-background flex items-center justify-center gap-2 py-4 shadow-none mt-12 cursor-pointer transition-all"
            >
               <LogOut size={20} /> Terminate Secure Session
            </button>
         </div>
      </div>
    </div>
  )
}
