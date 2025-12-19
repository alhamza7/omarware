import { create } from 'zustand';
import { authApi, LoginRequest } from '../api/auth.api';
import { handleApiError } from '../api/client';

interface User {
  id: number;
  name: string;
  username: string;
  email: string;
  departments: Array<{
    id: number;
    name: string;
    code: string;
    role: string;
  }>;
  language: string;
  is_admin: boolean;
  is_manager?: boolean;
  uploaded_documents?: number;
  pending_approvals?: number;
  unread_notifications?: number;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  setLanguage: (lang: string) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => {
  // Safely parse user from localStorage
  const getUserFromStorage = () => {
    try {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (e) {
      console.error('Failed to parse user from localStorage:', e);
      return null;
    }
  };
  
  return {
  user: getUserFromStorage(),
  accessToken: localStorage.getItem('access_token') || null,
  refreshToken: localStorage.getItem('refresh_token') || null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,

  login: async (credentials) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await authApi.login(credentials);
      
      console.log('Login response:', response);
      
      // Check if response is valid
      if (!response || !response.success) {
        throw new Error('Login failed');
      }
      
      // Save tokens
      localStorage.setItem('access_token', response.access_token || '');
      localStorage.setItem('refresh_token', response.refresh_token || '');
      localStorage.setItem('user', JSON.stringify(response.user || {}));
      
      set({
        user: response.user || null,
        accessToken: response.access_token || null,
        refreshToken: response.refresh_token || null,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      const errorMessage = handleApiError(error);
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  logout: async () => {
    set({ isLoading: true });
    
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear state regardless of API result
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    }
  },

  refreshUser: async () => {
    try {
      const response = await authApi.getCurrentUser();
      
      if (response && response.success && response.user) {
        // Update user in localStorage and state
        localStorage.setItem('user', JSON.stringify(response.user));
        
        set({
          user: response.user,
          error: null,
        });
      }
    } catch (error) {
      const errorMessage = handleApiError(error);
      console.error('Refresh user error:', errorMessage);
      set({ error: null }); // Don't show error for background refresh
    }
  },

  setLanguage: (lang) => {
    const { user } = get();
    if (user) {
      const updatedUser = { ...user, language: lang };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      set({ user: updatedUser });
    }
  },

  clearError: () => set({ error: null }),
}
});

