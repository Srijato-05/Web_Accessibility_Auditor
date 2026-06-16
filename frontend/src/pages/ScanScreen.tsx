import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { client } from '../api/client.ts';
import { 
  Play, 
  ShieldAlert, 
  Cpu, 
  Layers, 
  ChevronLeft, 
  ChevronRight, 
  Monitor, 
  Smartphone,
  Eye,
  Settings,
  HelpCircle,
  Clock,
  Compass,
  AlertTriangle
} from 'lucide-react';

export default function ScanScreen() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [url, setUrl] = useState('');
  const [depth, setDepth] = useState(2);
  const [scanType, setScanType] = useState<'single' | 'multi'>('single');
  const [strategy, setStrategy] = useState<'fast' | 'polite'>('fast');
  const [viewport, setViewport] = useState('1920x1080');
  const [dpr, setDpr] = useState('1.0');
  const [network, setNetwork] = useState('none');
  const [latency, setLatency] = useState('0');
  const [reducedMotion, setReducedMotion] = useState(false);
  const [colorScheme, setColorScheme] = useState('no-preference');
  const [contrast, setContrast] = useState('no-preference');
  const [forcedColors, setForcedColors] = useState(false);
  const [reducedData, setReducedData] = useState(false);
  const [agent, setAgent] = useState('desktop_chrome');
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const simulationLogs = [
    "Establishing connection with A11yAudit analyzer node...",
    "Emulating target agent: Default Desktop Chrome",
    "Applying environment parameters: Resolution 1920x1080, Network: LAN",
    "Sending crawlers to origin root route...",
    "Traversing DOM nodes for accessibility hierarchy...",
    "Analyzing text nodes for WCAG color contrast matches...",
    "Scanning tag hierarchies for correct screen-reader landmarks...",
    "Compiling programmatic findings and remediation advice...",
    "Saving reports to secure database repository..."
  ];

  const startTelemetrySimulation = () => {
    setLogs([]);
    let index = 0;
    const interval = setInterval(() => {
      if (index < simulationLogs.length) {
        setLogs(prev => [...prev, `[${(index * 0.6).toFixed(1)}s] ${simulationLogs[index]}`]);
        index++;
      } else {
        clearInterval(interval);
      }
    }, 600);
    return interval;
  };

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    setLoading(true);
    setErrorMsg(null);
    const telemetryInterval = startTelemetrySimulation();

    try {
      const resp = await client.post('/scans', {
        url,
        depth: scanType === 'single' ? 1 : depth,
        standards: ['wcag2a', 'wcag2aa', 'wcag2aaa', 'sec508'],
        agent,
        strategy,
        viewport,
        dpr,
        network,
        latency,
        reducedMotion,
        colorScheme,
        contrast,
        forcedColors,
        reducedData
      });
      clearInterval(telemetryInterval);
      navigate(`/reports/${resp.data.id || resp.data.scan_id}`);
    } catch (e: any) {
      clearInterval(telemetryInterval);
      console.error(e);
      setErrorMsg(e.response?.data?.detail || 'Analysis pipeline initialization failure.');
      setLoading(false);
    }
  };

  const agentPersonas = [
    { id: 'desktop_chrome', name: 'Default Desktop Chrome', desc: 'Simulates normal desktop user interactions.' },
    { id: 'secure_auditor', name: 'Secure Auditor Bot', desc: 'Secure agent proxy to bypass rate-limiting and access shields.' },
    { id: 'screen_reader', name: 'Screen Reader Assist (JAWS/NVDA)', desc: 'Prioritizes accessibility tree, custom ARIA states, and read orders.' },
    { id: 'mobile_chrome', name: 'Mobile Chrome Emulator', desc: 'Renders pages using mobile screen breakpoints and touch reflow.' },
    { id: 'keyboard_only', name: 'Keyboard-Only Traversal', desc: 'Simulates focus tracking, tab navigation paths, and keyboard traps.' },
    { id: 'colorblind_deuteranopia', name: 'Colorblind Viewer (Deuteranopia)', desc: 'Simulates red-green visual cues and checks compliance contrast ratios.' },
    { id: 'low_vision_zoom', name: 'Low Vision (Zoom 200%)', desc: 'Emulates visual magnification viewport reflow and layout overlapping.' },
    { id: 'seo_crawler', name: 'Search Engine Crawler (SEO Bot)', desc: 'Simulates search bot algorithms parsing structure and header tags.' }
  ];

  // Map viewport choices to aspect ratio preview dimensions
  const getPreviewDimensions = () => {
    switch(viewport) {
      case '375x812': return { width: '180px', height: '360px', device: 'Phone Portrait' };
      case '812x375': return { width: '320px', height: '160px', device: 'Phone Landscape' };
      case '768x1024': return { width: '240px', height: '320px', device: 'Tablet Portrait' };
      case '1024x768': return { width: '320px', height: '240px', device: 'Tablet Landscape' };
      case '240x240': return { width: '140px', height: '140px', device: 'Watch Face' };
      default: return { width: '100%', height: '280px', device: 'Widescreen Monitor' };
    }
  };

  const previewDim = getPreviewDimensions();

  const steps = [
    { number: 1, title: 'Scope & Strategy', icon: <Compass size={14} /> },
    { number: 2, title: 'Environment Simulator', icon: <Settings size={14} /> },
    { number: 3, title: 'Tactical Personas', icon: <Cpu size={14} /> }
  ];

  return (
    <div className="max-w-5xl mx-auto px-6 py-10 pb-32 min-h-screen fade-in-up">
      {/* SVG Deuteranopia Matrix Filter */}
      <svg className="hidden" aria-hidden="true">
        <defs>
          <filter id="deuteranopia-filter-preview">
            <feColorMatrix
              type="matrix"
              values="0.625, 0.375, 0, 0, 0,
                      0.7,   0.3,   0, 0, 0,
                      0,     0.3,   0.7, 0, 0,
                      0,     0,     0, 1, 0"
            />
          </filter>
        </defs>
      </svg>

      {loading && (
        <div className="fixed inset-0 bg-background/95 z-50 flex flex-col items-center justify-center p-6 backdrop-blur-md">
          <div className="glass-panel w-full max-w-2xl p-8 space-y-6 flex flex-col h-[400px] border-primary/50 relative overflow-hidden">
            <div className="scan-line"></div>
            <div className="flex items-center justify-between border-b border-surface-border pb-4">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-error"></div>
                <div className="w-3 h-3 rounded-full bg-warning"></div>
                <div className="w-3 h-3 rounded-full bg-primary animate-pulse"></div>
              </div>
              <span className="text-xs font-mono font-bold text-primary tracking-widest uppercase">Telemetry Analysis Stream</span>
            </div>
            
            <div className="flex-1 overflow-y-auto font-mono text-xs text-on-surface-variant space-y-2 p-4 bg-black/40 rounded border border-surface-border/30 shadow-inner flex flex-col justify-end">
              {logs.map((log, i) => (
                <div key={i} className="text-left">
                  <span className="text-primary font-bold">{log.slice(0, 8)}</span>
                  <span className="text-on-surface ml-2">{log.slice(8)}</span>
                </div>
              ))}
              <div className="flex items-center gap-2 text-primary font-bold animate-pulse mt-2 text-left">
                <span>&gt;</span>
                <span className="w-2 h-4 bg-primary"></span>
              </div>
            </div>
            
            <div className="flex justify-between items-center text-[10px] text-on-surface-variant uppercase font-mono pt-4 border-t border-surface-border/40">
              <span>Target: {url}</span>
              <span className="text-primary animate-pulse">Running Audits</span>
            </div>
          </div>
        </div>
      )}

      <header className="mb-8 border-b border-surface-border pb-6">
        <h1 className="text-3xl font-heading font-bold text-on-surface">Target Initializer</h1>
        <p className="text-on-surface-variant mt-2 text-sm">Configure spider crawl vectors and simulated agent personas.</p>
      </header>

      {errorMsg && (
        <div className="mb-6 p-4 bg-error/10 border border-error/20 text-error rounded text-xs flex items-center gap-2" role="alert">
          <ShieldAlert size={16} />
          {errorMsg}
        </div>
      )}

      {/* Progress Steps Header */}
      <nav aria-label="Target scan initialization steps" className="flex items-center justify-between mb-8 bg-surface-container-low p-4 rounded-lg border border-surface-border">
        {steps.map((s, idx) => (
          <div key={s.number} className="flex items-center flex-1 last:flex-none">
            <button
              type="button"
              onClick={() => {
                // Allow clicking back to already visited steps
                if (s.number < step || (s.number === 2 && url)) {
                  setStep(s.number);
                }
              }}
              disabled={s.number > 1 && !url}
              className="flex items-center gap-3 text-left focus:ring-2 focus:ring-primary outline-none rounded p-1 cursor-pointer disabled:cursor-not-allowed disabled:opacity-40"
              aria-current={step === s.number ? 'step' : undefined}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all border ${
                step === s.number ? 'bg-primary text-background border-primary shadow-neon' :
                step > s.number ? 'bg-surface-highlight border-primary text-primary' : 'bg-background border-surface-border text-on-surface-variant'
              }`}>
                {step > s.number ? '✓' : s.number}
              </div>
              <div className="hidden md:block">
                <span className={`text-[9px] uppercase tracking-wider font-extrabold block ${step === s.number ? 'text-primary' : 'text-on-surface-variant'}`}>
                  Step {s.number}
                </span>
                <span className={`text-xs font-bold ${step === s.number ? 'text-on-surface font-extrabold' : 'text-on-surface-variant'}`}>
                  {s.title}
                </span>
              </div>
            </button>
            {idx < steps.length - 1 && (
              <div className={`flex-1 h-0.5 mx-6 transition-all ${step > s.number ? 'bg-primary' : 'bg-surface-border'}`}></div>
            )}
          </div>
        ))}
      </nav>

      <form onSubmit={handleScan} className="space-y-8">
        
        {/* STEP 1: Target Scope & Strategy */}
        {step === 1 && (
          <div className="glass-panel p-8 space-y-6 fade-in-up">
            <h2 className="text-sm font-bold uppercase tracking-wider text-on-surface border-b border-surface-border/40 pb-3 flex items-center gap-2">
              <Compass size={16} className="text-primary" /> Step 1: Target & Crawling Scope
            </h2>
            
            <div className="space-y-2">
              <label htmlFor="target-url" className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Target Website URL</label>
              <input
                id="target-url"
                type="url"
                required
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full bg-background border border-surface-border rounded-md px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary text-on-surface font-mono"
              />
            </div>

            <div className="space-y-3 pt-4 border-t border-surface-border/50">
              <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant block">Scan Scope</span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setScanType('single')}
                  className={`flex items-start gap-3 p-4 rounded-md border text-left cursor-pointer transition-all hover:bg-surface-highlight/30 ${scanType === 'single' ? 'bg-primary/15 border-primary' : 'bg-background border-surface-border/50'}`}
                >
                  <input
                    type="radio"
                    readOnly
                    checked={scanType === 'single'}
                    className="mt-0.5 w-4 h-4 border-surface-border text-primary focus:ring-primary bg-background pointer-events-none"
                  />
                  <div>
                    <span className="text-xs font-bold text-on-surface">Single Page Scan</span>
                    <p className="text-[10px] text-on-surface-variant leading-normal mt-0.5">Audit only the target URL entry-point route.</p>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setScanType('multi')}
                  className={`flex items-start gap-3 p-4 rounded-md border text-left cursor-pointer transition-all hover:bg-surface-highlight/30 ${scanType === 'multi' ? 'bg-primary/15 border-primary' : 'bg-background border-surface-border/50'}`}
                >
                  <input
                    type="radio"
                    readOnly
                    checked={scanType === 'multi'}
                    className="mt-0.5 w-4 h-4 border-surface-border text-primary focus:ring-primary bg-background pointer-events-none"
                  />
                  <div>
                    <span className="text-xs font-bold text-on-surface">Multi-Page Deep Scan</span>
                    <p className="text-[10px] text-on-surface-variant leading-normal mt-0.5">Recursively crawl and audit linked paths under the same domain host.</p>
                  </div>
                </button>
              </div>
            </div>

            {scanType === 'multi' && (
              <div className="space-y-4 pt-4 border-t border-surface-border/50 transition-all duration-300">
                <div className="flex justify-between items-center">
                  <label htmlFor="crawl-depth" className="text-xs font-bold uppercase tracking-wider text-on-surface-variant flex items-center gap-2">
                    <Layers size={14} className="text-primary" /> Crawl Depth Boundaries
                  </label>
                  <span className="font-mono text-xs font-bold text-primary">{depth} Levels</span>
                </div>
                <input
                  id="crawl-depth"
                  type="range"
                  min="2"
                  max="5"
                  value={depth}
                  onChange={(e) => setDepth(Number(e.target.value))}
                  className="w-full h-1.5 bg-background rounded-lg appearance-none cursor-pointer accent-primary"
                />
                <div className="flex justify-between text-[10px] text-on-surface-variant font-mono uppercase font-bold">
                  <span>Standard Crawl (2)</span>
                  <span>Deep Traverse (5)</span>
                </div>
              </div>
            )}

            <div className="space-y-3 pt-4 border-t border-surface-border/50">
              <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant block">Scan Strategy Mode</span>
              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => setStrategy('fast')}
                  className={`flex-1 py-3 px-4 rounded-md border text-xs font-bold uppercase tracking-wider transition-all focus:outline-none ${strategy === 'fast' ? 'bg-primary/20 border-primary text-primary' : 'bg-background border-surface-border/50 text-on-surface-variant hover:text-on-surface'}`}
                >
                  Accelerated Scan
                </button>
                <button
                  type="button"
                  onClick={() => setStrategy('polite')}
                  className={`flex-1 py-3 px-4 rounded-md border text-xs font-bold uppercase tracking-wider transition-all focus:outline-none ${strategy === 'polite' ? 'bg-primary/20 border-primary text-primary' : 'bg-background border-surface-border/50 text-on-surface-variant hover:text-on-surface'}`}
                >
                  Throttled Mode
                </button>
              </div>
              <p className="text-[10px] text-on-surface-variant leading-normal mt-1">
                {strategy === 'fast' ? 'Crawls target host using parallel page traversals.' : 'Crawls sequentially with a 1.5s delay to prevent rate limit triggers.'}
              </p>
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="button"
                onClick={() => setStep(2)}
                disabled={!url}
                className="primary-btn flex items-center gap-2 px-6 py-2.5 text-xs font-bold uppercase tracking-wider cursor-pointer disabled:opacity-50"
              >
                Configure Environment <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: Environmental Simulator & Live Mockup Preview */}
        {step === 2 && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start fade-in-up">
            {/* Simulator Inputs Column */}
            <div className="glass-panel p-8 space-y-6 lg:col-span-7">
              <h2 className="text-sm font-bold uppercase tracking-wider text-on-surface border-b border-surface-border/40 pb-3 flex items-center gap-2">
                <Settings size={16} className="text-primary" /> Step 2: Environment Simulator
              </h2>

              <div className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="scan-viewport" className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Simulated Viewport</label>
                  <select
                    id="scan-viewport"
                    value={viewport}
                    onChange={(e) => setViewport(e.target.value)}
                    className="w-full bg-background border border-surface-border rounded-md px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary text-on-surface cursor-pointer font-mono"
                  >
                    <option value="1920x1080">Desktop Widescreen (1920x1080)</option>
                    <option value="1024x768">Tablet Landscape (1024x768)</option>
                    <option value="768x1024">Tablet Portrait (768x1024)</option>
                    <option value="812x375">Mobile Landscape (812x375)</option>
                    <option value="375x812">Mobile Portrait (375x812)</option>
                    <option value="240x240">Smart Watch Wearable (240x240)</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label htmlFor="scan-zoom" className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Simulated Zoom / DPR</label>
                  <select
                    id="scan-zoom"
                    value={dpr}
                    onChange={(e) => setDpr(e.target.value)}
                    className="w-full bg-background border border-surface-border rounded-md px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary text-on-surface cursor-pointer font-mono"
                  >
                    <option value="1.0">Standard Zoom (100% / 1.0 DPR)</option>
                    <option value="1.5">Zoom Level 1.5 (150% / 1.5 DPR)</option>
                    <option value="2.0">Accessibility Zoom (200% / 2.0 DPR)</option>
                    <option value="3.0">Maximum Zoom (300% / 3.0 DPR)</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label htmlFor="scan-network" className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Throttling</label>
                    <select
                      id="scan-network"
                      value={network}
                      onChange={(e) => setNetwork(e.target.value)}
                      className="w-full bg-background border border-surface-border rounded-md px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-primary text-on-surface cursor-pointer font-mono"
                    >
                      <option value="none">No limit</option>
                      <option value="fast4g">Fast 4G</option>
                      <option value="fast3g">Fast 3G</option>
                      <option value="slow3g">Slow 3G</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="scan-latency" className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Latency (RTT)</label>
                    <select
                      id="scan-latency"
                      value={latency}
                      onChange={(e) => setLatency(e.target.value)}
                      className="w-full bg-background border border-surface-border rounded-md px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-primary text-on-surface cursor-pointer font-mono"
                    >
                      <option value="0">0ms</option>
                      <option value="100">100ms</option>
                      <option value="500">500ms</option>
                      <option value="2000">2000ms</option>
                    </select>
                  </div>
                </div>

                <div className="pt-4 border-t border-surface-border/40 space-y-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block">Media Preferences</span>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label htmlFor="media-color-scheme" className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant">Color Scheme</label>
                      <select
                        id="media-color-scheme"
                        value={colorScheme}
                        onChange={(e) => setColorScheme(e.target.value)}
                        className="w-full bg-background border border-surface-border rounded-md px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary text-on-surface cursor-pointer font-mono"
                      >
                        <option value="no-preference">No Preference</option>
                        <option value="dark">Dark Theme</option>
                        <option value="light">Light Theme</option>
                      </select>
                    </div>

                    <div className="space-y-1">
                      <label htmlFor="media-contrast" className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant">Contrast</label>
                      <select
                        id="media-contrast"
                        value={contrast}
                        onChange={(e) => setContrast(e.target.value)}
                        className="w-full bg-background border border-surface-border rounded-md px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary text-on-surface cursor-pointer font-mono"
                      >
                        <option value="no-preference">No Preference</option>
                        <option value="more">High Contrast</option>
                        <option value="less">Low Contrast</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2">
                    <label className="flex items-center gap-2 text-xs text-on-surface cursor-pointer">
                      <input
                        type="checkbox"
                        checked={reducedMotion}
                        onChange={(e) => setReducedMotion(e.target.checked)}
                        className="rounded border-surface-border text-primary focus:ring-primary bg-background cursor-pointer"
                      />
                      <span className="truncate">reduced-motion</span>
                    </label>

                    <label className="flex items-center gap-2 text-xs text-on-surface cursor-pointer">
                      <input
                        type="checkbox"
                        checked={forcedColors}
                        onChange={(e) => setForcedColors(e.target.checked)}
                        className="rounded border-surface-border text-primary focus:ring-primary bg-background cursor-pointer"
                      />
                      <span className="truncate">forced-colors</span>
                    </label>

                    <label className="flex items-center gap-2 text-xs text-on-surface cursor-pointer">
                      <input
                        type="checkbox"
                        checked={reducedData}
                        onChange={(e) => setReducedData(e.target.checked)}
                        className="rounded border-surface-border text-primary focus:ring-primary bg-background cursor-pointer"
                      />
                      <span className="truncate">reduced-data</span>
                    </label>
                  </div>
                </div>
              </div>

              <div className="flex justify-between pt-6 border-t border-surface-border/40">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="secondary-btn flex items-center gap-2 px-5 py-2.5 text-xs font-bold uppercase tracking-wider cursor-pointer"
                >
                  <ChevronLeft size={14} /> Back
                </button>
                <button
                  type="button"
                  onClick={() => setStep(3)}
                  className="primary-btn flex items-center gap-2 px-5 py-2.5 text-xs font-bold uppercase tracking-wider cursor-pointer"
                >
                  Configure Personas <ChevronRight size={14} />
                </button>
              </div>
            </div>

            {/* Live Device Simulator Frame Column (Idea 5) */}
            <div className="lg:col-span-5 space-y-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant flex items-center gap-2">
                <Eye size={12} className="text-secondary" /> Live Simulator Frame
              </span>
              
              <div className="flat-panel p-6 bg-surface-highlight/5 border border-surface-border/40 flex items-center justify-center min-h-[420px] relative overflow-hidden">
                <div className="absolute top-3 right-3 bg-surface-container-high border border-surface-border px-2 py-0.5 rounded text-[9px] font-mono font-bold text-secondary uppercase tracking-widest">
                  {previewDim.device}
                </div>
                
                {/* Simulated Device Body */}
                <div 
                  className="border-2 border-surface-border rounded-lg bg-surface-container-low overflow-hidden flex flex-col transition-all duration-300 shadow-glow"
                  style={{ 
                    width: previewDim.width, 
                    height: previewDim.height,
                    maxWidth: '100%',
                    fontFamily: 'sans-serif',
                    filter: agent === 'colorblind_deuteranopia' ? 'url(#deuteranopia-filter-preview)' : 'none'
                  }}
                >
                  {/* Mock Site Header */}
                  <div className={`p-3 border-b border-surface-border flex items-center justify-between ${
                    colorScheme === 'dark' ? 'bg-black text-white' : 
                    colorScheme === 'light' ? 'bg-white text-black' : 'bg-surface-highlight text-on-surface'
                  }`}>
                    <span className="text-[10px] font-bold tracking-wider font-mono">MOCK_HOST</span>
                    <div className="flex gap-1">
                      <div className="w-1.5 h-1.5 rounded-full bg-error"></div>
                      <div className="w-1.5 h-1.5 rounded-full bg-warning"></div>
                      <div className="w-1.5 h-1.5 rounded-full bg-primary"></div>
                    </div>
                  </div>

                  {/* Mock Site Content View */}
                  <div className={`flex-1 p-3 overflow-y-auto space-y-3 text-left ${
                    colorScheme === 'dark' ? 'bg-black text-white' : 
                    colorScheme === 'light' ? 'bg-white text-black' : 'bg-background text-on-surface-variant'
                  }`}
                  style={{
                    fontSize: dpr === '2.0' ? '1.2rem' : dpr === '3.0' ? '1.5rem' : '0.8rem',
                    lineHeight: dpr === '2.0' || dpr === '3.0' ? '1.7' : '1.4'
                  }}
                  >
                    <h4 className={`font-bold text-xs ${
                      contrast === 'more' ? 'text-white bg-black p-1' :
                      contrast === 'less' ? 'text-surface-highlight' : 'text-on-surface'
                    }`}>Auditable Layout Elements</h4>
                    
                    {/* Simulated Image / Data Loader */}
                    {reducedData ? (
                      <div className="p-3 bg-surface-highlight/30 border border-surface-border rounded text-[8px] font-mono text-center text-on-surface-variant uppercase">
                        [Data Saving: Image Omitted]
                      </div>
                    ) : (
                      <div className="h-16 w-full rounded bg-gradient-to-r from-primary/30 to-secondary/30 relative flex items-center justify-center overflow-hidden">
                        <span className="text-[8px] font-bold font-mono tracking-widest text-white/50">SIMULATION_GRAPHIC</span>
                      </div>
                    )}

                    <p className="text-[9px] leading-relaxed">
                      This panel emulates media parameters applied dynamically during spider missions.
                    </p>

                    {/* Interactive Button Group with focus indicators */}
                    <div className="flex gap-2 pt-1">
                      <div className={`flex-1 text-center py-1.5 rounded text-[8px] font-bold ${
                        contrast === 'more' ? 'bg-white text-black border-2 border-white' :
                        contrast === 'less' ? 'bg-surface-border/40 text-surface-highlight' : 'bg-primary text-background'
                      }`}>
                        Button A
                      </div>
                      <div className="flex-1 text-center py-1.5 rounded text-[8px] border border-surface-border font-bold">
                        Button B
                      </div>
                    </div>

                    {/* Reduced Motion Warning element */}
                    {!reducedMotion && (
                      <div className="p-2 bg-error/10 border border-error/20 rounded flex items-center gap-1.5 text-[8px] text-error font-mono animate-pulse">
                        <AlertTriangle size={8} /> Pulsing Motion Check
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: Tactical Persona Agents */}
        {step === 3 && (
          <div className="glass-panel p-8 space-y-6 fade-in-up">
            <h2 className="text-sm font-bold uppercase tracking-wider text-on-surface border-b border-surface-border/40 pb-3 flex items-center gap-2">
              <Cpu size={16} className="text-primary" /> Step 3: Select Simulated Audit Persona
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
              {agentPersonas.map((persona) => (
                <button
                  type="button"
                  key={persona.id}
                  onClick={() => setAgent(persona.id)}
                  className={`flex items-start gap-3 cursor-pointer text-left group p-4 rounded-md border transition-all focus:ring-2 focus:ring-primary outline-none ${
                    agent === persona.id 
                      ? 'bg-primary/15 border-primary shadow-neon' 
                      : 'bg-background border-surface-border/50 hover:bg-surface-highlight/30 hover:border-surface-border'
                  }`}
                >
                  <input
                    type="radio"
                    readOnly
                    checked={agent === persona.id}
                    className="mt-0.5 w-4 h-4 border-surface-border text-primary focus:ring-primary bg-background pointer-events-none"
                  />
                  <div>
                    <span className="text-xs font-bold text-on-surface group-hover:text-primary transition-colors">{persona.name}</span>
                    <p className="text-[10px] text-on-surface-variant leading-normal mt-0.5">{persona.desc}</p>
                  </div>
                </button>
              ))}
            </div>

            <div className="flex justify-between pt-6 border-t border-surface-border/40">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="secondary-btn flex items-center gap-2 px-5 py-2.5 text-xs font-bold uppercase tracking-wider cursor-pointer"
              >
                <ChevronLeft size={14} /> Back
              </button>
              
              <button
                type="submit"
                disabled={loading || !url}
                className="primary-btn flex items-center gap-2 px-6 py-2.5 text-xs font-bold uppercase tracking-wider cursor-pointer shadow-glow disabled:opacity-50"
              >
                {loading ? (
                  <div className="w-4 h-4 border-2 border-background border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <Play size={12} className="fill-current" />
                )}
                {loading ? 'Initializing Audit...' : 'Trigger Heuristic Scan'}
              </button>
            </div>
          </div>
        )}

      </form>
    </div>
  );
}
