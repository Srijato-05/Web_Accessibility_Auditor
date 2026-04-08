import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import AuditReport from './pages/AuditReport';
import ScanScreen from './pages/ScanScreen';
import Insights from './pages/Insights';
import IssueDetail from './pages/IssueDetail';
import GraphInsights from './pages/GraphInsights';
import Profile from './pages/Profile';
import Privacy from './pages/Privacy';
import Support from './pages/Support';
import Navbar from './components/Navbar';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<ScanScreen />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/scan" element={<ScanScreen />} />
            <Route path="/insights" element={<Insights />} />
            <Route path="/insights/:audit_id" element={<Insights />} />
            <Route path="/insights/:audit_id/issue/:violation_id" element={<IssueDetail />} />
            <Route path="/graph-insights/:audit_id" element={<GraphInsights />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/support" element={<Support />} />
            <Route path="/report/:id" element={<AuditReport />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
