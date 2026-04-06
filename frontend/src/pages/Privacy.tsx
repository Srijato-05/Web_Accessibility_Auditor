import { useNavigate } from 'react-router-dom';
import { ShieldCheck, ArrowLeft, Lock, Database } from 'lucide-react';

export default function Privacy() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background text-on-surface p-8 max-w-4xl mx-auto pb-32">
      <header className="mb-8 border-b border-outline-variant/15 pb-8">
        <button onClick={() => navigate('/profile')} className="flex items-center gap-2 text-on-surface-variant hover:text-on-surface transition-colors mb-6 text-xs uppercase tracking-widest font-bold">
           <ArrowLeft size={16} /> Back to Profile
        </button>
        <div className="flex items-center gap-3">
            <div className="bg-primary/10 text-primary p-2 rounded-md border border-primary/40 shadow-ambient">
                <ShieldCheck size={24} />
            </div>
            <h1 className="text-display font-medium">Privacy & Security</h1>
        </div>
        <p className="text-on-surface-variant text-lg mt-2 tracking-wide">Luminescent Auditor organizational compliance policies.</p>
      </header>

      <div className="space-y-8">
         <section className="glass-panel p-8 bg-surface-container-low shadow-ambient border-primary/20">
            <h2 className="text-xl font-heading mb-4 flex items-center gap-2 text-primary"><Lock size={20} /> Data Security</h2>
            <div className="space-y-4 text-on-surface-variant leading-relaxed">
               <p>All heuristic scans operate using isolated execution contexts. Source code trees injected into the AST verification pipeline are never retained longer than active session requirements dictate.</p>
               <p>Automated database commits run fully localized and are strictly scrubbed of zero-day structural intelligence parameters outside of standard WCAG flagging matrices.</p>
            </div>
         </section>

         <section className="glass-panel p-8 bg-surface-container-lowest shadow-ambient border-outline-variant/20">
            <h2 className="text-xl font-heading mb-4 flex items-center gap-2 text-secondary"><Database size={20} /> Privacy Policy</h2>
            <div className="space-y-4 text-on-surface-variant leading-relaxed">
               <p><strong>Information Collection:</strong> The Sentinel framework captures strictly necessary telemetry limited to target domain topologies, user layout paths, and programmatic violations.</p>
               <p><strong>Third-Party Disclosures:</strong> Telemetry arrays remain absolutely confidential. No structural layout intelligence logic is dispatched to external vendor infrastructures. Artificial intelligence resolutions operate over local or strictly sandboxed secure enclaves exclusively.</p>
               <p><strong>User Consent & Purge Protocols:</strong> As an institutional administrator, you retain explicit operational override of the `LocalStorage` and `SessionStorage` caching hooks governing the token engine endpoints.</p>
            </div>
         </section>
      </div>
    </div>
  )
}
