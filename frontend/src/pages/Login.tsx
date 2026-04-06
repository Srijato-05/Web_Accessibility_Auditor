import { useNavigate } from 'react-router-dom';
import { Shield, Lock } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background text-on-surface flex items-center justify-center p-8 relative overflow-hidden">
      {/* Aesthetic Background Ornaments */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-20%] right-[-10%] w-[40%] h-[40%] bg-secondary/10 rounded-full blur-[100px] pointer-events-none"></div>

      <div className="glass-panel max-w-md w-full p-8 md:p-12 relative z-10 flex flex-col items-center text-center shadow-ambient">
        <div className="bg-surface-container p-4 rounded-full border border-outline-variant/30 text-primary mb-6 shadow-glow">
          <Shield size={48} />
        </div>
        
        <h1 className="text-4xl font-heading tracking-tight mb-3 text-on-surface">Smart Audit</h1>
        <p className="text-on-surface-variant font-body mb-8 text-sm leading-relaxed">
          Secure, AI-powered forensic web accessibility auditing. Please authenticate to access mission control.
        </p>

        <div className="w-full space-y-4">
           {/* Decorative Inputs */}
           <div className="bg-surface-container-highest/50 rounded-md p-3 px-4 border border-outline-variant/15 flex items-center gap-3 text-on-surface-variant opacity-50 select-none">
             <Lock size={16} />
             <span className="text-sm">Corporate ID token detected...</span>
           </div>

           <button 
             onClick={() => navigate('/dashboard')}
             className="w-full primary-btn flex justify-center items-center gap-2 py-3 text-lg mt-4 cursor-pointer">
             Start Demo
           </button>
        </div>
      </div>
    </div>
  );
}
