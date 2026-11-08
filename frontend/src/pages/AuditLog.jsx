
import { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import './AuditLog.css';

const demoLogs = [
  {
    id: 'LOG-001',
    dispute_id: 'DP-10241',
    action: 'Dispute received',
    detail: 'A new item-not-received dispute was recorded.',
    created_at: 'Nov 4, 2026, 10:30 AM',
  },
  {
    id: 'LOG-002',
    dispute_id: 'DP-10241',
    action: 'Evidence reviewed',
    detail: 'Order confirmation and payment record were identified.',
    created_at: 'Nov 4, 2026, 10:35 AM',
  },
  {
    id: 'LOG-003',
    dispute_id: 'DP-10240',
    action: 'Risk alert generated',
    detail: 'A transaction was flagged for further review.',
    created_at: 'Nov 3, 2026, 02:15 PM',
  },
  {
    id: 'LOG-004',
    dispute_id: 'DP-10239',
    action: 'Investigation started',
    detail: 'The dispute was opened for evidence analysis.',
    created_at: 'Nov 2, 2026, 11:20 AM',
  },
  {
    id: 'LOG-005',
    dispute_id: 'DP-10238',
    action: 'Dispute resolved',
    detail: 'The dispute was marked as closed.',
    created_at: 'Nov 1, 2026, 04:45 PM',
  },
];

function AuditLog() {
  const [logs, setLogs] = useState(demoLogs);
  const [demoMode, setDemoMode] = useState(true);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    let active = true;

    async function loadLogs() {
      try {
        const result = await api.getAudit();

        if (!active) return;

        setLogs(Array.isArray(result) ? result : []);
        setDemoMode(false);
      } catch {
        if (!active) return;

        setLogs(demoLogs);
        setDemoMode(true);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadLogs();

    return () => {
      active = false;
    };
  }, []);

  const filteredLogs = useMemo(() => {
    const term = search.toLowerCase().trim();

    if (!term) return logs;

    return logs.filter((log) =>
      [
        log.id,
        log.dispute_id,
        log.action,
        log.detail,
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(term))
    );
  }, [logs, search]);

  return (
    <main className="main-content audit-page">
      <header className="topbar">
        <div>
          <div className="breadcrumb">Workspace / Audit Log</div>
          <h1>Audit Log</h1>
          <p className="audit-description">
            Track activity and review the history of dispute-related actions.
          </p>
        </div>

        <span className="audit-status">
          {demoMode ? 'Demo data' : 'Backend connected'}
        </span>
      </header>

      <section className="audit-summary">
        <div>
          <span>Total recorded activities</span>
          <strong>{logs.length.toString().padStart(2, '0')}</strong>
        </div>
        <div>
          <span>Disputes referenced</span>
          <strong>
            {new Set(logs.map((log) => log.dispute_id).filter(Boolean)).size
              .toString()
              .padStart(2, '0')}
          </strong>
        </div>
      </section>

      <section className="audit-content">
        <div className="audit-heading">
          <div>
            <h2>Activity history</h2>
            <p>{filteredLogs.length} activities found</p>
          </div>

          <input
            className="audit-search"
            type="text"
            placeholder="Search activity or dispute ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {loading ? (
          <div className="audit-empty">Loading activity...</div>
        ) : filteredLogs.length === 0 ? (
          <div className="audit-empty">No matching activities found.</div>
        ) : (
          <div className="audit-table-wrapper">
            <table className="audit-table">
              <thead>
                <tr>
                  <th>ACTIVITY ID</th>
                  <th>DISPUTE ID</th>
                  <th>ACTION</th>
                  <th>DETAILS</th>
                  <th>DATE & TIME</th>
                </tr>
              </thead>

              <tbody>
                {filteredLogs.map((log, index) => (
                  <tr key={log.id || index}>
                    <td className="audit-id">{log.id || '—'}</td>
                    <td>{log.dispute_id || '—'}</td>
                    <td>
                      <span className="audit-action">
                        {log.action || 'Activity recorded'}
                      </span>
                    </td>
                    <td className="audit-detail">{log.detail || '—'}</td>
                    <td>{log.created_at || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {demoMode && (
          <p className="audit-demo-note">
            These are illustrative activities, not actual merchant actions.
            Live audit records will appear when the backend is connected.
          </p>
        )}
      </section>
    </main>
  );
}

export default AuditLog;
