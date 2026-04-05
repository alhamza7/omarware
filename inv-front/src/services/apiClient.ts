import axios from 'axios';

const TOKEN_KEY = 'inv_token';
const USER_KEY  = 'inv_user';

/** Get stored JWT token */
export const getToken = (): string | null => localStorage.getItem(TOKEN_KEY);

/** Store auth data after successful login */
export const setAuth = (token: string, user: object): void => {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

/** Get stored user object */
export const getUser = <T>(): T | null => {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as T) : null;
};

/** Clear auth data on logout */
export const clearAuth = (): void => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

/** Check if user is authenticated */
export const isAuthenticated = (): boolean => !!getToken();

const apiClient = axios.create({
  baseURL: '/api/inventory/v1',
  headers: { 'Content-Type': 'application/json' },
});

/** Attach Bearer token to every outgoing request */
apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

/** On 401, clear auth and redirect to login page */
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status;
    if (status === 401) {
      clearAuth();
      if (window.location.pathname !== '/') {
        window.location.href = '/';
        return new Promise(() => {}); // stop error propagation during redirect
      }
    }
    const responseData = err.response?.data as { error?: string; message?: string } | undefined;
    const serverMsg = responseData?.error ?? responseData?.message;
    const msg = serverMsg ?? err.message ?? 'خطأ في الاتصال بالخادم';
    return Promise.reject(new Error(msg));
  }
);

export default apiClient;
