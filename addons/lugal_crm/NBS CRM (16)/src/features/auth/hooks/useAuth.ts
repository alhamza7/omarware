import { useCallback } from 'react';
import { useAuthStore } from '../store/authStore';
import { authService } from '../services/authService';

/**
 * Main auth hook — use this in components and containers.
 * Wraps the store and service into a single clean interface.
 */
export function useAuth() {
  const { user, isLoggedIn, isLoading, error, setUser, setLoading, setError, clearSession } =
    useAuthStore();

  /** Login with username + password */
  const login = useCallback(
    async (username: string, password: string) => {
      setLoading(true);
      setError(null);
      const result = await authService.login(username, password);
      if (result.success && result.data) {
        setUser(result.data.user);
      } else {
        setError(result.error ?? 'Login failed');
      }
      return result.success;
    },
    [setLoading, setError, setUser],
  );

  /** Logout — clears tokens + store */
  const logout = useCallback(async () => {
    await authService.logout();
    clearSession();
  }, [clearSession]);

  /** Restore session from localStorage on app mount */
  const restoreSession = useCallback(() => {
    const savedUser = authService.restoreSession();
    if (savedUser) setUser(savedUser);
    return !!savedUser;
  }, [setUser]);

  return { user, isLoggedIn, isLoading, error, login, logout, restoreSession };
}
