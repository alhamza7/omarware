import apiClient from './client';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
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
  };
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface RefreshResponse {
  success: boolean;
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  success: boolean;
  user: {
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
    uploaded_documents: number;
    pending_approvals: number;
    unread_notifications: number;
  };
}

export const authApi = {
  /**
   * Login
   */
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post('/api/auth/login', {
      username: data.username,
      password: data.password,
    });
    return response.data;
  },

  /**
   * Refresh access token
   */
  refresh: async (data: RefreshRequest): Promise<RefreshResponse> => {
    const response = await apiClient.post('/api/auth/refresh', data);
    return response.data;
  },

  /**
   * Logout
   */
  logout: async (): Promise<void> => {
    const refreshToken = localStorage.getItem('refresh_token');
    await apiClient.post('/api/auth/logout', { refresh_token: refreshToken });
    
    // Clear local storage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },

  /**
   * Get current user
   */
  getCurrentUser: async (): Promise<UserResponse> => {
    const response = await apiClient.post('/api/auth/me', {});
    return response.data;
  },
};

