import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { client } from '../api/client.ts';
import { LogOut, Settings, Shield, FileText, Loader2, Keyboard } from 'lucide-react';
import { useTheme } from '../components/ThemeContext.tsx';

export default function Profile() {
  const { enableHotkeys, setEnableHotkeys } = useTheme();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<any>(null);

  const [concurrency, setConcurrency] = useState(4);
  const [maxDepth, setMaxDepth] = useState(2);
  const [timeout, setTimeoutVal] = useState(30);
  const [skipExternal, setSkipExternal] = useState(true);
  const [userAgent, setUserAgent] = useState('default');
  const [ruleset, setRuleset] = useState('wcag21aa');
  const [politenessDelay, setPolitenessDelay] = useState(250);
  const [ignoredPatterns, setIgnoredPatterns] = useState('');
  const [retryLimit, setRetryLimit] = useState(3);
  const [robotsTxt, setRobotsTxt] = useState('strict');
  const [auditScope, setAuditScope] = useState('full');
  const [reportTemplate, setReportTemplate] = useState('cyberpunk');
  const [ignoredSelectors, setIgnoredSelectors] = useState('');
  
  const [isExporting, setIsExporting] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  useEffect(() => {
    client.get('/user/profile').then(res => {
       setProfile(res.data);
       setConcurrency(res.data.settings.concurrency);
       setMaxDepth(res.data.settings.max_depth);
       setTimeoutVal(res.data.settings.timeout);
       setSkipExternal(res.data.settings.skip_external);
       setUserAgent(res.data.settings.user_agent || 'default');
       setRuleset(res.data.settings.ruleset || 'wcag21aa');
       setPolitenessDelay(res.data.settings.politeness_delay || 250);
       setIgnoredPatterns(res.data.settings.ignored_patterns || '');
       setRetryLimit(res.data.settings.retry_limit || 3);
       setRobotsTxt(res.data.settings.robots_txt || 'strict');
       setAuditScope(res.data.settings.audit_scope || 'full');
       setReportTemplate(res.data.settings.report_template || 'cyberpunk');
       setIgnoredSelectors(res.data.settings.ignored_selectors || '');
    }).catch(console.error);
  }, []);

  const handleConcurrencyChange = (val: number) => {
     setConcurrency(val);
     client.patch('/user/settings', { concurrency: val }).catch(console.error);
  }
  
  const handleMaxDepthChange = (val: number) => {
     setMaxDepth(val);
     client.patch('/user/settings', { max_depth: val }).catch(console.error);
  }

  const handleTimeoutChange = (val: number) => {
     setTimeoutVal(val);
     client.patch('/user/settings', { timeout: val }).catch(console.error);
  }

  const handleSkipExternalToggle = () => {
     setSkipExternal(!skipExternal);
     client.patch('/user/settings', { skip_external: !skipExternal }).catch(console.error);
  }

  const handleUserAgentChange = (val: string) => {
     setUserAgent(val);
     client.patch('/user/settings', { user_agent: val }).catch(console.error);
  }

  const handleRulesetChange = (val: string) => {
     setRuleset(val);
     client.patch('/user/settings', { ruleset: val }).catch(console.error);
  }

  const handlePolitenessDelayChange = (val: number) => {
     setPolitenessDelay(val);
     client.patch('/user/settings', { politeness_delay: val }).catch(console.error);
  }

  const handleIgnoredPatternsChange = (val: string) => {
     setIgnoredPatterns(val);
  }

  const persistIgnoredPatterns = (val: string) => {
     client.patch('/user/settings', { ignored_patterns: val }).catch(console.error);
  }

  const handleRetryLimitChange = (val: number) => {
     setRetryLimit(val);
     client.patch('/user/settings', { retry_limit: val }).catch(console.error);
  }

  const handleRobotsTxtChange = (val: string) => {
     setRobotsTxt(val);
     client.patch('/user/settings', { robots_txt: val }).catch(console.error);
  }

  const handleAuditScopeChange = (val: string) => {
     setAuditScope(val);
     client.patch('/user/settings', { audit_scope: val }).catch(console.error);
  }

  const handleReportTemplateChange = (val: string) => {
     setReportTemplate(val);
     client.patch('/user/settings', { report_template: val }).catch(console.error);
  }

  const handleIgnoredSelectorsChange = (val: string) => {
     setIgnoredSelectors(val);
  }

  const persistIgnoredSelectors = (val: string) => {
     client.patch('/user/settings', { ignored_selectors: val }).catch(console.error);
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

  if (!profile) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center text-on-surface" aria-live="polite">
        <Loader2 className="animate-spin text-primary" size={48} aria-label="Loading Settings Details" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-on-surface p-8 max-w-4xl mx-auto pb-32 fade-in-up">
      <header className="mb-10 pt-4 flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-surface-border pb-8">
        <div>
          <h1 className="text-3xl font-heading font-bold text-on-surface">Settings Center</h1>
          <p className="text-on-surface-variant mt-2 text-sm">Manage dynamic crawler configurations, audit timeouts, and active session telemetry.</p>
        </div>
      </header>

      <div className="space-y-8">
         {/* Preferences Panel */}
         <div className="glass-panel p-8 border-none bg-surface-container-low">
            <h2 className="text-xs text-on-surface-variant uppercase tracking-widest font-bold mb-8 flex items-center gap-2">
               <Settings size={14} className="text-primary" aria-hidden="true" /> Crawl Engine Tuning
            </h2>

            <div className="space-y-6">
               {/* Select: Concurrency */}
               <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                     <label htmlFor="concurrency-select" className="font-bold text-sm text-on-surface block cursor-pointer">Crawler Concurrency</label>
                     <p className="text-xs text-on-surface-variant mt-1 leading-normal">Maximum simultaneous page requests processed by the runner.</p>
                  </div>
                  <select
                     id="concurrency-select"
                     value={concurrency}
                     onChange={(e) => handleConcurrencyChange(Number(e.target.value))}
                     className="bg-background border border-surface-border rounded-md px-3 py-2 text-xs font-bold text-on-surface focus:outline-none focus:ring-2 focus:ring-primary w-full sm:w-32 cursor-pointer uppercase tracking-wider font-heading"
                  >
                     <option value={1}>1 Worker</option>
                     <option value={2}>2 Workers</option>
                     <option value={4}>4 Workers</option>
                     <option value={8}>8 Workers</option>
                  </select>
               </div>

               {/* Select: Crawl Depth Boundary */}
               <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-surface-border/50 pt-6">
                  <div>
                     <label htmlFor="depth-select" className="font-bold text-sm text-on-surface block cursor-pointer">Max Crawl Depth</label>
                     <p className="text-xs text-on-surface-variant mt-1 leading-normal">Link distance limit from the entry URL for multi-page auditing.</p>
                  </div>
                  <select
                     id="depth-select"
                     value={maxDepth}
                     onChange={(e) => handleMaxDepthChange(Number(e.target.value))}
                     className="bg-background border border-surface-border rounded-md px-3 py-2 text-xs font-bold text-on-surface focus:outline-none focus:ring-2 focus:ring-primary w-full sm:w-32 cursor-pointer uppercase tracking-wider font-heading"
                  >
                     <option value={1}>1 (Single URL)</option>
                     <option value={2}>2 (Depth 2)</option>
                     <option value={3}>3 (Depth 3)</option>
                     <option value={5}>5 (Depth 5)</option>
                  </select>
               </div>

               {/* Select: Timeout Limit */}
               <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-surface-border/50 pt-6">
                  <div>
                     <label htmlFor="timeout-select" className="font-bold text-sm text-on-surface block cursor-pointer">Audit Timeout Limit</label>
                     <p className="text-xs text-on-surface-variant mt-1 leading-normal">Seconds permitted for a single URL response check before aborting.</p>
                  </div>
                  <select
                     id="timeout-select"
                     value={timeout}
                     onChange={(e) => handleTimeoutChange(Number(e.target.value))}
                     className="bg-background border border-surface-border rounded-md px-3 py-2 text-xs font-bold text-on-surface focus:outline-none focus:ring-2 focus:ring-primary w-full sm:w-32 cursor-pointer uppercase tracking-wider font-heading"
                  >
                     <option value={15}>15 Seconds</option>
                     <option value={30}>30 Seconds</option>
                     <option value={60}>60 Seconds</option>
                     <option value={90}>90 Seconds</option>
                  </select>
               </div>
                {/* Select: User Agent Override */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-surface-border/50 pt-6">
                   <div>
                      <label htmlFor="user-agent-select" className="font-bold text-sm text-on-surface block cursor-pointer">User Agent Simulator</label>
                      <p className="text-xs text-on-surface-variant mt-1 leading-normal">Override crawler identity headers presented to server nodes.</p>
                   </div>
                   <select
                      id="user-agent-select"
                      value={userAgent}
                      onChange={(e) => handleUserAgentChange(e.target.value)}
                      className="bg-background border border-surface-border rounded-md px-3 py-2 text-xs font-bold text-on-surface focus:outline-none focus:ring-2 focus:ring-primary w-full sm:w-48 cursor-pointer uppercase tracking-wider font-heading text-left"
                   >
                      <option value="default">Default Crawler</option>
                      <option value="googlebot">Googlebot Mobile</option>
                      <option value="lighthouse">Lighthouse Auditor</option>
                      <option value="desktop-chrome">Desktop Chrome / Mac</option>
                      <option value="mobile-safari">Mobile Safari / iOS</option>
                   </select>
                </div>
 
                {/* Select: Ruleset */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-surface-border/50 pt-6">
                   <div>
                      <label htmlFor="ruleset-select" className="font-bold text-sm text-on-surface block cursor-pointer">WCAG Audit Standard</label>
                      <p className="text-xs text-on-surface-variant mt-1 leading-normal">Primary accessibility compliance guidelines targeted during heuristics.</p>
                   </div>
                   <select
                      id="ruleset-select"
                      value={ruleset}
                      onChange={(e) => handleRulesetChange(e.target.value)}
                      className="bg-background border border-surface-border rounded-md px-3 py-2 text-xs font-bold text-on-surface focus:outline-none focus:ring-2 focus:ring-primary w-full sm:w-48 cursor-pointer uppercase tracking-wider font-heading text-left"
                   >
                      <option value="wcag21aa">WCAG 2.1 (AA)</option>
                      <option value="wcag22aaa">WCAG 2.2 (AAA)</option>
                      <option value="section508">Section 508</option>
                      <option value="en301549">EN 301 549 (EU)</option>
                   </select>
                </div>
 
                {/* Select: Politeness Delay */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-surface-border/50 pt-6">
                   <div>
                      <label htmlFor="politeness-select" className="font-bold text-sm text-on-surface block cursor-pointer">Request Politeness Delay</label>
                      <p className="text-xs text-on-surface-variant mt-1 leading-normal">Millisecond wait timer between concurrent request executions.</p>
                   </div>
                   <select
                      id="politeness-select"
                      value={politenessDelay}
                      onChange={(e) => handlePolitenessDelayChange(Number(e.target.value))}
                      className="bg-background border border-surface-border rounded-md px-3 py-2 text-xs font-bold text-on-surface focus:outline-none focus:ring-2 focus:ring-primary w-full sm:w-48 cursor-pointer uppercase tracking-wider font-heading text-left"
                   >
                      <option value={0}>No Delay (Immediate)</option>
                      <option value={250}>250ms Delay</option>
                      <option value={500}>500ms Delay</option>
                      <option value={1000}>1000ms (Gentle)</option>
                   </select>
                </div>
               
               {/* Input: Ignored Patterns */}
               <div className="flex flex-col gap-2 border-t border-surface-border/50 pt-6">
                  <div>
                     <h3 className="font-bold text-sm text-on-surface">Ignored URL Patterns</h3>
                     <p className="text-xs text-on-surface-variant mt-1 leading-normal">Comma-separated regex patterns of URLs to skip (e.g. signouts, downloads).</p>
                  </div>
                  <textarea
                     id="ignored-patterns"
                     value={ignoredPatterns}
                     onChange={(e) => handleIgnoredPatternsChange(e.target.value)}
                     onBlur={(e) => persistIgnoredPatterns(e.target.value)}
                     rows={2}
                     className="bg-background border border-surface-border rounded-md px-4 py-2 text-xs text-on-surface focus:outline-none focus:ring-2 focus:ring-primary w-full font-mono mt-1 placeholder-on-surface-variant/40"
                     placeholder="e.g. .*\/logout, .*\/signout, .*\/delete, .*\.pdf"
                  />
               </div>
               {/* Select: Connection Retry Limit */}
               <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-surface-border/50 pt-6">
                  <div>
                     <h3 className="font-bold text-sm text-on-surface">Connection Retry Limit</h3>
                     <p className="text-xs text-on-surface-variant mt-1 leading-normal">Network retry attempts made upon page load or connection timeout failures.</p>
                  </div>
                  <select
                     id="retry-select"
                     value={retryLimit}
                     onChange={(e) => handleRetryLimitChange(Number(e.target.value))}
                     className="bg-background border border-surface-border rounded-md px-3 py-2 text-xs font-bold text-on-surface focus:outline-none focus:ring-2 focus:ring-primary w-full sm:w-48 cursor-pointer uppercase tracking-wider font-heading text-left"
                  >
                     <option value={0}>0 Retries (Immediate Fail)</option>
                     <option value={1}>1 Retry</option>
                     <option value={2}>2 Retries</option>
                     <option value={3}>3 Retries</option>
                  </select>
               </div>

               {/* Select: Robots.txt Strictness Mode */}
               <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-surface-border/50 pt-6">
                  <div>
                     <h3 className="font-bold text-sm text-on-surface">Robots.txt Adherence</h3>
                     <p className="text-xs text-on-surface-variant mt-1 leading-normal">Strictness level applied to crawler constraints declared in site registries.</p>
                  </div>
                  <select
                     id="robots-select"
                     value={robotsTxt}
                     onChange={(e) => handleRobotsTxtChange(e.target.value)}
                     className="bg-background border border-surface-border rounded-md px-3 py-2 text-xs font-bold text-on-surface focus:outline-none focus:ring-2 focus:ring-primary w-full sm:w-48 cursor-pointer uppercase tracking-wider font-heading text-left"
                  >
                     <option value="strict">Strict (Obey Directives)</option>
                     <option value="deceptive">Deceptive (Ignore robots.txt)</option>
                  </select>
               </div>

               {/* Select: Heuristics Target Scope */}
               <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-surface-border/50 pt-6">
                  <div>
                     <h3 className="font-bold text-sm text-on-surface">Heuristic Target Scope</h3>
                     <p className="text-xs text-on-surface-variant mt-1 leading-normal">Limit evaluation rules to specific DOM sub-sections or element types.</p>
                  </div>
                  <select
                     id="scope-select"
                     value={auditScope}
                     onChange={(e) => handleAuditScopeChange(e.target.value)}
                     className="bg-background border border-surface-border rounded-md px-3 py-2 text-xs font-bold text-on-surface focus:outline-none focus:ring-2 focus:ring-primary w-full sm:w-48 cursor-pointer uppercase tracking-wider font-heading text-left"
                  >
                     <option value="full">Entire Document (Full DOM)</option>
                     <option value="interactive">Interactive Elements Only</option>
                     <option value="text">Content & Text Blocks Only</option>
                     <option value="media">Images & Media Assets Only</option>
                  </select>
               </div>

               {/* Select: Compliance Report Template Style */}
               <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-surface-border/50 pt-6">
                  <div>
                     <h3 className="font-bold text-sm text-on-surface">Report Presentation Theme</h3>
                     <p className="text-xs text-on-surface-variant mt-1 leading-normal">Visual template theme applied during compliance PDF generation exports.</p>
                  </div>
                  <select
                     id="template-select"
                     value={reportTemplate}
                     onChange={(e) => handleReportTemplateChange(e.target.value)}
                     className="bg-background border border-surface-border rounded-md px-3 py-2 text-xs font-bold text-on-surface focus:outline-none focus:ring-2 focus:ring-primary w-full sm:w-48 cursor-pointer uppercase tracking-wider font-heading text-left"
                  >
                     <option value="cyberpunk">Cyberpunk Default</option>
                     <option value="monochrome">Minimal Monochrome</option>
                     <option value="executive">Executive Summary</option>
                     <option value="technical">Full Technical Checklist</option>
                  </select>
               </div>

               {/* Input: Ignored Selectors */}
               <div className="flex flex-col gap-2 border-t border-surface-border/50 pt-6">
                  <div>
                     <h3 className="font-bold text-sm text-on-surface">Ignored CSS Selectors</h3>
                     <p className="text-xs text-on-surface-variant mt-1 leading-normal">Comma-separated CSS selectors to skip during contrast/focus scans.</p>
                  </div>
                  <textarea
                     id="ignored-selectors"
                     value={ignoredSelectors}
                     onChange={(e) => handleIgnoredSelectorsChange(e.target.value)}
                     onBlur={(e) => persistIgnoredSelectors(e.target.value)}
                     rows={2}
                     className="bg-background border border-surface-border rounded-md px-4 py-2 text-xs text-on-surface focus:outline-none focus:ring-2 focus:ring-primary w-full font-mono mt-1 placeholder-on-surface-variant/40"
                     placeholder="e.g. .ignore-a11y, #cookie-banner, .chat-bubble"
                  />
               </div>
               
               {/* Toggle: Skip External Domains */}
               <div className="flex items-center justify-between border-t border-surface-border/50 pt-6">
                  <div>
                     <h3 className="font-bold text-sm text-on-surface">Skip Third-Party Assets</h3>
                     <p className="text-xs text-on-surface-variant mt-1 leading-normal">Ignore external domains and track local site architecture only.</p>
                  </div>
                  <button 
                     onClick={handleSkipExternalToggle}
                     role="switch"
                     aria-checked={skipExternal}
                     aria-label="Toggle Skip Third-Party Assets"
                     className={`w-14 h-8 rounded-full flex items-center transition-colors p-1 cursor-pointer ${skipExternal ? 'bg-primary' : 'bg-surface-highlight border border-surface-border'}`}
                  >
                     <div className={`w-6 h-6 rounded-full bg-background transition-transform ${skipExternal ? 'translate-x-6' : 'translate-x-0'}`}></div>
                  </button>
               </div>
            </div>
         </div>

         {/* Accessibility & Navigation Preferences */}
         <div className="glass-panel p-8 border-none bg-surface-container-low">
            <h2 className="text-xs text-on-surface-variant uppercase tracking-widest font-bold mb-6 flex items-center gap-2">
               <Keyboard size={14} className="text-primary" aria-hidden="true" /> Accessibility Shortcuts
            </h2>

            <div className="space-y-6">
               <div className="flex items-center justify-between">
                  <div>
                     <h3 className="font-bold text-sm text-on-surface">Keyboard Navigation hotkeys</h3>
                     <p className="text-xs text-on-surface-variant mt-1 leading-normal">Permit dynamic system adjustments and navigation via Alt + [Key] sequences.</p>
                  </div>
                  <button 
                     onClick={() => setEnableHotkeys(!enableHotkeys)}
                     role="switch"
                     aria-checked={enableHotkeys}
                     aria-label="Toggle Keyboard Shortcuts"
                     className={`w-14 h-8 rounded-full flex items-center transition-colors p-1 cursor-pointer ${enableHotkeys ? 'bg-primary' : 'bg-surface-highlight border border-surface-border'}`}
                  >
                     <div className={`w-6 h-6 rounded-full bg-background transition-transform ${enableHotkeys ? 'translate-x-6' : 'translate-x-0'}`}></div>
                  </button>
               </div>
            </div>
         </div>

         {/* Utility Actions */}
         <div className="glass-panel p-2 border-none relative">
            {toastMsg && (
              <div className="absolute top-0 right-0 transform translate-x-1/2 -translate-y-1/2 bg-surface border border-primary/50 text-primary px-4 py-2 rounded-md shadow-glow z-20 font-medium tracking-wide flex items-center gap-2 text-xs" role="status">
                 {isExporting && <Loader2 className="animate-spin" size={12} />} {toastMsg}
              </div>
            )}
            <div className="flex flex-col">
               <button onClick={() => navigate('/privacy')} className="flex items-center justify-between p-4 hover:bg-surface-highlight/50 transition-colors rounded-t-md group cursor-pointer text-left focus:text-primary outline-none">
                  <div className="flex items-center gap-3">
                     <Shield className="text-on-surface-variant group-hover:text-primary transition-colors" size={18} aria-hidden="true" />
                     <span className="font-medium text-xs">Privacy & Security Policies</span>
                  </div>
               </button>
               <button onClick={handleExportLogs} disabled={isExporting} className="flex items-center justify-between p-4 hover:bg-surface-highlight/50 transition-colors border-t border-surface-border/50 rounded-b-md group cursor-pointer text-left disabled:opacity-50 focus:text-primary outline-none">
                  <div className="flex items-center gap-3">
                     <FileText className="text-on-surface-variant group-hover:text-primary transition-colors" size={18} aria-hidden="true" />
                     <span className="font-medium text-xs">Export Complete Organization Logs</span>
                  </div>
               </button>
            </div>
         </div>

         {/* Terminate Session */}
         <button 
            onClick={handleLogout}
            className="w-full secondary-btn bg-error/10 text-error border-error/50 hover:bg-error hover:text-background flex items-center justify-center gap-2 py-4 shadow-none mt-4 cursor-pointer transition-all focus:ring-2 focus:ring-error outline-none"
         >
            <LogOut size={18} aria-hidden="true" /> Terminate Secure Session
         </button>
      </div>
    </div>
  );
}
