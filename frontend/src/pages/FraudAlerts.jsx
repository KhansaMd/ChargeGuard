
import { useMemo, useState } from 'react';
import './FraudAlerts.css';

const demoAlerts = [
  {
    id: 'RISK-001',
    transactionId: 'TXN-58371',
    customer: 'customer2@example.com',
    amount: 89.50,
    risk: 'High',
    reasons: [
      'Unrecognised payment dispute associated with this transaction',
      'Customer identity requires further verification',
    ],
    recommendation: 'Review the payment and verify customer details before processing further orders.',
    date: 'Nov 3, 2026',
  },
  {
    id: 'RISK-002',
    transactionId: 'TXN-58320',
    customer: 'customer3@example.com',
    amount: 210.00,
    risk: 'Medium',
    reasons: [
      'High-value transaction',
      'Additional order and delivery verification recommended',
    ],
    recommendation: 'Check the order and shipping records before taking action.',
    date: 'Nov 2, 2026',
  },
  {
    id: 'RISK-003',
    transactionId: 'TXN-58392',
    customer: 'customer1@example.com',
    amount: 149.00,
    risk: 'Low',
    reasons: [
      'No specific risk indicator has been recorded in this demo',
    ],
    recommendation: 'Continue normal monitoring and retain transaction evidence.',
    date: 'Nov 4, 2026',
  },
];

function FraudAlerts() {
  const [selectedRisk, setSelectedRisk] = useState('All');
  const [expandedAlert, setExpandedAlert] = useState(null);

  const filteredAlerts = useMemo(() => {
    if (selectedRisk === 'All') return demoAlerts;
    return demoAlerts.filter((alert) => alert.risk === selectedRisk);
  }, [selectedRisk]);

  const highCount = demoAlerts.filter((a) => a.risk === 'High').length;
  const mediumCount = demoAlerts.filter((a) => a.risk === 'Medium').length;
  const lowCount = demoAlerts.filter((a) => a.risk === 'Low').length;

  return (
    <main className="main-content fraud-page">
      <header className="topbar">
        <div>
          <div className="breadcrumb">Workspace / Fraud Alerts</div>
          <h1>Fraud Alerts</h1>
          <p className="page-description">
            Review transaction risk indicators and recommended actions.
          </p>
        </div>
        <span className="demo-status">Demo data</span>
      </header>

      <section className="risk-summary">
        <div className="risk-summary-card">
          <span className="risk-label">High risk</span>
          <strong>{highCount.toString().padStart(2, '0')}</strong>
          <small>Requires attention</small>
        </div>
        <div className="risk-summary-card">
          <span className="risk-label">Medium risk</span>
          <strong>{mediumCount.toString().padStart(2, '0')}</strong>
          <small>Review recommended</small>
        </div>
        <div className="risk-summary-card">
          <span className="risk-label">Low risk</span>
          <strong>{lowCount.toString().padStart(2, '0')}</strong>
          <small>Normal monitoring</small>
        </div>
      </section>

      <section className="fraud-content">
        <div className="fraud-section-header">
          <div>
            <h2>Risk assessments</h2>
            <p>{filteredAlerts.length} alerts found</p>
          </div>

          <select
            value={selectedRisk}
            onChange={(e) => setSelectedRisk(e.target.value)}
            className="risk-filter"
          >
            <option value="All">All risk levels</option>
            <option value="High">High risk</option>
            <option value="Medium">Medium risk</option>
            <option value="Low">Low risk</option>
          </select>
        </div>

        <div className="fraud-alert-list">
          {filteredAlerts.map((alert) => (
            <article className="fraud-alert-card" key={alert.id}>
              <div className="fraud-alert-top">
                <div>
                  <span className={`risk-badge risk-${alert.risk.toLowerCase()}`}>
                    {alert.risk} risk
                  </span>
                  <h3>{alert.transactionId}</h3>
                  <p>{alert.customer}</p>
                </div>
                <strong className="fraud-amount">
                  USD {alert.amount.toFixed(2)}
                </strong>
              </div>

              <div className="fraud-alert-meta">
                <span>Alert: {alert.id}</span>
                <span>{alert.date}</span>
              </div>

              <button
                className="details-button"
                onClick={() =>
                  setExpandedAlert(
                    expandedAlert === alert.id ? null : alert.id
                  )
                }
              >
                {expandedAlert === alert.id ? 'Hide details' : 'View risk details'}
                <span>{expandedAlert === alert.id ? '−' : '+'}</span>
              </button>

              {expandedAlert === alert.id && (
                <div className="risk-details">
                  <h4>Risk indicators</h4>
                  <ul>
                    {alert.reasons.map((reason, index) => (
                      <li key={index}>{reason}</li>
                    ))}
                  </ul>

                  <h4>Recommended action</h4>
                  <p>{alert.recommendation}</p>
                </div>
              )}
            </article>
          ))}
        </div>

        <p className="fraud-demo-note">
          These are illustrative demo assessments, not real fraud detections.
          Risk levels and indicators are sample data and do not represent
          verified fraud probabilities.
        </p>
      </section>
    </main>
  );
}

export default FraudAlerts;
