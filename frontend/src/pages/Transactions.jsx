
import { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import './Transactions.css';

const sampleTransactions = [
  {
    id: 'TXN-58392',
    order_id: 'ORD-58392',
    amount: 149,
    currency: 'USD',
    payer_email: 'customer1@example.com',
    shipping_address: 'Riyadh, Saudi Arabia',
    created_at: '2026-11-04',
    is_synthetic: true,
  },
  {
    id: 'TXN-58371',
    order_id: 'ORD-58371',
    amount: 89.5,
    currency: 'USD',
    payer_email: 'customer2@example.com',
    shipping_address: 'Jeddah, Saudi Arabia',
    created_at: '2026-11-03',
    is_synthetic: true,
  },
  {
    id: 'TXN-58320',
    order_id: 'ORD-58320',
    amount: 210,
    currency: 'USD',
    payer_email: 'customer3@example.com',
    shipping_address: 'Dammam, Saudi Arabia',
    created_at: '2026-11-02',
    is_synthetic: true,
  },
  {
    id: 'TXN-58294',
    order_id: 'ORD-58294',
    amount: 65,
    currency: 'USD',
    payer_email: 'customer4@example.com',
    shipping_address: 'Riyadh, Saudi Arabia',
    created_at: '2026-11-01',
    is_synthetic: true,
  },
];

function formatDate(value) {
  if (!value) return '—';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleDateString('en-US', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function Transactions() {
  const [transactions, setTransactions] = useState(sampleTransactions);
  const [search, setSearch] = useState('');
  const [backendStatus, setBackendStatus] = useState('Demo data');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadTransactions() {
      try {
        const result = await api.getTransactions();

        if (!active) return;

        setTransactions(Array.isArray(result) ? result : result.transactions || []);
        setBackendStatus('Backend connected');
      } catch {
        if (!active) return;

        setTransactions(sampleTransactions);
        setBackendStatus('Demo data');
      } finally {
        if (active) setLoading(false);
      }
    }

    loadTransactions();

    return () => {
      active = false;
    };
  }, []);

  const filteredTransactions = useMemo(() => {
    const term = search.toLowerCase();

    return transactions.filter((transaction) =>
      [
        transaction.id,
        transaction.order_id,
        transaction.payer_email,
        transaction.shipping_address,
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(term))
    );
  }, [transactions, search]);

  const totalValue = transactions.reduce(
    (total, transaction) => total + Number(transaction.amount || 0),
    0
  );

  const syntheticCount = transactions.filter(
    (transaction) => transaction.is_synthetic
  ).length;

  return (
    <main className="main-content transactions-page">
      <header className="topbar">
        <div>
          <div className="breadcrumb">Workspace / Transactions</div>
          <h1>Transactions</h1>
          <p className="transactions-description">
            Review payment records associated with your merchant account.
          </p>
        </div>

        <span className="transaction-data-mode">
          {backendStatus}
        </span>
      </header>

      <section className="transaction-summary">
        <div className="transaction-summary-card">
          <span>Total transactions</span>
          <strong>{transactions.length.toString().padStart(2, '0')}</strong>
        </div>

        <div className="transaction-summary-card">
          <span>Total transaction value</span>
          <strong>${totalValue.toFixed(2)}</strong>
        </div>

        <div className="transaction-summary-card">
          <span>Demo records</span>
          <strong>{syntheticCount.toString().padStart(2, '0')}</strong>
        </div>
      </section>

      <section className="content-card transactions-table-card">
        <div className="transactions-toolbar">
          <div>
            <h2>Payment records</h2>
            <p>{filteredTransactions.length} transactions found</p>
          </div>

          <input
            type="search"
            placeholder="Search transactions..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        {loading ? (
          <p className="transactions-empty">Loading transactions...</p>
        ) : filteredTransactions.length === 0 ? (
          <p className="transactions-empty">No matching transactions found.</p>
        ) : (
          <div className="transactions-table-wrapper">
            <table className="transactions-table">
              <thead>
                <tr>
                  <th>TRANSACTION ID</th>
                  <th>ORDER ID</th>
                  <th>AMOUNT</th>
                  <th>PAYER EMAIL</th>
                  <th>SHIPPING ADDRESS</th>
                  <th>DATE</th>
                  <th>DATA TYPE</th>
                </tr>
              </thead>

              <tbody>
                {filteredTransactions.map((transaction) => (
                  <tr key={transaction.id}>
                    <td className="transaction-id">{transaction.id}</td>
                    <td>{transaction.order_id || '—'}</td>
                    <td className="transaction-amount">
                      {transaction.currency || 'USD'}{' '}
                      {Number(transaction.amount || 0).toFixed(2)}
                    </td>
                    <td>{transaction.payer_email || '—'}</td>
                    <td>{transaction.shipping_address || '—'}</td>
                    <td>{formatDate(transaction.created_at)}</td>
                    <td>
                      <span className={`transaction-type ${
                        transaction.is_synthetic ? 'synthetic' : 'verified'
                      }`}>
                        {transaction.is_synthetic ? 'Demo' : 'API record'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <p className="transactions-footnote">
          Demo records are illustrative and are not real PayPal customer transactions.
        </p>
      </section>
    </main>
  );
}

export default Transactions;
