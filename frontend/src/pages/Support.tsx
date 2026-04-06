import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { client } from '../api/client';
import { LifeBuoy, ArrowLeft, Send, CheckCircle2, Loader2 } from 'lucide-react';

export default function Support() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ name: '', issue: '', message: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.issue || !formData.message) return alert("Fill out all required fields.");
    
    setIsSubmitting(true);
    try {
      await client.post('/support/ticket', formData);
      setSubmitted(true);
    } catch (err) {
      console.error(err);
    }
    setIsSubmitting(false);
  };

  return (
    <div className="min-h-screen bg-background text-on-surface p-8 max-w-4xl mx-auto pb-32">
       <header className="mb-8 border-b border-outline-variant/15 pb-8">
        <button onClick={() => navigate('/profile')} className="flex items-center gap-2 text-on-surface-variant hover:text-on-surface transition-colors mb-6 text-xs uppercase tracking-widest font-bold">
           <ArrowLeft size={16} /> Back to Profile
        </button>
        <div className="flex items-center gap-3">
            <div className="bg-tertiary/10 text-tertiary p-2 rounded-md border border-tertiary/40 shadow-ambient">
                <LifeBuoy size={24} />
            </div>
            <h1 className="text-display font-medium">Support Center</h1>
        </div>
        <p className="text-on-surface-variant text-lg mt-2 tracking-wide">Open a priority technical request vector with system operations.</p>
      </header>

      {submitted ? (
         <div className="glass-panel p-12 text-center bg-surface-container-low shadow-ambient border-secondary/30 flex flex-col items-center justify-center">
            <CheckCircle2 size={64} className="text-secondary mb-6 drop-shadow-[0_0_8px_rgba(50,250,150,0.5)]" />
            <h2 className="text-2xl font-heading mb-4 text-on-surface">Ticket Dispatched Successfully</h2>
            <p className="text-on-surface-variant max-w-lg mb-8">Your intelligence payload has been securely routed to the Sentinel diagnostics team. A resolution expert will be in touch shortly.</p>
            <button onClick={() => navigate('/profile')} className="secondary-btn border-secondary/50 text-secondary hover:bg-secondary hover:text-background transition-colors">
               Return to Profile
            </button>
         </div>
      ) : (
         <form onSubmit={handleSubmit} className="glass-panel p-8 bg-surface-container-low shadow-ambient">
            <h2 className="text-label text-on-surface-variant uppercase tracking-widest font-bold mb-6 flex items-center gap-2">Contact Operations</h2>

            <div className="space-y-6">
               <div>
                  <label className="text-xs uppercase tracking-widest font-bold text-on-surface-variant block mb-2">Identification</label>
                  <input type="text" placeholder="John Doe" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full bg-surface py-3 px-4 rounded-md border border-outline-variant/30 text-sm focus:outline-none focus:border-tertiary/50 text-on-surface transition-colors shadow-inner" />
               </div>
               
               <div>
                  <label className="text-xs uppercase tracking-widest font-bold text-on-surface-variant block mb-2">Issue Vector</label>
                  <select value={formData.issue} onChange={e => setFormData({...formData, issue: e.target.value})} className="w-full bg-surface py-3 px-4 rounded-md border border-outline-variant/30 text-sm focus:outline-none focus:border-tertiary/50 text-on-surface transition-colors shadow-inner appearance-none cursor-pointer">
                     <option value="" disabled>Select Core Disruption</option>
                     <option value="AST Remediation Failure">AST Patch Injection Failure</option>
                     <option value="Graph Traversal Errors">Graph Traversal Mismatches</option>
                     <option value="Billing Anomalies">Billing Token Anomalies</option>
                     <option value="Misc Diagnostics">Miscellaneous Heuristic Analysis</option>
                  </select>
               </div>
               
               <div>
                  <label className="text-xs uppercase tracking-widest font-bold text-on-surface-variant block mb-2">Payload Description</label>
                  <textarea placeholder="Describe the structural failure in logical semantics..." value={formData.message} onChange={e => setFormData({...formData, message: e.target.value})} className="w-full bg-surface py-3 px-4 rounded-md border border-outline-variant/30 text-sm focus:outline-none focus:border-tertiary/50 text-on-surface transition-colors min-h-32 shadow-inner"></textarea>
               </div>
            </div>

            <button type="submit" disabled={isSubmitting} className="w-full primary-btn mt-8 flex items-center justify-center gap-2 py-4 cursor-pointer disabled:opacity-50 transition-all border border-tertiary/30 bg-tertiary/10 text-tertiary hover:bg-tertiary hover:text-background">
               {isSubmitting ? <><Loader2 className="animate-spin" size={18}/> Routing Payload...</> : <><Send size={18}/> Dispatch Protocol</>}
            </button>
         </form>
      )}
    </div>
  )
}
