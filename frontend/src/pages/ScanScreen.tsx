import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { client } from '../api/client.ts';
import { Play, ShieldAlert, Cpu, Layers } from 'lucide-react';

export default function ScanScreen() {
  const navigate = useNavigate();
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

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 pb-32 min-h-screen">
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

      <header className="mb-10 border-b border-surface-border pb-8">
        <h1 className="text-3xl font-heading font-bold text-on-surface">Target Initializer</h1>
        <p className="text-on-surface-variant mt-2 text-sm">Configure spider crawl vectors and simulated agent personas.</p>
      </header>

      {errorMsg && (
        <div className="mb-6 p-4 bg-error/10 border border-error/20 text-error rounded text-xs flex items-center gap-2" role="alert">
          <ShieldAlert size={16} />
          {errorMsg}
        </div>
      )}

      <form onSubmit={handleScan} className="space-y-8">
        {/* Core URL input card */}
        <div className="glass-panel p-8 space-y-6">
          <div className="space-y-2">
            <label htmlFor="target-url" className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Target Website URL</label>
            <input
              id="target-url"
              type="url"
              required
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full bg-background border border-surface-border rounded-md px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary text-on-surface"
            />
          </div>

          {/* Scan Type Selection */}
          <div className="space-y-3 pt-4 border-t border-surface-border/50">
            <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant block">Scan Scope</span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <label className={`flex items-start gap-3 p-4 rounded-md border cursor-pointer transition-all hover:bg-surface-highlight/30 ${scanType === 'single' ? 'bg-primary/10 border-primary' : 'bg-background border-surface-border/50'}`}>
                <input
                  type="radio"
                  name="scan-type"
                  checked={scanType === 'single'}
                  onChange={() => {
                    setScanType('single');
                  }}
                  className="mt-0.5 w-4 h-4 border-surface-border text-primary focus:ring-primary bg-background cursor-pointer"
                />
                <div>
                  <span className="text-xs font-bold text-on-surface">Single Page Scan</span>
                  <p className="text-[10px] text-on-surface-variant leading-normal mt-0.5">Audit only the target URL entry-point route.</p>
                </div>
              </label>

              <label className={`flex items-start gap-3 p-4 rounded-md border cursor-pointer transition-all hover:bg-surface-highlight/30 ${scanType === 'multi' ? 'bg-primary/10 border-primary' : 'bg-background border-surface-border/50'}`}>
                <input
                  type="radio"
                  name="scan-type"
                  checked={scanType === 'multi'}
                  onChange={() => {
                    setScanType('multi');
                  }}
                  className="mt-0.5 w-4 h-4 border-surface-border text-primary focus:ring-primary bg-background cursor-pointer"
                />
                <div>
                  <span className="text-xs font-bold text-on-surface">Multi-Page Deep Scan</span>
                  <p className="text-[10px] text-on-surface-variant leading-normal mt-0.5">Recursively crawl and audit linked paths under the same domain host.</p>
                </div>
              </label>
            </div>
          </div>

          {/* Crawling Depth Limit Slider (visible only for multi) */}
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
              <p className="text-[10px] text-primary/80 font-mono mt-2 bg-primary/5 p-2 rounded border border-primary/20">
                {depth === 2 && "Level 2: Audits landing page and immediate relative links found on the main page."}
                {depth === 3 && "Level 3: Traverses 2 hops away. Thoroughly audits the main structure and sub-directories."}
                {depth === 4 && "Level 4: Traverses 3 hops away. Ideal for mapping large corporate websites or documentation catalogs."}
                {depth === 5 && "Level 5: Maximum crawl depth. Exhaustively scans all reachable internal site paths."}
              </p>
            </div>
          )}

          {/* Scan Speed Strategy */}
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
              {strategy === 'fast' ? 'Crawls target host using parallel page traversals.' : 'Crawls sequentially with a 1.5s delay to prevent rate limit triggers or high server CPU spikes.'}
            </p>
          </div>

          {/* Environmental Simulator Panel */}
          <div className="space-y-6 pt-4 border-t border-surface-border/50">
            <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant block">Environmental Simulator</span>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Left Column: Viewport Selector & Custom Dimensions */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="scan-viewport" className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Simulated Viewport</label>
                  <select
                    id="scan-viewport"
                    value={viewport}
                    onChange={(e) => setViewport(e.target.value)}
                    className="w-full bg-background border border-surface-border rounded-md px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary text-on-surface cursor-pointer font-mono"
                  >
                    <option value="2560x1080">Ultra-Wide Desktop (2560x1080)</option>
                    <option value="1920x1080">Desktop Widescreen (1920x1080)</option>
                    <option value="1280x800">Laptop Standard (1280x800)</option>
                    <option value="1024x768">Tablet Landscape (1024x768)</option>
                    <option value="768x1024">Tablet Portrait (768x1024)</option>
                    <option value="1024x600">Netbook Standard (1024x600)</option>
                    <option value="812x375">Mobile Landscape (812x375)</option>
                    <option value="375x812">Mobile Portrait (375x812)</option>
                    <option value="240x240">Smart Watch Wearable (240x240)</option>
                  </select>
                </div>

                <div className="space-y-2 pt-1">
                  <label htmlFor="scan-zoom" className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Simulated Zoom / DPR</label>
                  <select
                    id="scan-zoom"
                    value={dpr}
                    onChange={(e) => setDpr(e.target.value)}
                    className="w-full bg-background border border-surface-border rounded-md px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary text-on-surface cursor-pointer font-mono"
                  >
                    <option value="1.0">Standard Zoom (100% / 1.0 DPR)</option>
                    <option value="1.25">Enlarged Layout (125% / 1.25 DPR)</option>
                    <option value="1.5">Zoom Level 1.5 (150% / 1.5 DPR)</option>
                    <option value="2.0">Accessibility Zoom (200% / 2.0 DPR)</option>
                    <option value="3.0">Maximum Zoom (300% / 3.0 DPR)</option>
                  </select>
                </div>
              </div>

              {/* Center Column: Throttling & Packet Latency (RTT) */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="scan-network" className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Network Throttling</label>
                  <select
                    id="scan-network"
                    value={network}
                    onChange={(e) => setNetwork(e.target.value)}
                    className="w-full bg-background border border-surface-border rounded-md px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary text-on-surface cursor-pointer font-mono"
                  >
                    <option value="none">No Throttling (High Speed)</option>
                    <option value="5g">Fast 5G / Broadband (50 Mbps)</option>
                    <option value="fast4g">Fast 4G / LTE (15 Mbps)</option>
                    <option value="fast3g">Fast 3G (Average Mobile - 1.5 Mbps)</option>
                    <option value="slow3g">Slow 3G (Low Bandwidth - 400 Kbps)</option>
                    <option value="2g">2G GPRS (Ultra Slow - 50 Kbps)</option>
                    <option value="offline">Offline Mode</option>
                  </select>
                </div>

                <div className="space-y-2 pt-1">
                  <label htmlFor="scan-latency" className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Simulated Packet Latency (RTT)</label>
                  <select
                    id="scan-latency"
                    value={latency}
                    onChange={(e) => setLatency(e.target.value)}
                    className="w-full bg-background border border-surface-border rounded-md px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary text-on-surface cursor-pointer font-mono"
                  >
                    <option value="0">No Latency (0ms)</option>
                    <option value="100">Low Latency (100ms)</option>
                    <option value="500">High Latency (500ms)</option>
                    <option value="2000">Saturation Latency (2000ms)</option>
                  </select>
                </div>
              </div>

              {/* Right Column: Media Features */}
              <div className="space-y-4">
                <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block">System Media Features</span>
                
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
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
                      <label htmlFor="media-contrast" className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant">Contrast Mode</label>
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

                  <div className="space-y-2 pt-1">
                    <label className="flex items-center gap-2 text-xs text-on-surface cursor-pointer">
                      <input
                        type="checkbox"
                        checked={reducedMotion}
                        onChange={(e) => setReducedMotion(e.target.checked)}
                        className="rounded border-surface-border text-primary focus:ring-primary bg-background cursor-pointer"
                      />
                      <span>prefers-reduced-motion</span>
                    </label>
                    
                    <label className="flex items-center gap-2 text-xs text-on-surface cursor-pointer">
                      <input
                        type="checkbox"
                        checked={forcedColors}
                        onChange={(e) => setForcedColors(e.target.checked)}
                        className="rounded border-surface-border text-primary focus:ring-primary bg-background cursor-pointer"
                      />
                      <span>forced-colors: active</span>
                    </label>

                    <label className="flex items-center gap-2 text-xs text-on-surface cursor-pointer">
                      <input
                        type="checkbox"
                        checked={reducedData}
                        onChange={(e) => setReducedData(e.target.checked)}
                        className="rounded border-surface-border text-primary focus:ring-primary bg-background cursor-pointer"
                      />
                      <span>prefers-reduced-data</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Tactical agent configuration (8 agents) */}
        <div className="glass-panel p-8 space-y-6">
          <h2 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant flex items-center gap-2 border-b border-surface-border/40 pb-4">
            <Cpu size={14} className="text-primary" /> Tactical Persona Agents
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            {agentPersonas.map((persona) => (
              <label key={persona.id} className="flex items-start gap-3 cursor-pointer group p-3 rounded-md hover:bg-surface-highlight/30 border border-transparent hover:border-surface-border/50 transition-all">
                <input
                  type="radio"
                  name="agent-selection"
                  checked={agent === persona.id}
                  onChange={() => setAgent(persona.id)}
                  className="mt-0.5 w-4 h-4 border-surface-border text-primary focus:ring-primary bg-background cursor-pointer"
                />
                <div>
                  <span className="text-xs font-bold text-on-surface group-hover:text-primary transition-colors">{persona.name}</span>
                  <p className="text-[10px] text-on-surface-variant leading-normal mt-0.5">{persona.desc}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Scan launch trigger */}
        <button
          type="submit"
          disabled={loading}
          className="w-full primary-btn py-4 flex items-center justify-center gap-2 cursor-pointer transition-all shadow-glow text-sm font-bold uppercase tracking-widest disabled:opacity-50"
        >
          {loading ? (
            <div className="w-5 h-5 border-2 border-background border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <Play size={16} className="fill-current" />
          )}
          {loading ? 'Initializing Spider Analysis...' : 'Trigger Heuristic Scan'}
        </button>
      </form>
    </div>
  );
}
