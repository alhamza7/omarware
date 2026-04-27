import apiClient from './apiClient';
import type { UserData } from '../app/components/admin/types';

interface UsersApiResponse {
  success: boolean;
  data: { users: UserData[]; total: number; page: number; per_page: number };
}

export interface FetchUsersResult { users: UserData[]; total: number; }

/** Fetch paginated inventory users list */
export async function fetchUsers(page = 1, perPage = 25, search = ''): Promise<FetchUsersResult> {
  const { data } = await apiClient.get<UsersApiResponse>('/users', {
    params: { page, per_page: perPage, search: search || undefined },
  });
  return { users: data.data.users ?? [], total: data.data.total ?? 0 };
}

/** Create a new inventory user */
export async function createUser(payload: {
  username: string;
  full_name: string;
  password: string;
  role: 'admin' | 'user';
  warehouse_id: number;
}): Promise<UserData> {
  const { data } = await apiClient.post<{ success: boolean; data: UserData }>('/users', payload);
  return data.data;
}

/** Delete an inventory user by ID */
export async function deleteUser(id: number): Promise<void> {
  await apiClient.delete(`/users/${id}`);
}

/** Odoo user who has no inventory record yet */
export interface OdooCandidate {
  id: number;
  name: string;
  login: string;
}

/** Fetch Odoo users not yet assigned to the inventory system */
export async function fetchOdooCandidates(): Promise<OdooCandidate[]> {
  const { data } = await apiClient.get<{ success: boolean; data: OdooCandidate[] }>(
    '/users/odoo-candidates'
  );
  return data.data ?? [];
}

/** Assign an existing Odoo user to the inventory system */
export async function importOdooUser(payload: {
  odoo_user_id: number;
  full_name: string;
  role: 'admin' | 'user';
  warehouse_id: number;
}): Promise<UserData> {
  const { data } = await apiClient.post<{ success: boolean; data: UserData }>('/users', {
    odoo_user_id: payload.odoo_user_id,
    full_name: payload.full_name,
    role: payload.role,
    warehouse_id: payload.warehouse_id,
  });
  return data.data;
}
