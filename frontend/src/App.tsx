import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard.tsx';
import AuditReport from './pages/AuditReport.tsx';
import ScanScreen from './pages/ScanScreen.tsx';
import Insights from './pages/Insights.tsx';
import IssueDetail from './pages/IssueDetail.tsx';
import GraphInsights from './pages/GraphInsights.tsx';
import Profile from './pages/Profile.tsx';
import Privacy from './pages/Privacy.tsx';
import Support from './pages/Support.tsx';
import Sidebar from './components/Sidebar.tsx';
import Audits from './pages/Audits.tsx';
import Help from './pages/Help.tsx';

import { ThemeProvider } from './components/ThemeContext.tsx';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="flex min-h-screen bg-background text-on-surface transition-colors duration-200">
          <a href="#main-content" className="skip-to-content-link">
            Skip to main content
          </a>
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0">
            <main id="main-content" className="flex-grow focus:outline-none" tabIndex={-1}>
              <Routes>
                <Route path="/" element={<ScanScreen />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/audits" element={<Audits />} />
                <Route path="/insights/:audit_id" element={<Insights />} />
                <Route path="/insights/:audit_id/violations/:violation_id" element={<IssueDetail />} />
                <Route path="/audits/:audit_id/graph-insights" element={<GraphInsights />} />
                <Route path="/reports/:audit_id" element={<AuditReport />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/privacy" element={<Privacy />} />
                <Route path="/support" element={<Support />} />
                <Route path="/help" element={<Help />} />
              </Routes>
            </main>
          </div>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
