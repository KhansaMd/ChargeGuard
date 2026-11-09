
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { AgGridReact } from 'ag-grid-react';

import {
  AllCommunityModule,
  ModuleRegistry,
  themeQuartz,
} from 'ag-grid-community';

import { api } from '../services/api';
import './Disputes.css';

ModuleRegistry.registerModules([AllCommunityModule]);

const sampleDisputes = [
  {
    id: 'DP-10241',
    transaction_id: 'TXN-58392',
    reason: 'Item not received',
    status: 'Under review',
    stage: 'Evidence review',
    amount: 149,
    currency: 'USD',
    due_date: '2026-11-12',
    created_at: '2026-11-05',
  },
  {
    id: 'DP-10240',
    transaction_id: 'TXN-58371',
    reason: 'Unrecognised payment',
    status: 'Action needed',
    stage: 'Needs investigation',
    amount: 89.5,
    currency: 'USD',
    due_date: '2026-11-10',
    created_at: '2026-11-04',
  },
  {
    id: 'DP-10239',
    transaction_id: 'TXN-58320',
    reason: 'Item not as described',
    status: 'Under review',
    stage: 'Evidence review',
    amount: 210,
    currency: 'USD',
    due_date: '2026-11-14',
    created_at: '2026-11-03',
  },
  {
    id: 'DP-10238',
    transaction_id: 'TXN-58294',
    reason: 'Duplicate charge',
    status: 'Resolved',
    stage: 'Closed',
    amount: 65,
    currency: 'USD',
    due_date: null,
    created_at: '2026-11-01',
  },
];

function Disputes() {
  const [disputes, setDisputes] = useState(sampleDisputes);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('All');
  const [backendStatus, setBackendStatus] = useState('Loading');

  const loadDisputes = async () => {
    setLoading(true);

    try {
      const data = await api.getDisputes();

      if (!Array.isArray(data)) {
        throw new Error('Unexpected disputes response');
      }

      setDisputes(data);
      setBackendStatus('Connected');
    } catch (error) {
      console.error('Could not load disputes:', error);
      setBackendStatus('Demo data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDisputes();
  }, []);

  const handleSync = async () => {
    setSyncing(true);

    try {
      await api.syncDisputes();
      await loadDisputes();
    } catch (error) {
      console.error('Sync failed:', error);
      alert('Could not sync disputes. Please check the backend connection.');
    } finally {
      setSyncing(false);
    }
  };

  const filteredDisputes = useMemo(() => {
    return disputes.filter((dispute) => {
      const searchText = search.toLowerCase();

      const matchesSearch = [
        dispute.id,
        dispute.transaction_id,
        dispute.reason,
        dispute.status,
      ].some((value) =>
        String(value || '').toLowerCase().includes(searchText)
      );

      const matchesFilter =
        filter === 'All' || dispute.status === filter;

      return matchesSearch && matchesFilter;
    });
  }, [disputes, search, filter]);

  const columnDefs = useMemo(() => [
    {
      field: 'id',
      headerName: 'DISPUTE ID',
      minWidth: 145,
      flex: 1,
      cellRenderer: (params) => (
        <Link
          className="dispute-id-link"
          to={`/disputes/${encodeURIComponent(params.value)}`}
        >
          {params.value}
        </Link>
      ),
    },
    {
      field: 'transaction_id',
      headerName: 'TRANSACTION',
      minWidth: 145,
      flex: 1,
    },
    {
      field: 'reason',
      headerName: 'REASON',
      minWidth: 190,
      flex: 1.5,
    },
    {
      field: 'amount',
      headerName: 'AMOUNT',
      minWidth: 115,
      valueFormatter: (params) => {
        if (params.value == null) return '—';

        const currency = params.data?.currency || 'USD';

        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency,
        }).format(params.value);
      },
    },
    {
      field: 'status',
      headerName: 'STATUS',
      minWidth: 145,
      flex: 1,
    },
    {
      field: 'stage',
      headerName: 'STAGE',
      minWidth: 155,
      flex: 1,
    },
    {
      field: 'due_date',
      headerName: 'DEADLINE',
      minWidth: 130,
      valueFormatter: (params) => {
        if (!params.value) return '—';

        return new Date(`${params.value}T00:00:00`).toLocaleDateString(
          'en-GB',
          { day: '2-digit', month: 'short', year: 'numeric' }
        );
      },
    },
  ], []);

  return (
    <main className="main-content disputes-page">
      <header className="topbar">
        <div>
          <div className="breadcrumb">Workspace / Disputes</div>
          <h1>Dispute Management</h1>
        </div>

        <button
          className="primary-button"
          onClick={handleSync}
          disabled={syncing}
        >
          {syncing ? 'Syncing...' : '↻ Sync Disputes'}
        </button>
      </header>

      <section className="disputes-intro">
        <div>
          <h2>Manage your disputes</h2>
          <p>Review cases, track deadlines and investigate disputes.</p>
        </div>

        <span className={`backend-indicator ${
          backendStatus === 'Connected' ? 'connected' : ''
        }`}>
          <span className="status-dot"></span>
          {backendStatus}
        </span>
      </section>

      <section className="dispute-summary">
        <div className="dispute-summary-card">
          <span>Total disputes</span>
          <strong>{disputes.length}</strong>
        </div>

        <div className="dispute-summary-card">
          <span>Action needed</span>
          <strong>
            {disputes.filter((d) => d.status === 'Action needed').length}
          </strong>
        </div>

        <div className="dispute-summary-card">
          <span>Under review</span>
          <strong>
            {disputes.filter((d) => d.status === 'Under review').length}
          </strong>
        </div>

        <div className="dispute-summary-card">
          <span>Resolved</span>
          <strong>
            {disputes.filter((d) => d.status === 'Resolved').length}
          </strong>
        </div>
      </section>

      <section className="content-card disputes-table-card">
        <div className="disputes-toolbar">
          <div>
            <h3>All Disputes</h3>
            <p>Review and manage your PayPal dispute cases.</p>
          </div>

          <div className="disputes-controls">
            <input
              type="text"
              placeholder="Search disputes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />

            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="All">All statuses</option>
              <option value="Action needed">Action needed</option>
              <option value="Under review">Under review</option>
              <option value="Resolved">Resolved</option>
            </select>
          </div>
        </div>

        <div className="disputes-grid">
          <AgGridReact
            theme={themeQuartz}
            rowData={filteredDisputes}
            columnDefs={columnDefs}
            defaultColDef={{
              sortable: true,
              resizable: true,
            }}
            loading={loading}
            pagination={true}
            paginationPageSize={10}
            animateRows={true}
          />
        </div>

        <p className="table-note">
          {backendStatus === 'Connected'
            ? 'Showing disputes retrieved from the backend.'
            : 'Showing illustrative sample data until the backend is available.'}
        </p>
      </section>
    </main>
  );
}

export default Disputes;
