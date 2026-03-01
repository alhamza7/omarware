/**
 * Central HTTP client for all Lugal CRM API calls.
 *
 * In development: VITE_API_BASE_URL is empty → all requests go to the Vite
 * dev server (port 5173) which proxies /api/* and /lugal/* to Odoo, fully
 * avoiding CORS issues.
 *
 * In production: VITE_API_BASE_URL is set to the actual Odoo backend URL.
 * In that case the backend must serve CORS headers (handled by lugal_crm
 * CorsController on the backend).
 */

/** Empty string in dev (uses Vite proxy); full URL in production */
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';
const DB_NAME  = import.meta.env.VITE_DB_NAME ?? 'lugal_db';

/** Standard JSON-RPC response wrapper from Odoo */
export interface JsonRpcResponse<T = unknown> {
  jsonrpc: '2.0';
  id:      number | null;
  result?: { success: boolean; data?: T; error?: string; code?: number };
  error?:  { code: number; message: string; data?: unknown };
}

/** Generic API result used by all services */
export interface ApiResult<T = unknown> {
  success: boolean;
  data?:   T;
  error?:  string;
}

let _requestId = 1;

/** Get stored JWT access token */
export const getAccessToken = (): string | null =>
  localStorage.getItem('lugal_access_token');

/** Get stored JWT refresh token */
export const getRefreshToken = (): string | null =>
  localStorage.getItem('lugal_refresh_token');

/** Persist tokens after login */
export const setTokens = (access: string, refresh: string): void => {
  localStorage.setItem('lugal_access_token', access);
  localStorage.setItem('lugal_refresh_token', refresh);
};

/** Clear tokens on logout */
export const clearTokens = (): void => {
  localStorage.removeItem('lugal_access_token');
  localStorage.removeItem('lugal_refresh_token');
  localStorage.removeItem('lugal_user');
};

/**
 * Core JSON-RPC call to Odoo backend.
 * @param route  - Odoo route (e.g. '/lugal/auth/login')
 * @param params - JSON-RPC params object
 * @param auth   - Whether to attach Bearer token header
 */
async function rpc<T>(
  route: string,
  params: Record<string, unknown> = {},
  auth = true,
): Promise<ApiResult<T>> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (auth) {
    const token = getAccessToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  /**
   * Pass db as a JSON-RPC param instead of a custom header.
   * Custom headers (X-Odoo-Database) trigger CORS preflight failures when
   * the backend has not explicitly allowed them.
   */
  const body = JSON.stringify({
    jsonrpc: '2.0',
    method:  'call',
    id:      _requestId++,
    params:  { db: DB_NAME, ...params },
  });

  try {
    const res = await fetch(`${API_BASE}${route}`, {
      method:  'POST',
      headers,
      body,
    });

    const json: JsonRpcResponse<T> = await res.json();

    if (json.error) {
      return { success: false, error: json.error.message ?? 'Server error' };
    }

    if (json.result) {
      const result = json.result as Record<string, unknown>;
      if (result['success'] === false) {
        return { success: false, error: (result['error'] as string) ?? 'Unknown error' };
      }
      /**
       * Odoo controllers return two different shapes:
       *   1. { success: true, data: { ... } }   — auth, single-record endpoints
       *   2. { success: true, items: [...], total, page } — list endpoints (flat)
       *
       * If the result has a 'data' key we unwrap it; otherwise we return
       * the whole result object so callers can access result.data.items etc.
       */
      const payload = 'data' in result ? result['data'] : result;
      return { success: true, data: payload as T };
    }

    return { success: false, error: 'Invalid response format' };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Network error';
    return { success: false, error: message };
  }
}

/**
 * Authenticated POST — used by all feature services.
 * Automatically attempts token refresh on 401.
 */
export async function apiPost<T>(
  route: string,
  params: Record<string, unknown> = {},
): Promise<ApiResult<T>> {
  const result = await rpc<T>(route, params, true);

  // Try refresh once on auth error
  if (!result.success && result.error?.toLowerCase().includes('unauthorized')) {
    const refreshed = await tryRefreshToken();
    if (refreshed) return rpc<T>(route, params, true);
  }

  return result;
}

/**
 * Public POST — no auth header (login, refresh).
 */
export async function apiPublicPost<T>(
  route: string,
  params: Record<string, unknown> = {},
): Promise<ApiResult<T>> {
  return rpc<T>(route, params, false);
}

/** Attempt to refresh the access token silently. Returns true on success. */
async function tryRefreshToken(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) return false;

  const result = await rpc<{ access_token: string }>(
    '/lugal/auth/refresh',
    { refresh_token: refresh },
    false,
  );

  if (result.success && result.data?.access_token) {
    localStorage.setItem('lugal_access_token', result.data.access_token);
    return true;
  }

  clearTokens();
  return false;
}
