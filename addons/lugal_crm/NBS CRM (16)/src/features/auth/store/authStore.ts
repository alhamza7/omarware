import { create } from 'zustand';
import type { AuthUser } from '../types';

interface AuthStore {
  user:       AuthUser | null;
  isLoggedIn: boolean;
  isLoading:  boolean;
  error:      string | null;

  setUser:      (user: AuthUser) => void;
  setLoading:   (loading: boolean) => void;
  setError:     (error: string | null) => void;
  clearSession: () => void;
}

/** Global auth state — single source of truth for login status */
export const useAuthStore = create<AuthStore>((set) => ({
  user:       null,
  isLoggedIn: false,
  isLoading:  false,
  error:      null,

  setUser: (user) =>
    set({ user, isLoggedIn: true, error: null, isLoading: false }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error, isLoading: false }),

  clearSession: () =>
    set({ user: null, isLoggedIn: false, error: null, isLoading: false }),
}));
