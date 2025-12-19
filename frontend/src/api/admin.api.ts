import apiClient from './client';

export interface Department {
  id: number;
  name: string;
  code: string;
}

export interface DocumentType {
  id: number;
  name: string;
  code: string;
  department_id: number;
  department_name: string;
}

export interface Tag {
  id: number;
  name: string;
}

export interface DashboardStats {
  success: boolean;
  stats: {
    total_documents: number;
    my_documents: number;
    pending_approvals: number;
    recent_uploads: number;
    unread_notifications?: number;
    by_department?: Array<{ department: string; count: number }>;
  };
}

export interface AuditLog {
  id: number;
  user_id: number;
  user_name: string;
  action: string;
  document_id?: number;
  document_title?: string;
  department_id?: number;
  department_name?: string;
  timestamp: string;
  ip_address: string;
  metadata?: string;
}

export interface AdminUserRow {
  id: number;
  name: string;
  login: string;
  email?: string | null;
  role: 'employee' | 'manager' | 'admin';
  department_ids: number[];
  manager_department_ids: number[];
}

export const adminApi = {
  /**
   * Get all departments
   */
  getDepartments: async (): Promise<{ success: boolean; data: Department[] }> => {
    const response = await apiClient.post('/api/departments', {
      jsonrpc: '2.0',
      method: 'call',
      params: {},
    });
    return response.data.result || response.data;
  },

  /**
   * Get document types
   */
  getDocumentTypes: async (department_id?: number): Promise<{ success: boolean; data: DocumentType[] }> => {
    const response = await apiClient.post('/api/document-types', {
      jsonrpc: '2.0',
      method: 'call',
      params: { department_id },
    });
    return response.data.result || response.data;
  },

  /**
   * Get all tags
   */
  getTags: async (): Promise<{ success: boolean; data: Tag[] }> => {
    const response = await apiClient.post('/api/tags', {
      jsonrpc: '2.0',
      method: 'call',
      params: {},
    });
    return response.data.result || response.data;
  },

  /**
   * Get audit logs
   */
  getAuditLogs: async (params?: {
    document_id?: number;
    action?: string;
    date_from?: string;
    date_to?: string;
    page?: number;
    per_page?: number;
  }): Promise<{
    success: boolean;
    data: AuditLog[];
    pagination: { total: number; page: number; per_page: number };
  }> => {
    const response = await apiClient.post('/api/audit-logs', {
      jsonrpc: '2.0',
      method: 'call',
      params: params || {},
    });
    return response.data.result || response.data;
  },

  /**
   * Get dashboard stats
   */
  getDashboardStats: async (): Promise<DashboardStats> => {
    try {
      const response = await apiClient.post('/api/stats/dashboard', {
        jsonrpc: '2.0',
        method: 'call',
        params: {},
      });
      return response.data.result || response.data;
    } catch (error: any) {
      // Return empty stats if endpoint not ready
      return {
        success: true,
        stats: {
          total_documents: 0,
          my_documents: 0,
          pending_approvals: 0,
          recent_uploads: 0,
        }
      };
    }
  },

  /**
   * Admin: list users + roles + department access
   */
  getUsers: async (search?: string): Promise<{ success: boolean; data: AdminUserRow[]; error?: string }> => {
    const response = await apiClient.post('/api/nbs/admin/users', { search });
    return response.data;
  },

  /**
   * Admin: update user role + departments
   */
  updateUser: async (
    userId: number,
    payload: { role?: 'employee' | 'manager' | 'admin'; department_ids?: number[]; manager_department_ids?: number[] }
  ): Promise<{ success: boolean; error?: string }> => {
    const response = await apiClient.post(`/api/nbs/admin/users/${userId}/update`, payload);
    return response.data;
  },
};
