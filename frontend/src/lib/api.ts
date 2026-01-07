export function getApiBase(): string {
  // 在浏览器环境中，使用相对路径通过nginx代理访问API
  // 如果在容器网络内，nginx会代理到web:8000
  // 如果直接访问，nginx会代理到host.docker.internal:8000
  if (typeof window !== 'undefined') {
    // 浏览器环境：使用相对路径，让nginx代理处理
    return '';
  }
  
  // Node.js环境（SSR等）：使用环境变量或默认值
  const viteBase = (import.meta as any).env?.VITE_API_BASE as string | undefined;
  const winBase = (globalThis as any).__API_BASE__ as string | undefined;
  return viteBase || winBase || 'http://localhost:8000';
}

export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const base = getApiBase().replace(/\/$/, '');
  const url = `${base}${path.startsWith('/') ? path : `/${path}`}`;
  return fetch(url, init);
}


