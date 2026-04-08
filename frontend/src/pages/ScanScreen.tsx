import { useState } from 'react';
import { client } from '../api/client';
import { Target, Loader2, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function ScanScreen() {
  const [url, setUrl] = useState('');
  const navigate = useNavigate();
  const [isScanning, setIsScanning] = useState(false);

  const startScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    setIsScanning(true);

    try {
      const res = await client.post('/audit', { url, scan_type: 'precision' });
      const audit_id = res.data.session_id;
      // In a real scenario we'd poll or use websockets. Here we navigate to insights.
      // Wait a moment for the background initial record to write
      setTimeout(() => {
        setIsScanning(false);
        navigate('/insights/' + audit_id, { replace: true });
      }, 1000);
    } catch (err) {
      console.error(err);
      setIsScanning(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-20 pb-32 flex flex-col items-center justify-center min-h-[calc(100vh-64px)]">
      <div className="text-center mb-10 w-full">
        <h1 className="text-4xl font-heading font-bold text-on-surface mb-3">Target Initialization</h1>
        <p className="text-on-surface-variant font-body">Execute forensic high-precision scan on secondary targets.</p>
      </div>

      <div className="w-full">
        <form onSubmit={startScan} className="relative flex shadow-flat rounded-md overflow-hidden bg-surface border border-surface-border transition-all focus-within:ring-2 focus-within:ring-primary focus-within:border-primary">
          <div className="pl-4 flex items-center justify-center text-on-surface-variant bg-surface">
            <Target size={20} />
          </div>
          <input 
            type="url" 
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isScanning}
            required
            className="flex-1 py-4 px-4 text-on-surface focus:outline-none bg-surface"
          />
          <button 
            type="submit"
            disabled={isScanning || !url}
            className="bg-primary hover:bg-primary-hover text-on-primary px-8 font-medium transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-w-[140px]"
          >
            {isScanning ? <Loader2 className="animate-spin" size={20} /> : <span className="flex items-center gap-2">Analyze <ArrowRight size={18} /></span>}
          </button>
        </form>
      </div>
      
      {isScanning && (
         <p className="mt-8 text-sm text-on-surface-variant animate-pulse">Initializing engine and beginning data capture...</p>
      )}
    </div>
  )
}
