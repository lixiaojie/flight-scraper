export function getApiBase(): string {
  if (typeof window !== 'undefined') {
    return window.location.origin;
  }
  const viteBase = (import.meta as any).env?.VITE_API_BASE as string | undefined;
  const winBase = (globalThis as any).__API_BASE__ as string | undefined;
  return viteBase || winBase || 'http://localhost:8000';
}

export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const pathNorm = path.startsWith('/') ? path : `/${path}`;
  // 浏览器环境：始终用相对路径，与当前页面同源同端口，避免出现 http://localhost/api/... 无端口
  if (typeof window !== 'undefined') {
    return fetch(pathNorm, init);
  }
  const base = getApiBase().replace(/\/$/, '');
  return fetch(`${base}${pathNorm}`, init);
}


