export const API = import.meta.env.VITE_API_URL || '/api';
const API_KEY = import.meta.env.VITE_API_KEY || localStorage.getItem('h3-api-key') || '';
const API_TOKEN = import.meta.env.VITE_API_TOKEN || localStorage.getItem('h3-api-token') || '';

export function apiHeaders(init?: HeadersInit) {
  const headers = new Headers(init);
  if (API_KEY) headers.set('X-API-Key', API_KEY);
  if (API_TOKEN) headers.set('Authorization', 'Bearer ' + API_TOKEN);
  return headers;
}

export function apiFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  return fetch(input, { ...init, headers: apiHeaders(init.headers) });
}

export function apiJson(input: RequestInfo | URL, init: RequestInit = {}) {
  const headers = apiHeaders(init.headers);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  return fetch(input, { ...init, headers });
}
