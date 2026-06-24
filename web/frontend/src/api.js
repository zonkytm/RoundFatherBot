const API_BASE = '/api';

async function request(url, options = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    credentials: 'same-origin',
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export const api = {
  auth: {
    verify: (token) => request('/auth/verify', {
      method: 'POST',
      body: JSON.stringify({ token }),
    }),
  },

  stats: {
    get: () => request('/stats'),
    hourly: () => request('/stats/hourly'),
  },

  revenue: {
    get: () => request('/revenue'),
    monthly: () => request('/revenue/monthly'),
    packages: () => request('/revenue/packages'),
    recent: () => request('/revenue/recent'),
  },

  mailings: {
    list: () => request('/mailings'),
    create: (data) => request('/mailings', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    update: (id, data) => request(`/mailings/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
    delete: (id) => request(`/mailings/${id}`, {
      method: 'DELETE',
    }),
    send: (id) => request(`/mailings/${id}/send`, {
      method: 'POST',
    }),
    logs: (id) => request(`/mailings/${id}/logs`),
  },

  presets: {
    list: () => request('/presets'),
    create: (data) => request('/presets', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    delete: (id) => request(`/presets/${id}`, {
      method: 'DELETE',
    }),
  },

  settings: {
    get: () => request('/settings'),
    update: (key, value) => request(`/settings/${encodeURIComponent(key)}`, {
      method: 'PUT',
      body: JSON.stringify({ value }),
    }),
    updatePackage: (id, data) => request(`/settings/package/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  },
};
