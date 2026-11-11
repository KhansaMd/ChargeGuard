const API_BASE_URL = 'http://127.0.0.1:8001';

async function request(endpoint, options = {}) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  } catch {
    throw new Error(
      'Cannot connect to the backend. Check whether the FastAPI server is running.'
    );
  }

  const contentType = response.headers.get('content-type');
  let data = null;

  if (contentType?.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const message =
      typeof data === 'object' && data !== null
        ? data.detail || JSON.stringify(data)
        : data || response.statusText;

    throw new Error(`API Error ${response.status}: ${message}`);
  }

  return data;
}

export const api = {
  getHealth: () => request('/health'),
  getDisputes: () => request('/api/disputes'),
  syncDisputes: () => request('/api/disputes/sync', { method: 'POST' }),
  getDispute: (id) => request(`/api/disputes/${id}`),
  investigate: (id) => request(`/api/disputes/${id}/investigate`, { method: 'POST' }),
  generateDraft: (id) => request(`/api/disputes/${id}/draft`, { method: 'POST' }),
  approveReport: (id, data) => request(`/api/disputes/${id}/approve`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  submitEvidence: (id) => request(`/api/disputes/${id}/submit`, { method: 'POST' }),
  addEvidence: (id, data) => request(`/api/disputes/${id}/evidence`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  getTransactions: () => request('/api/transactions'),
  getAudit: (disputeId) => request(`/api/audit${disputeId ? `?dispute_id=${disputeId}` : ''}`),
};
