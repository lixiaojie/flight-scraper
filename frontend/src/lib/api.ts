export function getApiBase(): string {
  // Prefer Vite env var at build time; fallback to window-injected or localhost
  const viteBase = (import.meta as any).env?.VITE_API_BASE as string | undefined;
  const winBase = (globalThis as any).__API_BASE__ as string | undefined;
  return viteBase || winBase || 'http://localhost:8000';
}

export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const base = getApiBase().replace(/\/$/, '');
  const url = `${base}${path.startsWith('/') ? path : `/${path}`}`;
  return fetch(url, init);
}


