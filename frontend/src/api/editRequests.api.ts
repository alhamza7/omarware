import apiClient from './client';

export interface EditRequest {
  id: number;
  document_id: number;
  document_title: string;
  requester_id: number;
  requester_name: string;
  reason: string;
  state: 'pending' | 'approved' | 'rejected' | 'completed' | 'expired';
  request_date: string;
  response_date?: string;
  approver_id?: number;
  approver_name?: string;
  rejection_reason?: string;
}

export interface EditRequestsResponse {
  success: boolean;
  data: EditRequest[];
  pagination: {
    total: number;
    page: number;
    per_page: number;
  };
}

export const editRequestsApi = {
  /**
   * Get list of edit requests
   */
  getEditRequests: async (params?: {
    state?: string;
    document_id?: number;
    page?: number;
    per_page?: number;
  }): Promise<EditRequestsResponse> => {
    const response = await apiClient.post('/api/edit-requests', {
      jsonrpc: '2.0',
      method: 'call',
      params: params || {},
    });
    return response.data.result || response.data;
  },

  /**
   * Create new edit request
   */
  createEditRequest: async (document_id: number, reason: string): Promise<{ success: boolean; data: { id: number } }> => {
    const response = await apiClient.post('/api/edit-requests/create', {
      jsonrpc: '2.0',
      method: 'call',
      params: {
        document_id,
        reason,
      },
    });
    return response.data.result || response.data;
  },

  /**
   * Approve edit request
   */
  approveEditRequest: async (request_id: number): Promise<{ success: boolean; data: { unlock_token: string } }> => {
    const response = await apiClient.post(`/api/edit-requests/${request_id}/approve`, {
      jsonrpc: '2.0',
      method: 'call',
      params: { request_id },
    });
    return response.data.result || response.data;
  },

  /**
   * Reject edit request
   */
  rejectEditRequest: async (request_id: number, rejection_reason: string): Promise<{ success: boolean }> => {
    const response = await apiClient.post(`/api/edit-requests/${request_id}/reject`, {
      jsonrpc: '2.0',
      method: 'call',
      params: {
        request_id,
        rejection_reason,
      },
    });
    return response.data.result || response.data;
  },

  /**
   * Get pending approvals (for managers)
   */
  getPendingApprovals: async (): Promise<{ success: boolean; data: EditRequest[] }> => {
    const response = await apiClient.post('/api/edit-requests/pending-approvals', {
      jsonrpc: '2.0',
      method: 'call',
      params: {},
    });
    return response.data.result || response.data;
  },
};
