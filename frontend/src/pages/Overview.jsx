import '../App.css'

function App() {
  return (
    <div className="app-container">


      {/* MAIN CONTENT */}
      <main className="main-content">

        {/* TOPBAR */}
        <header className="topbar">
          <div>
            <div className="breadcrumb">Workspace / Overview</div>
            <h1>Overview</h1>
          </div>

          <div className="topbar-actions">
            <span className="connection-status">
              <span className="status-dot"></span>
              Sandbox Demo
            </span>

            <button className="notification-button" type="button">
              ♧
            </button>
          </div>
        </header>

        {/* WELCOME */}
        <section className="welcome-section">
          <div>
            <h2>Good afternoon, John 👋</h2>
            <p>Here's what's happening with your business today.</p>
          </div>

          <a href="#" className="primary-button">
            + View Disputes
          </a>
        </section>

        {/* STATISTICS */}
        <section className="stats-grid">

          <div className="stat-card">
            <div className="stat-top">
              <span className="stat-label">Open Disputes</span>
              <span className="stat-icon blue">▤</span>
            </div>
            <h2>08</h2>
            <p className="stat-description">Cases requiring attention</p>
          </div>

          <div className="stat-card">
            <div className="stat-top">
              <span className="stat-label">Urgent Cases</span>
              <span className="stat-icon red">⚠</span>
            </div>
            <h2>03</h2>
            <p className="stat-description">Deadlines approaching</p>
          </div>

          <div className="stat-card">
            <div className="stat-top">
              <span className="stat-label">Resolved Disputes</span>
              <span className="stat-icon green">✓</span>
            </div>
            <h2>24</h2>
            <p className="stat-description">Successfully closed cases</p>
          </div>

          <div className="stat-card">
            <div className="stat-top">
              <span className="stat-label">Fraud Alerts</span>
              <span className="stat-icon orange">⌁</span>
            </div>
            <h2>03</h2>
            <p className="stat-description">Transactions flagged for review</p>
          </div>

        </section>

        {/* RECENT DISPUTES */}
        <section className="content-card disputes-section">

          <div className="section-header">
            <div>
              <h3>Recent Disputes</h3>
              <p>Monitor and manage your latest PayPal disputes.</p>
            </div>

            <a href="#" className="text-link">
              View all disputes →
            </a>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>DISPUTE ID</th>
                  <th>TRANSACTION</th>
                  <th>AMOUNT</th>
                  <th>REASON</th>
                  <th>STATUS</th>
                  <th>DEADLINE</th>
                </tr>
              </thead>

              <tbody>
                <tr>
                  <td>#DP-10241</td>
                  <td>TXN-58392</td>
                  <td>$149.00</td>
                  <td>Item not received</td>
                  <td><span className="badge pending">Under review</span></td>
                  <td className="deadline urgent">2 days left</td>
                </tr>

                <tr>
                  <td>#DP-10240</td>
                  <td>TXN-58371</td>
                  <td>$89.50</td>
                  <td>Unrecognised payment</td>
                  <td><span className="badge action">Action needed</span></td>
                  <td className="deadline urgent">1 day left</td>
                </tr>

                <tr>
                  <td>#DP-10239</td>
                  <td>TXN-58320</td>
                  <td>$210.00</td>
                  <td>Item not as described</td>
                  <td><span className="badge pending">Under review</span></td>
                  <td className="deadline">5 days left</td>
                </tr>

                <tr>
                  <td>#DP-10238</td>
                  <td>TXN-58294</td>
                  <td>$65.00</td>
                  <td>Duplicate charge</td>
                  <td><span className="badge resolved">Resolved</span></td>
                  <td className="deadline">—</td>
                </tr>
              </tbody>
            </table>
          </div>

        </section>

        {/* BOTTOM GRID */}
        <section className="bottom-grid">

          {/* RECENT ACTIVITY */}
          <div className="content-card activity-card">

            <div className="section-header">
              <div>
                <h3>Recent Activity</h3>
                <p>Latest updates from your workspace.</p>
              </div>
              <a href="#" className="text-link">View all</a>
            </div>

            <div className="activity-item">
              <div className="activity-icon green">✓</div>
              <div className="activity-details">
                <strong>Evidence submitted</strong>
                <p>Dispute #DP-10235</p>
                <small>Today, 2:45 PM</small>
              </div>
            </div>

            <div className="activity-item">
              <div className="activity-icon blue">✦</div>
              <div className="activity-details">
                <strong>AI investigation completed</strong>
                <p>Dispute #DP-10241</p>
                <small>Today, 1:20 PM</small>
              </div>
            </div>

            <div className="activity-item">
              <div className="activity-icon orange">⚠</div>
              <div className="activity-details">
                <strong>New fraud alert detected</strong>
                <p>Transaction TXN-58399</p>
                <small>Today, 11:10 AM</small>
              </div>
            </div>

          </div>

          {/* FRAUD ALERTS */}
          <div className="content-card fraud-card">

            <div className="section-header">
              <div>
                <h3>Fraud Alerts</h3>
                <p>Transactions flagged for review.</p>
              </div>
              <a href="#" className="text-link">View all</a>
            </div>

            <div className="fraud-item">
              <div>
                <strong>TXN-58399</strong>
                <p>Unusually high first purchase</p>
              </div>
              <span className="risk high">High Risk</span>
            </div>

            <div className="fraud-item">
              <div>
                <strong>TXN-58387</strong>
                <p>Multiple rapid transactions</p>
              </div>
              <span className="risk medium">Medium</span>
            </div>

            <div className="fraud-item">
              <div>
                <strong>TXN-58365</strong>
                <p>Address mismatch</p>
              </div>
              <span className="risk medium">Medium</span>
            </div>

          </div>

        </section>

        {/* FOOTER */}
        <footer>
          <span>© 2026 ChargeGuard</span>
          <span>AI-powered dispute intelligence</span>
        </footer>

      </main>
    </div>
  )
}

export default App
