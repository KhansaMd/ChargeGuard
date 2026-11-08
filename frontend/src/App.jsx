
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import './App.css';
import Disputes from './pages/Disputes';
import Investigation from './pages/Investigation';
import Transactions from './pages/Transactions';
import FraudAlerts from './pages/FraudAlerts';
import AuditLog from './pages/AuditLog';

function Placeholder({ title }) {
  return (
    <main className="main-content">
      <header className="topbar">
        <div>
          <div className="breadcrumb">Workspace / {title}</div>
          <h1>{title}</h1>
        </div>
      </header>
      <section className="content-card">
        <h3>{title}</h3>
        <p>This page is currently being developed.</p>
      </section>
    </main>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Sidebar />

        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/disputes" element={<Disputes />} />
          <Route path="/disputes/:id" element={<Investigation />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/fraud-alerts" element={<FraudAlerts />} />
          <Route path="/audit" element={<AuditLog />} />
          <Route path="/settings" element={<Placeholder title="Settings" />} />
          <Route path="*" element={<Placeholder title="Page Not Found" />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
