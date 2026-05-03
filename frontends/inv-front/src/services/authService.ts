import apiClient, { setAuth } from './apiClient';

export interface AuthUser {
  user_id: number;
  username: string;
  full_name: string;
  role: 'admin' | 'user';
  warehouse_id: number;
  warehouse_code: string;
  token: string;
}

/** Authenticate user and store credentials */
export async function loginUser(payload: {
  username: string;
  password: string;
  warehouse_id?: number;
}): Promise<AuthUser> {
  const { data } = await apiClient.post<{ success: boolean; data: AuthUser }>('/auth/login', payload);
  if (!data.success) throw new Error('فشل تسجيل الدخول');
  setAuth(data.data.token, data.data);
  return data.data;
}
