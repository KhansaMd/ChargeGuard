
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../services/api';
import './Investigation.css';

function formatDate(value) {
  if (!value) return 'Not provided';

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleDateString('en-US', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function Investigation() {
  const { id } = useParams();

  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [draft, setDraft] = useState('');
  const [selectedFinding, setSelectedFinding] = useState(null);

  const dispute = detail?.dispute;
  const evidenceCheck = detail?.evidence_check || {};
  const report = detail?.report;
  const reportData = report?.data || {};

  const findings = reportData.findings || [];
  const evidence = evidenceCheck.evidence || [];
  const checklist = evidenceCheck.checklist || [];

  const contradictions = [
    ...(evidenceCheck.contradictions || []),
    ...(reportData.contradictions || []),
  ];

  // Load dispute details
  useEffect(() => {
    let active = true;

    async function loadDispute() {
      setLoading(true);
      setError('');
      setNotice('');

      try {
        const result = await api.getDispute(id);

        if (!active) return;

        setDetail(result);
        setDraft(result?.report?.data?.response_draft || '');
      } catch (err) {
        if (!active) return;

        setDetail(null);
        setError(
          err.message ||
          'Unable to load dispute. Check your backend connection.'
        );
      } finally {
        if (active) setLoading(false);
      }
    }

    loadDispute();

    return () => {
      active = false;
    };
  }, [id]);

  // Run AI investigation
  async function runInvestigation() {
    setActionLoading(true);
    setError('');
    setNotice('');

    try {
      // Run the AI investigation.
      await api.investigate(id);

      // Fetch the saved report from the backend.
      // The investigation endpoint may return an empty object,
      // so we retrieve the updated dispute separately.
      const refreshed = await api.getDispute(id);

      setDetail(refreshed);
      setDraft(
        refreshed?.report?.data?.response_draft || ''
      );
      setSelectedFinding(null);

      setNotice('Investigation completed successfully.');
    } catch (err) {
      setError(err.message || 'Investigation failed.');
    } finally {
      setActionLoading(false);
    }
  }

  // Generate response draft
  async function generateDraft() {
    if (!report?.id) return;

    setActionLoading(true);
    setError('');
    setNotice('');

    try {
      const result = await api.generateDraft(id);

      setDraft(result.response_draft || '');

      setDetail((previous) => ({
        ...previous,
        report: {
          ...previous.report,
          id: result.report_id || previous.report.id,
          data: {
            ...previous.report?.data,
            response_draft: result.response_draft || '',
          },
        },
      }));

      setNotice('Response draft generated.');
    } catch (err) {
      setError(
        err.message || 'Could not generate the response draft.'
      );
    } finally {
      setActionLoading(false);
    }
  }

  // Approve merchant response
  async function approveReport() {
    if (!report?.id || !draft.trim()) return;

    setActionLoading(true);
    setError('');
    setNotice('');

    try {
      const result = await api.approveReport(id, {
        report_id: report.id,
        approved_by: 'Merchant',
        edited_draft: draft,
      });

      setDetail((previous) => ({
        ...previous,
        report: result,
      }));

      setNotice(
        result?.approved
          ? 'Report approved successfully.'
          : 'Approval request sent. Check the backend response.'
      );
    } catch (err) {
      setError(err.message || 'Could not approve the report.');
    } finally {
      setActionLoading(false);
    }
  }

  // Loading state
  if (loading) {
    return (
      <main className="main-content">
        <p className="investigation-message">
          Loading dispute...
        </p>
      </main>
    );
  }

  // Error state
  if (error && !detail) {
    return (
      <main className="main-content">
        <Link to="/disputes" className="back-link">
          ← Back to disputes
        </Link>

        <p className="investigation-error">{error}</p>
      </main>
    );
  }

  if (!dispute) return null;

  return (
    <main className="main-content investigation-page">

      {/* Page heading */}
      <div className="investigation-topbar">
        <div>
          <Link to="/disputes" className="back-link">
            ← Back to disputes
          </Link>

          <div className="breadcrumb">
            Workspace / Disputes / {id}
          </div>

          <h1>Dispute Investigation</h1>

          <p className="page-description">
            Review transaction evidence and investigate the dispute.
          </p>
        </div>

        <span className="data-mode live">
          Backend connected
        </span>
      </div>

      {error && (
        <div className="investigation-alert error">
          {error}
        </div>
      )}

      {notice && (
        <div className="investigation-alert notice">
          {notice}
        </div>
      )}

      {/* Dispute overview */}
      <section className="investigation-card">
        <div className="section-heading">
          <div>
            <span className="eyebrow">DISPUTE OVERVIEW</span>
            <h2>{dispute.id}</h2>
          </div>

          <span className="status-pill">
            {dispute.status || 'Unknown status'}
          </span>
        </div>

        <div className="overview-grid">
          <div>
            <span>Dispute reason</span>
            <strong>
              {dispute.reason || 'Not provided'}
            </strong>
          </div>

          <div>
            <span>Disputed amount</span>
            <strong>
              {dispute.amount ?? '—'} {dispute.currency || ''}
            </strong>
          </div>

          <div>
            <span>Transaction ID</span>
            <strong>
              {dispute.transaction_id || 'Not provided'}
            </strong>
          </div>

          <div>
            <span>Current stage</span>
            <strong>
              {dispute.stage || 'Not provided'}
            </strong>
          </div>

          <div>
            <span>Date created</span>
            <strong>
              {formatDate(dispute.created_at)}
            </strong>
          </div>

          <div>
            <span>Response deadline</span>
            <strong className="deadline">
              {formatDate(dispute.due_date)}
            </strong>
          </div>
        </div>
      </section>

      {/* AI investigation */}
      <section className="investigation-card">
        <div className="section-heading">
          <div>
            <span className="eyebrow">AI ANALYSIS</span>
            <h2>Investigation findings</h2>
          </div>

          <button
            className="primary-button"
            onClick={runInvestigation}
            disabled={actionLoading}
          >
            {actionLoading ? 'Working...' : 'Run investigation'}
          </button>
        </div>

        {findings.length > 0 ? (
          <div className="findings-list">
            {findings.map((finding, index) => (
              <button
                key={index}
                className={`finding-item ${
                  selectedFinding === index ? 'selected' : ''
                }`}
                onClick={() => setSelectedFinding(index)}
              >
                <span className="finding-number">
                  {index + 1}
                </span>

                <span className="finding-content">
                  <strong>{finding.statement}</strong>

                  <small>
                    {finding.verified
                      ? 'Verified finding'
                      : 'Requires verification'}

                    {finding.source_ids?.length
                      ? ` · Sources: ${finding.source_ids.join(', ')}`
                      : ''}
                  </small>
                </span>
              </button>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <span className="empty-icon">✦</span>

            <strong>No investigation findings yet</strong>

            <p>
              Run an investigation to generate AI findings.
            </p>
          </div>
        )}

        {reportData.case_summary && (
          <div className="case-summary">
            <h3>Case summary</h3>
            <p>{reportData.case_summary}</p>
          </div>
        )}

        {reportData.recommended_action && (
          <div className="recommendation">
            <span>RECOMMENDED ACTION</span>
            <p>{reportData.recommended_action}</p>
          </div>
        )}
      </section>

      {/* Evidence checklist */}
      <section className="investigation-card">
        <div className="section-heading">
          <div>
            <span className="eyebrow">EVIDENCE REVIEW</span>
            <h2>Evidence checklist</h2>
          </div>

          <span className="evidence-count">
            {checklist.filter(
              (item) => item.status === 'available'
            ).length}
            {' / '}
            {checklist.length} available
          </span>
        </div>

        {checklist.length > 0 ? (
          <div className="checklist">
            {checklist.map((item, index) => (
              <div className="checklist-item" key={index}>
                <div>
                  <strong>{item.type}</strong>

                  {item.evidence_id && (
                    <small>
                      Evidence ID: {item.evidence_id}
                    </small>
                  )}
                </div>

                <span
                  className={`evidence-status ${item.status}`}
                >
                  {item.status}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="muted-text">
            No evidence checklist available.
          </p>
        )}

        {contradictions.length > 0 && (
          <div className="contradictions">
            <h3>Potential contradictions</h3>

            {contradictions.map((item, index) => (
              <div key={index}>
                <strong>
                  {item.issue || item.statement}
                </strong>

                {item.evidence_ids?.length > 0 && (
                  <small>
                    Related evidence: {item.evidence_ids.join(', ')}
                  </small>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Source records */}
      <section className="investigation-card">
        <div className="section-heading">
          <div>
            <span className="eyebrow">SOURCE RECORDS</span>
            <h2>Available evidence</h2>
          </div>
        </div>

        {evidence.length > 0 ? (
          <div className="evidence-list">
            {evidence.map((item) => {
              const highlighted =
                selectedFinding !== null &&
                findings[selectedFinding]?.source_ids?.includes(item.id);

              const checklistItem = checklist.find(
                (entry) => entry.evidence_id === item.id
              );

              const evidenceStatus =
                checklistItem?.status || 'unclassified';

              return (
                <div
                  key={item.id}
                  className={`evidence-item ${
                    highlighted ? 'highlighted' : ''
                  }`}
                >
                  <div className="evidence-item-heading">
                    <strong>{item.type}</strong>

                    <span
                      className={`evidence-status ${evidenceStatus}`}
                    >
                      {evidenceStatus}
                    </span>
                  </div>

                  <small>Evidence ID: {item.id}</small>

                  <p>{item.value || 'No value provided'}</p>

                  <small>
                    Source: {item.source || 'Not specified'}
                  </small>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="muted-text">
            No evidence records available.
          </p>
        )}

        {reportData.missing_information?.length > 0 && (
          <div className="missing-info">
            <h3>Missing information</h3>

            {reportData.missing_information.map((item, index) => (
              <p key={index}>
                • {typeof item === 'string'
                  ? item
                  : item.description || item.type}
              </p>
            ))}
          </div>
        )}
      </section>

      {/* Merchant response */}
      <section className="investigation-card">
        <div className="section-heading">
          <div>
            <span className="eyebrow">MERCHANT RESPONSE</span>
            <h2>Response draft</h2>
          </div>

          <button
            className="secondary-button"
            onClick={generateDraft}
            disabled={actionLoading || !report?.id}
          >
            Generate draft
          </button>
        </div>

        <textarea
          className="response-editor"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="The AI-generated response will appear here after investigation..."
          rows={8}
        />

        <p className="editor-note">
          Review and edit the response before approving it. Do not submit
          unverified claims.
        </p>

        <div className="approval-actions">
          <span
            className={`approval-status ${
              report?.approved ? 'approved' : ''
            }`}
          >
            {report?.approved
              ? 'Approved'
              : 'Awaiting merchant approval'}
          </span>

          <button
            className="primary-button"
            onClick={approveReport}
            disabled={
              actionLoading ||
              !report?.id ||
              !draft.trim() ||
              report?.approved
            }
          >
            Approve response
          </button>

          <button
            className="submit-button"
            disabled={true}
            title="PayPal submission is disabled during development"
          >
            Submission disabled during testing
          </button>
        </div>
      </section>

    </main>
  );
}

export default Investigation;