import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  HelpCircle, 
  FileText, 
  CheckCircle, 
  MessageSquare, 
  AlertCircle, 
  ArrowLeft,
  BookOpen,
  Keyboard,
  Cpu,
  ExternalLink,
  ChevronDown,
  Info,
  CheckSquare,
  Square
} from 'lucide-react';

export default function Help() {
  const navigate = useNavigate();
  const [ticketSubject, setTicketSubject] = useState('');
  const [ticketMsg, setTicketMsg] = useState('');
  const [success, setSuccess] = useState(false);
  const [activeFaq, setActiveFaq] = useState<number | null>(null);
  
  // Self-Audit Checklist State
  const [checklist, setChecklist] = useState<{ [key: string]: boolean }>({
    '1.1.1': false,
    '1.4.3': false,
    '1.4.6': false,
    '2.1.1': false,
    '2.1.2': false,
    '2.4.1': false,
    '2.4.7': false,
    '3.3.3': false,
  });

  const toggleChecklistItem = (id: string) => {
    setChecklist(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketSubject || !ticketMsg) return;
    setSuccess(true);
    setTicketSubject('');
    setTicketMsg('');
    setTimeout(() => setSuccess(false), 4000);
  };

  // Safe scroll handler to bypass HashRouter link redirection
  const handleScrollTo = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      // Move programmatic focus to the element for screen reader accessibility
      element.setAttribute('tabindex', '-1');
      element.focus();
    }
  };

  const wcagSuccessCriteria = [
    {
      level: 'Level A (Essential Conformance)',
      color: 'border-t-error/60 bg-error/5',
      title: 'Core Blockers & Screen Reader Assist',
      desc: 'Mandatory standard to remove absolute showstoppers. Failure here leaves the site completely unusable for keyboard-only and screen reader users.',
      criteria: [
        { 
          code: '1.1.1 Non-Text Content', 
          url: 'https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html', 
          detail: 'Provide equivalent text alternatives for any non-text component (e.g. images, audio, buttons). Blank alt attributes (alt="") should be used for purely decorative images to instruct screen readers to ignore them.' 
        },
        { 
          code: '2.1.1 Keyboard Accessibility', 
          url: 'https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html', 
          detail: 'All interactive elements (buttons, inputs, sliders, menus) must be operable via standard Tab, Shift+Tab, Enter, and Space keys. Do not lock users into mouse-only coordinates.' 
        },
        { 
          code: '2.1.2 No Keyboard Trap', 
          url: 'https://www.w3.org/WAI/WCAG21/Understanding/no-keyboard-trap.html', 
          detail: 'Focus must never get stuck inside slide-out drawers, modal dialogs, or dropdown overlays. If focus is locked within a dialog, the user must be able to escape using the Escape key.' 
        },
        { 
          code: '2.4.1 Bypass Blocks', 
          url: 'https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html', 
          detail: 'Provide a keyboard-navigable "Skip to main content" link at the very top of each page. This allows screen readers and keyboard users to skip header navigation bar list items.' 
        }
      ]
    },
    {
      level: 'Level AA (Standard Conformance)',
      color: 'border-t-warning/60 bg-warning/5',
      title: 'Target Benchmark for Modern Websites',
      desc: 'The baseline legal standard for commercial, government, and educational websites globally. Addresses mainstream accessibility barriers.',
      criteria: [
        { 
          code: '1.4.3 Contrast (Minimum)', 
          url: 'https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html', 
          detail: 'Standard body text (below 18pt/24px) must have a contrast ratio of at least 4.5:1 against its background. Large scale text (above 18pt/24px) requires at least 3:1.' 
        },
        { 
          code: '1.4.4 Resize Text', 
          url: 'https://www.w3.org/WAI/WCAG21/Understanding/resize-text.html', 
          detail: 'Users must be able to zoom text up to 200% via browser magnification settings without causing overlapping texts, content truncations, or side-scrolling layouts.' 
        },
        { 
          code: '2.4.7 Focus Visible', 
          url: 'https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html', 
          detail: 'Any element currently holding keyboard focus must display a distinct visual outline. Removing outlines (outline: none) without a custom high-contrast style is a direct violation.' 
        },
        { 
          code: '3.3.3 Error Suggestion', 
          url: 'https://www.w3.org/WAI/WCAG21/Understanding/error-suggestion.html', 
          detail: 'If a form input fails validation, do not just color the border red. The site must provide written suggestions explaining how the input must be corrected.' 
        }
      ]
    },
    {
      level: 'Level AAA (Optimal Conformance)',
      color: 'border-t-primary/60 bg-primary/5',
      title: 'Optimal Usability & Maximum Inclusivity',
      desc: 'The gold standard for accessibility, ensuring a premium experience for individuals with severe visual, cognitive, or physical limitations.',
      criteria: [
        { 
          code: '1.4.6 Contrast (Enhanced)', 
          url: 'https://www.w3.org/WAI/WCAG21/Understanding/contrast-enhanced.html', 
          detail: 'Standard text must meet a contrast threshold of at least 7:1. Large text must meet a minimum of 4.5:1. Essential icon strokes should also respect these parameters.' 
        },
        { 
          code: '1.4.8 Visual Presentation', 
          url: 'https://www.w3.org/WAI/WCAG21/Understanding/visual-presentation.html', 
          detail: 'The user must retain controls to select custom background/text colors, adjust paragraph spacing (at least 1.5x font size), and toggle page width restrictions.' 
        },
        { 
          code: '2.2.3 No Timing', 
          url: 'https://www.w3.org/WAI/WCAG21/Understanding/no-timing.html', 
          detail: 'Avoid time-outs or countdown clocks. Content must not automatically expire or force a page reload unless absolutely necessary for security (e.g. banking logs).' 
        },
        { 
          code: '2.4.9 Link Purpose', 
          url: 'https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-link-only.html', 
          detail: 'Every link text must clearly describe its destination standalone. Avoid generic link text like "click here" or "learn more". Use descriptive labels like "Download Q4 CSV Audit Logs".' 
        }
      ]
    }
  ];

  const agentDetails = [
    { 
      id: 'desktop_chrome', 
      name: 'Default Desktop Chrome', 
      desc: 'Audits the default DOM layout at 1920x1080 resolution. Emulates typical user flows, verifying core accessibility tree node attachments and base ARIA landmark groupings.' 
    },
    { 
      id: 'secure_auditor', 
      name: 'Secure Auditor Bot', 
      desc: 'Launches sandboxed browser sessions with customized headers and cookies to bypass security challenges, scraping firewalled pages and internal directories for private team audits.' 
    },
    { 
      id: 'screen_reader', 
      name: 'Screen Reader Assist', 
      desc: 'Simulates screen reader processing logic (NVDA/JAWS). Flags missing headers, incorrect aria-describedby associations, invalid label-for attributes, and empty links.' 
    },
    { 
      id: 'mobile_chrome', 
      name: 'Mobile Chrome Emulator', 
      desc: 'Tests responsiveness and element reflow at a tight mobile viewport (375x812). Checks if interactive tap targets are at least 48x48px and spaced to avoid double taps.' 
    },
    { 
      id: 'keyboard_only', 
      name: 'Keyboard-Only Traversal', 
      desc: 'Traces keyboard tab flows programmatically. Flags focus traps, skips non-focusable layout icons, validates that interactive cards are focusable, and logs tab order maps.' 
    },
    { 
      id: 'colorblind_deuteranopia', 
      name: 'Colorblind Viewer', 
      desc: 'Applies visual filters emulating green-cone vision deficiencies. Checks if information is presented purely via color (e.g. error text that has no icon or warning label).' 
    },
    { 
      id: 'low_vision_zoom', 
      name: 'Low Vision (Zoom 200%)', 
      desc: 'Scales the browser viewport by 2x (Device Pixel Ratio 2.0). Audits horizontal scrolling behavior to check that text remains readable without forcing horizontal page panning.' 
    },
    { 
      id: 'seo_crawler', 
      name: 'Search Engine Crawler', 
      desc: 'Validates tag hierarchy. Checks that each page has exactly one h1 tag, headers follow sequential order (h1 -> h2 -> h3), and links contain valid anchor descriptive texts.' 
    }
  ];

  const faqs = [
    { 
      q: 'How does A11yAudit evaluate pages?', 
      a: 'A11yAudit uses a hybrid pipeline. First, it triggers an automated Axe-Core analyzer script to parse standard code violations. Second, it launches interactive simulation bots (keyboard-only focus tracks, low-contrast filters) to evaluate layout reflow and check that users with assistive tech can interact without hitches.' 
    },
    { 
      q: 'What is the compliance calculation formula?', 
      a: 'Each scanned element is classified based on its WCAG Level (A, AA, AAA). Overall page compliance represents the proportion of passing elements over the total analyzed interactive landmarks. An overall rating of AAA requires 100% adherence to all Level A, AA, and AAA rules.' 
    },
    { 
      q: 'How do I resolve keyboard trapping?', 
      a: 'Keyboard traps happen when focus enters an overlay (like a modal dialog) and cannot be tabbed out of. Resolve this by adding key listeners on Tab and Esc keys to cycle focus back to the opening trigger or dismiss the window, maintaining focus focus-state coherence.' 
    },
    { 
      q: 'Why does Alt+R toggle not respond on my PC?', 
      a: 'On Windows, Alt+R is heavily hijacked by system utility programs (like AMD Radeon Software for game overlays). To bypass this, we support Alt+M (Motion) as a fallback. You can also disable shortcut key capture globally on the Profile page.' 
    }
  ];

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 pb-32 min-h-screen fade-in-up">
      {/* Page Header */}
      <header className="mb-10 border-b border-surface-border pb-8">
        <button 
          onClick={() => navigate('/profile')} 
          className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors mb-6 text-xs uppercase tracking-widest font-bold focus:ring-2 focus:ring-primary outline-none"
        >
          <ArrowLeft size={16} /> Back to Profile
        </button>
        <h1 className="text-3xl font-heading font-bold text-on-surface">Help, Documentation & WCAG Reference</h1>
        <p className="text-on-surface-variant mt-2 text-sm max-w-3xl leading-relaxed">
          Comprehensive compliance mapping manual for A11yAudit, detailing WCAG 2.1 AAA success criteria, keyboard control configurations, simulator specifications, and support channels.
        </p>

        {/* Quick Jump Anchors - Fixed via custom JS scroll handlers */}
        <nav aria-label="Documentation sections jump navigation" className="mt-6 flex flex-wrap gap-2 text-xs">
          <span className="text-on-surface-variant font-bold self-center mr-2">Quick Jump:</span>
          <button onClick={() => handleScrollTo('wcag-levels')} className="px-3 py-1.5 bg-surface-container-high hover:bg-surface-border border border-surface-border rounded-md text-on-surface transition-colors font-bold focus:ring-2 focus:ring-primary cursor-pointer outline-none">WCAG Standards</button>
          <button onClick={() => handleScrollTo('shortcuts')} className="px-3 py-1.5 bg-surface-container-high hover:bg-surface-border border border-surface-border rounded-md text-on-surface transition-colors font-bold focus:ring-2 focus:ring-primary cursor-pointer outline-none">Keyboard Shortcuts</button>
          <button onClick={() => handleScrollTo('telemetry-agents')} className="px-3 py-1.5 bg-surface-container-high hover:bg-surface-border border border-surface-border rounded-md text-on-surface transition-colors font-bold focus:ring-2 focus:ring-primary cursor-pointer outline-none">Telemetry Agents</button>
          <button onClick={() => handleScrollTo('audit-checklist')} className="px-3 py-1.5 bg-surface-container-high hover:bg-surface-border border border-surface-border rounded-md text-on-surface transition-colors font-bold focus:ring-2 focus:ring-primary cursor-pointer outline-none">Self-Audit Checklist</button>
          <button onClick={() => handleScrollTo('faq-section')} className="px-3 py-1.5 bg-surface-container-high hover:bg-surface-border border border-surface-border rounded-md text-on-surface transition-colors font-bold focus:ring-2 focus:ring-primary cursor-pointer outline-none">FAQs</button>
          <button onClick={() => handleScrollTo('resources')} className="px-3 py-1.5 bg-surface-container-high hover:bg-surface-border border border-surface-border rounded-md text-on-surface transition-colors font-bold focus:ring-2 focus:ring-primary cursor-pointer outline-none">Resources</button>
          <button onClick={() => handleScrollTo('support-ticket')} className="px-3 py-1.5 bg-surface-container-high hover:bg-surface-border border border-surface-border rounded-md text-on-surface transition-colors font-bold focus:ring-2 focus:ring-primary cursor-pointer outline-none">Support Ticket</button>
        </nav>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Main Content Areas */}
        <div className="lg:col-span-2 space-y-12">
          
          {/* Section 1: WCAG Guidelines Reference */}
          <section id="wcag-levels" aria-labelledby="wcag-ref-title" className="space-y-6">
            <h2 id="wcag-ref-title" className="text-sm font-bold uppercase tracking-widest text-primary flex items-center gap-2 border-b border-surface-border/50 pb-2">
              <FileText size={16} aria-hidden="true" className="text-primary" /> WCAG 2.1 Compliance Levels
            </h2>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              The Web Content Accessibility Guidelines (WCAG) define requirements for designers and developers to improve accessibility for people with disabilities. Requirements are organized across three levels of conformance.
            </p>

            <div className="space-y-6">
              {wcagSuccessCriteria.map((level, idx) => (
                <div key={idx} className={`flat-panel p-6 border-t-4 ${level.color} space-y-4`}>
                  <div className="flex justify-between items-start flex-wrap gap-2">
                    <div>
                      <h3 className="font-heading font-bold text-sm text-on-surface">{level.level}</h3>
                      <p className="text-[11px] text-primary font-bold mt-0.5">{level.title}</p>
                    </div>
                  </div>
                  <p className="text-xs text-on-surface-variant leading-relaxed">{level.desc}</p>
                  
                  <div className="space-y-3 pt-2">
                    <span className="text-[10px] uppercase tracking-wider font-bold text-on-surface block">Key Success Criteria Checked:</span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {level.criteria.map((item, cIdx) => (
                        <div key={cIdx} className="bg-background/40 p-3 rounded border border-surface-border/40 text-xs flex flex-col justify-between">
                          <div>
                            <a 
                              href={item.url} 
                              target="_blank" 
                              rel="noopener noreferrer" 
                              className="text-xs font-bold text-primary hover:underline flex items-center gap-1 focus:ring-1 focus:ring-primary outline-none"
                              aria-label={`Understand Success Criterion ${item.code} (opens in new tab)`}
                            >
                              {item.code} <ExternalLink size={10} aria-hidden="true" />
                            </a>
                            <p className="text-[10px] text-on-surface-variant mt-1.5 leading-normal">{item.detail}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Section 2: Keyboard Shortcuts Guide */}
          <section id="shortcuts" aria-labelledby="kbd-ref-title" className="space-y-6 pt-4">
            <h2 id="kbd-ref-title" className="text-sm font-bold uppercase tracking-widest text-primary flex items-center gap-2 border-b border-surface-border/50 pb-2">
              <Keyboard size={16} aria-hidden="true" className="text-primary" /> Accessibility Keyboard Shortcuts
            </h2>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              To support keyboard-only users and accelerate testing traversals, A11yAudit implements capture-phase keyboard shortcuts. These commands bypass active focus elements and are captured globally.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flat-panel p-4 bg-surface-highlight/10 flex justify-between items-center text-xs">
                <div>
                  <h4 className="font-bold text-on-surface">Cycle Theme Mode</h4>
                  <p className="text-[10px] text-on-surface-variant mt-1">Switches Cyberpunk, High-Contrast, and Colorblind themes.</p>
                </div>
                <kbd className="px-2.5 py-1 bg-surface-container-high border border-surface-border rounded text-[10px] font-mono font-bold text-primary shadow-sm">Alt + T</kbd>
              </div>
              <div className="flat-panel p-4 bg-surface-highlight/10 flex justify-between items-center text-xs">
                <div>
                  <h4 className="font-bold text-on-surface">Navigate to Dashboard</h4>
                  <p className="text-[10px] text-on-surface-variant mt-1">Jumps to telemetry data streams and site logs.</p>
                </div>
                <kbd className="px-2.5 py-1 bg-surface-container-high border border-surface-border rounded text-[10px] font-mono font-bold text-primary shadow-sm">Alt + D</kbd>
              </div>
              <div className="flat-panel p-4 bg-surface-highlight/10 flex justify-between items-center text-xs">
                <div>
                  <h4 className="font-bold text-on-surface">Navigate to Help</h4>
                  <p className="text-[10px] text-on-surface-variant mt-1">Redirects directly to this compliance reference manual.</p>
                </div>
                <kbd className="px-2.5 py-1 bg-surface-container-high border border-surface-border rounded text-[10px] font-mono font-bold text-primary shadow-sm">Alt + H</kbd>
              </div>
              <div className="flat-panel p-4 bg-surface-highlight/10 flex justify-between items-center text-xs">
                <div>
                  <h4 className="font-bold text-on-surface">Start New Scan</h4>
                  <p className="text-[10px] text-on-surface-variant mt-1">Redirects to the Target Initializer console.</p>
                </div>
                <kbd className="px-2.5 py-1 bg-surface-container-high border border-surface-border rounded text-[10px] font-mono font-bold text-primary shadow-sm">Alt + S</kbd>
              </div>
              <div className="flat-panel p-4 bg-surface-highlight/10 flex justify-between items-center text-xs">
                <div>
                  <h4 className="font-bold text-on-surface">Toggle Reduced Motion</h4>
                  <p className="text-[10px] text-on-surface-variant mt-1">Freezes page transitions, loading spinners, and pulse effects.</p>
                </div>
                <div className="flex gap-1.5 items-center">
                  <kbd className="px-2 py-1 bg-surface-container-high border border-surface-border rounded text-[10px] font-mono font-bold text-primary shadow-sm">Alt + R</kbd>
                  <span className="text-[9px] text-on-surface-variant uppercase font-bold">or</span>
                  <kbd className="px-2 py-1 bg-surface-container-high border border-surface-border rounded text-[10px] font-mono font-bold text-primary shadow-sm">Alt + M</kbd>
                </div>
              </div>
              <div className="flat-panel p-4 bg-surface-highlight/10 flex justify-between items-center text-xs">
                <div>
                  <h4 className="font-bold text-on-surface">Toggle Dyslexia Font</h4>
                  <p className="text-[10px] text-on-surface-variant mt-1">Applies OpenDyslexic typeface and increases spacing.</p>
                </div>
                <kbd className="px-2.5 py-1 bg-surface-container-high border border-surface-border rounded text-[10px] font-mono font-bold text-primary shadow-sm">Alt + F</kbd>
              </div>
              <div className="flat-panel p-4 bg-surface-highlight/10 flex justify-between items-center text-xs md:col-span-2">
                <div>
                  <h4 className="font-bold text-on-surface">Focus Active Search Input</h4>
                  <p className="text-[10px] text-on-surface-variant mt-1">Focuses search elements or filter fields on the active route.</p>
                </div>
                <kbd className="px-2.5 py-1 bg-surface-container-high border border-surface-border rounded text-[10px] font-mono font-bold text-primary shadow-sm">Alt + K</kbd>
              </div>
            </div>
          </section>

          {/* Section 3: Telemetry Simulators & Crawler Personas */}
          <section id="telemetry-agents" aria-labelledby="agents-title" className="space-y-6 pt-4">
            <h2 id="agents-title" className="text-sm font-bold uppercase tracking-widest text-primary flex items-center gap-2 border-b border-surface-border/50 pb-2">
              <Cpu size={16} aria-hidden="true" className="text-primary" /> Heuristic Telemetry Simulators
            </h2>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              When executing a crawler audit, A11yAudit deploys custom-configured headless Chromium engines to interact with the DOM under various environmental profiles. This identifies issues that static code parsing misses.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {agentDetails.map((agent, index) => (
                <div key={index} className="flat-panel p-4 bg-surface-highlight/5 border border-surface-border/40 flex flex-col justify-between">
                  <div>
                    <span className="font-mono text-[10px] font-bold text-primary uppercase">{agent.name}</span>
                    <p className="text-[11px] text-on-surface-variant leading-relaxed mt-2">{agent.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Section 3b: Interactive Audit Checklist */}
          <section id="audit-checklist" aria-labelledby="checklist-title" className="space-y-6 pt-4">
            <h2 id="checklist-title" className="text-sm font-bold uppercase tracking-widest text-primary flex items-center gap-2 border-b border-surface-border/50 pb-2">
              <CheckSquare size={16} aria-hidden="true" className="text-primary" /> Self-Audit Compliance Checklist
            </h2>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Use this interactive check slate to trace basic elements on your site to evaluate core accessibility before launching automated scraper crawlers.
            </p>
            <div className="flat-panel p-6 bg-surface-highlight/5 border border-surface-border/40 space-y-4">
              <div className="grid grid-cols-1 gap-3">
                {[
                  { id: '1.1.1', text: 'All descriptive images have functional alternative tags (alt="text description").' },
                  { id: '1.4.3', text: 'Contrast ratio matches or exceeds 4.5:1 for standard page text nodes.' },
                  { id: '1.4.6', text: 'Contrast ratio matches or exceeds 7:1 for enhanced AAA compliance requirements.' },
                  { id: '2.1.1', text: 'All headers, sidebars, buttons, and settings are fully navigable using Tab keys.' },
                  { id: '2.1.2', text: 'Focus never gets trapped inside dropdown select boxes or modals without clear exits.' },
                  { id: '2.4.1', text: 'A keyboard bypass shortcut ("Skip Link") is active on root page load headers.' },
                  { id: '2.4.7', text: 'Visible blue/colored borders outline active elements on tab focus.' },
                  { id: '3.3.3', text: 'Input error alerts explain validation parameters in text formatting.' }
                ].map((item) => {
                  const isChecked = checklist[item.id];
                  return (
                    <button
                      key={item.id}
                      onClick={() => toggleChecklistItem(item.id)}
                      className="w-full text-left p-3.5 bg-background/50 rounded border border-surface-border/50 hover:bg-surface-highlight/10 hover:border-primary/50 transition-all flex items-start gap-3 text-xs text-on-surface cursor-pointer focus:ring-2 focus:ring-primary outline-none"
                    >
                      <span className="text-primary shrink-0 mt-0.5">
                        {isChecked ? <CheckCircle size={16} className="fill-current text-primary" /> : <Square size={16} />}
                      </span>
                      <div>
                        <span className="font-bold font-mono text-[10px] uppercase text-primary block">WCAG {item.id}</span>
                        <span className="text-on-surface-variant text-[11px] leading-normal">{item.text}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </section>

          {/* Section 4: Resource Library */}
          <section id="resources" aria-labelledby="resources-title" className="space-y-6 pt-4">
            <h2 id="resources-title" className="text-sm font-bold uppercase tracking-widest text-primary flex items-center gap-2 border-b border-surface-border/50 pb-2">
              <BookOpen size={16} aria-hidden="true" className="text-primary" /> External References & Standards
            </h2>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Consult these official resources for deep documentation, tool kits, and guidelines on developing accessible web products:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <a 
                href="https://www.w3.org/WAI/" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="flat-panel p-5 bg-surface-highlight/10 hover:bg-surface-highlight/20 border-none flex flex-col justify-between text-left group focus:ring-2 focus:ring-primary outline-none"
                aria-label="W3C Web Accessibility Initiative portal (opens in a new tab)"
              >
                <div>
                  <h4 className="font-bold text-xs text-on-surface group-hover:text-primary transition-colors flex items-center gap-1">
                    W3C WAI Guidelines <ExternalLink size={12} aria-hidden="true" />
                  </h4>
                  <p className="text-[10px] text-on-surface-variant mt-2 leading-relaxed">Official Web Accessibility Initiative standard documentations and guides.</p>
                </div>
              </a>
              <a 
                href="https://webaim.org/" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="flat-panel p-5 bg-surface-highlight/10 hover:bg-surface-highlight/20 border-none flex flex-col justify-between text-left group focus:ring-2 focus:ring-primary outline-none"
                aria-label="WebAIM accessibility portal (opens in a new tab)"
              >
                <div>
                  <h4 className="font-bold text-xs text-on-surface group-hover:text-primary transition-colors flex items-center gap-1">
                    WebAIM Portal <ExternalLink size={12} aria-hidden="true" />
                  </h4>
                  <p className="text-[10px] text-on-surface-variant mt-2 leading-relaxed">Comprehensive accessibility articles, checklists, and color checkers.</p>
                </div>
              </a>
              <a 
                href="https://github.com/dequelabs/axe-core" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="flat-panel p-5 bg-surface-highlight/10 hover:bg-surface-highlight/20 border-none flex flex-col justify-between text-left group focus:ring-2 focus:ring-primary outline-none"
                aria-label="Axe-Core developer GitHub repository (opens in a new tab)"
              >
                <div>
                  <h4 className="font-bold text-xs text-on-surface group-hover:text-primary transition-colors flex items-center gap-1">
                    Axe-Core Repository <ExternalLink size={12} aria-hidden="true" />
                  </h4>
                  <p className="text-[10px] text-on-surface-variant mt-2 leading-relaxed">Open-source automated audit engine rules and developer frameworks.</p>
                </div>
              </a>
            </div>
          </section>

          {/* Section 5: FAQs */}
          <section id="faq-section" aria-labelledby="faq-title" className="space-y-6 pt-4">
            <h2 id="faq-title" className="text-sm font-bold uppercase tracking-widest text-primary flex items-center gap-2 border-b border-surface-border/50 pb-2">
              <HelpCircle size={16} aria-hidden="true" className="text-primary" /> Frequently Asked Questions
            </h2>
            <div className="space-y-3">
              {faqs.map((faq, idx) => {
                const isOpen = activeFaq === idx;
                return (
                  <div key={idx} className="flat-panel bg-surface-highlight/10 overflow-hidden">
                    <button 
                      onClick={() => setActiveFaq(isOpen ? null : idx)}
                      aria-expanded={isOpen}
                      className="w-full p-5 text-left font-bold text-xs text-on-surface flex justify-between items-center hover:bg-surface-highlight/20 transition-colors focus:ring-2 focus:ring-primary outline-none cursor-pointer"
                    >
                      <span className="flex items-center gap-2">
                        <span className="text-primary font-bold font-mono">Q{idx+1}:</span> {faq.q}
                      </span>
                      <ChevronDown size={14} className={`text-on-surface-variant transition-transform ${isOpen ? 'rotate-180' : ''}`} aria-hidden="true" />
                    </button>
                    {isOpen && (
                      <div className="p-5 pt-0 text-xs text-on-surface-variant leading-relaxed border-t border-surface-border/20 bg-background/25">
                        {faq.a}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>

        </div>

        {/* Sidebar Helpdesk & Status Panel */}
        <div id="support-ticket" className="col-span-1 space-y-6 lg:sticky lg:top-4">
          
          <div className="glass-panel p-6 border-t-4 border-t-secondary relative bg-surface-container-low">
            <h2 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant flex items-center gap-2 mb-4">
              <MessageSquare size={14} className="text-secondary" aria-hidden="true" /> Help Desk Ticket
            </h2>
            <p className="text-[11px] text-on-surface-variant leading-relaxed mb-4">
              Encountered a bug or compliance anomaly? Submit a diagnostic ticket directly to our engineers.
            </p>
            {success ? (
              <div className="p-4 bg-primary/10 border border-primary/20 text-primary rounded text-xs flex items-center gap-2 animate-pulse" role="status">
                <CheckCircle size={16} aria-hidden="true" /> Support request filed successfully!
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1">
                  <label htmlFor="ticket-subj" className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Subject</label>
                  <input
                    id="ticket-subj"
                    type="text"
                    required
                    placeholder="Brief summary..."
                    value={ticketSubject}
                    onChange={(e) => setTicketSubject(e.target.value)}
                    className="w-full bg-background border border-surface-border rounded-md px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-primary text-on-surface"
                  />
                </div>
                <div className="space-y-1">
                  <label htmlFor="ticket-desc" className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Explanation</label>
                  <textarea
                    id="ticket-desc"
                    required
                    rows={5}
                    placeholder="Explain the problem..."
                    value={ticketMsg}
                    onChange={(e) => setTicketMsg(e.target.value)}
                    className="w-full bg-background border border-surface-border rounded-md px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-primary text-on-surface resize-none"
                  ></textarea>
                </div>
                <button type="submit" className="w-full secondary-btn font-bold py-2.5 text-xs transition-all hover:bg-secondary hover:text-background cursor-pointer">
                  Submit Support Ticket
                </button>
              </form>
            )}
          </div>

          <div className="glass-panel p-5 flex items-start gap-3 bg-surface-highlight/20 border-none bg-surface-container-low">
            <AlertCircle size={18} className="text-on-surface-variant shrink-0 mt-0.5" aria-hidden="true" />
            <p className="text-[10px] text-on-surface-variant leading-normal">
              A11yAudit is currently operating under public preview tier. Contact local infrastructure team for active credential allocations.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
