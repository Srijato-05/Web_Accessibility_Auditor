import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { HelpCircle, FileText, CheckCircle, MessageSquare, AlertCircle, ArrowLeft } from 'lucide-react';

export default function Help() {
  const navigate = useNavigate();
  const [ticketSubject, setTicketSubject] = useState('');
  const [ticketMsg, setTicketMsg] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketSubject || !ticketMsg) return;
    setSuccess(true);
    setTicketSubject('');
    setTicketMsg('');
    setTimeout(() => setSuccess(false), 4000);
  };

  const wcagRules = [
    { level: 'Level A', description: 'Minimum compliance level. Handles critical keyboard traps, page titles, alternative text for images, and basic media transcripts.' },
    { level: 'Level AA', description: 'Standard acceptable compliance level for most organizations. Covers color contrasts (4.5:1), navigation menus consistency, text resizing, and form validation error guidance.' },
    { level: 'Level AAA', description: 'Optimal accessibility level. Demands high-contrast ratios (7:1), skip navigation shortcuts, section headings hierarchy, and alternate audio/visual options.' }
  ];

  const faqs = [
    { q: 'How does Sentinel audit compliance?', a: 'Sentinel checks your pages using both standard automated rules (Axe-Core) and dynamic heuristics run by active Chrome browsers (e.g. keyboard trapping, accessibility tags completeness) to compile diagnostic reports.' },
    { q: 'What is Deep Audit Mode?', a: 'Standard scans execute rapid parsing check heuristics. Deep Audit runs a thorough DOM traversal checking visual alignments, dynamic contrast changes, and interactive form structures.' },
    { q: 'How do I export CSV reports?', a: 'Head to Settings (Profile) page, and select "Export Complete Organization Logs" to download your complete audit logs in CSV format.' }
  ];

  return (
    <div className="max-w-5xl mx-auto px-6 py-10 pb-32 min-h-screen">
      <header className="mb-10 border-b border-surface-border pb-8">
        <button onClick={() => navigate('/profile')} className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors mb-6 text-xs uppercase tracking-widest font-bold focus:ring-2 focus:ring-primary outline-none">
           <ArrowLeft size={16} /> Back to Profile
        </button>
        <h1 className="text-3xl font-heading font-bold text-on-surface">Help & Documentation</h1>
        <p className="text-on-surface-variant mt-2 text-sm">Understand Web Content Accessibility Guidelines (WCAG) rules and system setup.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* WCAG Guidelines and FAQs */}
        <div className="lg:col-span-2 space-y-8">
          {/* WCAG Compliance cards */}
          <section aria-labelledby="wcag-ref-title" className="space-y-4">
            <h2 id="wcag-ref-title" className="text-sm font-bold uppercase tracking-widest text-primary flex items-center gap-2">
              <FileText size={16} aria-hidden="true" /> WCAG Compliance Levels Reference
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {wcagRules.map((rule, idx) => (
                <div key={idx} className="flat-panel p-5 space-y-2 border-t-2 border-t-primary/45 bg-surface-highlight/10">
                  <span className="font-mono text-xs font-bold text-primary uppercase">{rule.level}</span>
                  <p className="text-xs text-on-surface-variant leading-relaxed mt-2">{rule.description}</p>
                </div>
              ))}
            </div>
          </section>

          {/* FAQ section */}
          <section aria-labelledby="faq-title" className="space-y-4 pt-6 border-t border-surface-border/50">
            <h2 id="faq-title" className="text-sm font-bold uppercase tracking-widest text-primary flex items-center gap-2">
              <HelpCircle size={16} aria-hidden="true" /> Frequently Asked Questions
            </h2>
            <div className="space-y-4">
              {faqs.map((faq, idx) => (
                <div key={idx} className="flat-panel p-6 bg-surface-highlight/10 space-y-2">
                  <h3 className="text-sm font-bold text-on-surface flex items-start gap-2">
                    <span className="text-primary font-bold">Q:</span> {faq.q}
                  </h3>
                  <p className="text-xs text-on-surface-variant leading-relaxed pl-5">
                    {faq.a}
                  </p>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Support Ticket Sidebar */}
        <div className="col-span-1 space-y-6">
          <div className="glass-panel p-6 border-t-4 border-t-secondary relative">
            <h2 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant flex items-center gap-2 mb-4">
              <MessageSquare size={14} className="text-secondary" aria-hidden="true" /> Help Desk Ticket
            </h2>
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
                    rows={4}
                    placeholder="Explain the problem..."
                    value={ticketMsg}
                    onChange={(e) => setTicketMsg(e.target.value)}
                    className="w-full bg-background border border-surface-border rounded-md px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-primary text-on-surface resize-none"
                  ></textarea>
                </div>
                <button type="submit" className="w-full secondary-btn font-bold py-2 text-xs transition-all hover:bg-secondary hover:text-background">
                  Submit Support Ticket
                </button>
              </form>
            )}
          </div>

          <div className="glass-panel p-5 flex items-start gap-3 bg-surface-highlight/20 border-none">
            <AlertCircle size={18} className="text-on-surface-variant shrink-0 mt-0.5" aria-hidden="true" />
            <p className="text-[10px] text-on-surface-variant leading-normal">
              Sentinel is currently operating under public preview tier. Contact local infrastructure team for active credential allocations.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
