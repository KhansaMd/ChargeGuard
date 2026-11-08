
const API_BASE_URL = 'http://127.0.0.1:8000';

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

export const api = {
  getHealth: () => request('/health'),

  getDisputes: () => request('/api/disputes'),

  syncDisputes: () =>
    request('/api/disputes/sync', { method: 'POST' }),

  getDispute: (id) =>
    request(`/api/disputes/${id}`),

  investigate: (id) =>
    request(`/api/disputes/${id}/investigate`, { method: 'POST' }),

  generateDraft: (id) =>
    request(`/api/disputes/${id}/draft`, { method: 'POST' }),

  approveReport: (id, data) =>
    request(`/api/disputes/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  submitEvidence: (id) =>
    request(`/api/disputes/${id}/submit`, { method: 'POST' }),

  addEvidence: (id, data) =>
    request(`/api/disputes/${id}/evidence`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getTransactions: () => request('/api/transactions'),

  getAudit: (disputeId) =>
    request(`/api/audit${disputeId ? `?dispute_id=${disputeId}` : ''}`),
};
