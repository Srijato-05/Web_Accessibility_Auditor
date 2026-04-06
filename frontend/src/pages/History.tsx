import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { client } from '../api/client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Search, Download, Eye, ShieldAlert, Activity, CheckCircle2, Loader2 } from 'lucide-react';

interface AuditHistory {
  id: string;
  date: string;
  url: string;
  issues: number;
  status: string;
}

export default function History() {
  const [history, setHistory] = useState<AuditHistory[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const itemsPerPage = 8;
  const navigate = useNavigate();

  useEffect(() => {
    client.get('/audits/history')
      .then(res => { setHistory(res.data); setLoading(false); })
      .catch(e => { console.error(e); setLoading(false); });
  }, []);

  const handleDownload = () => {
    const headers = "Report ID,Date,URL,Issues,Status\n";
    const csvContent = headers + history.map(h => `${h.id},${h.date},${h.url},${h.issues},${h.status}`).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "master_audit_report.csv");
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filteredHistory = history.filter(item => 
    (item.url || '').toLowerCase().includes(searchTerm.toLowerCase()) || 
    item.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalPages = Math.ceil(filteredHistory.length / itemsPerPage);
  const paginatedHistory = filteredHistory.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const chartData = [...history].reverse().map(h => ({
     name: new Date(h.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
     score: Math.max(0, 100 - (h.issues || 0))
  }));

  // Map backend status values to display
  const getStatusLabel = (status: string) => {
    if (status === 'completed') return 'Completed';
    if (status === 'in_progress') return 'In Progress';
    if (status === 'failed') return 'Failed';
    return status;
  }

  const getStatusColor = (status: string) => {
    if (status === 'completed') return 'text-secondary bg-secondary/10 border-secondary/20';
    if (status === 'in_progress') return 'text-warning bg-warning/10 border-warning/20';
    return 'text-error bg-error/10 border-error/20';
  }

  const getStatusIcon = (status: string) => {
    if (status === 'completed') return <CheckCircle2 size={14} className="mr-1" />;
    if (status === 'in_progress') return <Activity size={14} className="mr-1" />;
    return <ShieldAlert size={14} className="mr-1" />;
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 pb-32">
      <header className="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-surface-border pb-8">
        <div>
            <h1 className="text-3xl font-heading font-bold text-on-surface">Audit History</h1>
            <p className="text-on-surface-variant mt-2 text-sm">Aggregate list of previous site evaluations.</p>
        </div>
        <button onClick={handleDownload} className="secondary-btn flex items-center gap-2 text-sm">
           <Download size={16} /> Export CSV
        </button>
      </header>

      {history.length > 0 && (
        <div className="flat-panel p-6 mb-8 h-64">
           <h2 className="text-sm font-bold text-on-surface mb-4">Score Progression</h2>
           <div className="w-full h-44">
             <ResponsiveContainer width="100%" height="100%">
               <LineChart data={chartData}>
                 <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
                 <XAxis dataKey="name" stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
                 <YAxis stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} domain={[0, 100]} />
                 <Tooltip 
                    contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #E5E7EB', borderRadius: '6px' }}
                    itemStyle={{ color: '#2563EB', fontWeight: 'bold' }} 
                 />
                 <Line type="monotone" dataKey="score" stroke="#2563EB" strokeWidth={3} dot={{ r: 4, fill: '#2563EB' }} activeDot={{ r: 6, fill: '#fff', stroke: '#2563EB', strokeWidth: 2 }} />
               </LineChart>
             </ResponsiveContainer>
           </div>
        </div>
      )}

      <div className="flat-panel overflow-hidden mt-8">
         <div className="p-4 border-b border-surface-border flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-surface">
            <h2 className="font-bold text-on-surface">All Records</h2>
            <div className="relative w-full sm:w-72">
               <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search size={16} className="text-on-surface-variant" />
               </div>
               <input
                  type="text"
                  placeholder="Search by URL or ID..."
                  className="w-full bg-surface py-2 pl-10 pr-4 rounded-md border border-surface-border text-sm focus:outline-none focus:border-primary text-on-surface transition-colors shadow-flat"
                  value={searchTerm}
                  onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
               />
            </div>
         </div>

         <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
               <thead>
                  <tr className="bg-surface-highlight border-b border-surface-border text-xs uppercase text-on-surface-variant font-bold">
                     <th className="px-6 py-4 tracking-wider">Target</th>
                     <th className="px-6 py-4 tracking-wider">Date</th>
                     <th className="px-6 py-4 tracking-wider text-center">Issues</th>
                     <th className="px-6 py-4 tracking-wider">Status</th>
                     <th className="px-6 py-4 tracking-wider text-right">Action</th>
                  </tr>
               </thead>
               <tbody>
                   {paginatedHistory.map((item) => (
                      <tr key={item.id} className="border-b border-surface-border hover:bg-surface-highlight transition-colors group">
                         <td className="px-6 py-4 font-medium text-sm text-on-surface max-w-xs truncate">{item.url}</td>
                         <td className="px-6 py-4 text-sm text-on-surface-variant whitespace-nowrap">{new Date(item.date).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute:'2-digit' })}</td>
                         <td className="px-6 py-4 text-center">
                            <span className="font-mono font-bold text-on-surface">{item.issues}</span>
                            <span className="text-on-surface-variant text-xs ml-1">issues</span>
                         </td>
                         <td className="px-6 py-4">
                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold border ${getStatusColor(item.status)}`}>
                               {getStatusIcon(item.status)}
                               {getStatusLabel(item.status)}
                            </span>
                         </td>
                         <td className="px-6 py-4 text-right">
                            <button 
                               onClick={() => navigate('/insights/' + item.id)}
                               className="inline-flex items-center gap-1 text-xs font-bold text-primary hover:underline">
                               <Eye size={14} /> View
                            </button>
                         </td>
                      </tr>
                   ))}
                  {loading && (
                     <tr>
                        <td colSpan={5} className="px-6 py-12 text-center text-on-surface-variant">
                           <Loader2 className="animate-spin inline-block mr-2" size={24} /> Loading Data...
                        </td>
                     </tr>
                  )}
                  {!loading && history.length === 0 && (
                     <tr>
                        <td colSpan={5} className="px-6 py-12 text-center text-on-surface-variant">
                           No history available.
                        </td>
                     </tr>
                  )}
                  {!loading && history.length > 0 && paginatedHistory.length === 0 && (
                     <tr>
                        <td colSpan={5} className="px-6 py-12 text-center text-on-surface-variant">
                           No audit records matched your specific filter constraints.
                        </td>
                     </tr>
                  )}
               </tbody>
            </table>
         </div>

         {totalPages > 1 && (
            <div className="p-4 border-t border-surface-border flex items-center justify-between bg-surface">
               <button 
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 border border-surface-border rounded hover:bg-surface-highlight disabled:opacity-50 text-sm text-on-surface-variant font-medium">
                  Previous
               </button>
               <span className="text-sm text-on-surface-variant">
                  Page {currentPage} of {totalPages}
               </span>
               <button 
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 border border-surface-border rounded hover:bg-surface-highlight disabled:opacity-50 text-sm text-on-surface-variant font-medium">
                  Next
               </button>
            </div>
         )}
      </div>
    </div>
  )
}
