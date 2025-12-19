import apiClient from './client';

export interface SignatureRequest {
  id: number;
  document_id: number;
  document_title: string;
  requester_id: number;
  requester_name: string;
  signer_id: number;
  signer_name: string;
  state: 'pending' | 'approved' | 'signed' | 'rejected' | 'expired' | 'cancelled';
  request_date?: string | null;
  approval_date?: string | null;
  signed_date?: string | null;
  rejection_reason?: string | null;
}

export const signaturesApi = {
  list: async (params?: { state?: string; document_id?: number; page?: number; per_page?: number }) => {
    const response = await apiClient.post('/api/signatures', params || {});
    return response.data;
  },

  create: async (params: { document_id: number; signer_id: number; message?: string }) => {
    const response = await apiClient.post('/api/signatures/create', params);
    return response.data;
  },

  approve: async (request_id: number) => {
    const response = await apiClient.post(`/api/signatures/${request_id}/approve`, {});
    return response.data;
  },

  reject: async (request_id: number, rejection_reason?: string) => {
    const response = await apiClient.post(`/api/signatures/${request_id}/reject`, { rejection_reason });
    return response.data;
  },

  uploadSigned: async (request_id: number, params: { file_data: string; file_name: string; sign_token: string; notes?: string }) => {
    const response = await apiClient.post(`/api/signatures/${request_id}/upload-signed`, params);
    return response.data;
  },
};


