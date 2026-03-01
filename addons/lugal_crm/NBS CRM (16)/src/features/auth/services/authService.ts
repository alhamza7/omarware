import {
  apiPublicPost,
  setTokens,
  clearTokens,
  getAccessToken,
} from '../../../shared/services/apiClient';
import type { ApiResult } from '../../../shared/services/apiClient';
import type { AuthTokens } from '../types';

/**
 * POST /lugal/auth/login
 * Authenticates user and stores JWT tokens in localStorage.
 */
async function login(
  username: string,
  password: string,
): Promise<ApiResult<AuthTokens>> {
  const result = await apiPublicPost<AuthTokens>('/lugal/auth/login', {
    username,
    password,
  });

  if (result.success && result.data) {
    setTokens(result.data.access_token, result.data.refresh_token);
    localStorage.setItem('lugal_user', JSON.stringify(result.data.user));
  }

  return result;
}

/**
 * POST /lugal/auth/logout
 * Revokes the current JWT token and clears localStorage.
 */
async function logout(): Promise<void> {
  const token = getAccessToken();
  if (token) {
    try {
      /** Use empty base URL so the request goes through Vite proxy in dev */
      const base = import.meta.env.VITE_API_BASE_URL ?? '';
      await fetch(`${base}/lugal/auth/logout`, {
        method:  'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization:  `Bearer ${token}`,
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method:  'call',
          id:      1,
          params:  { db: import.meta.env.VITE_DB_NAME ?? 'lugal_db' },
        }),
      });
    } catch {
      // Logout errors are silent — always clear local state
    }
  }
  clearTokens();
}

/**
 * Restore authenticated user from localStorage on app load.
 * Returns the user object or null if not authenticated.
 */
function restoreSession() {
  const raw = localStorage.getItem('lugal_user');
  if (!raw || !getAccessToken()) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export const authService = { login, logout, restoreSession };
