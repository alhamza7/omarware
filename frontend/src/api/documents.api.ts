import apiClient from './client';

export interface Document {
  id: number;
  title: string;
  department_id: number;
  department_name: string;
  document_type_id: number;
  document_type_name: string;
  uploader_id: number;
  uploader_name: string;
  upload_date: string;
  status: string;
  confidentiality_level: string;
  barcode: string;
  file_name: string;
  file_size: number;
}

export interface DocumentVersion {
  id: number;
  version_number: number;
  file_name: string;
  file_size: number;
  uploaded_by: string;
  upload_date: string;
  change_description: string;
  ocr_completed?: boolean;
  ocr_date?: string | null;
}

export interface DocumentDetail extends Document {
  is_locked: boolean;
  tags: Array<{ id: number; name: string }>;
  versions: DocumentVersion[];
  ocr_status?: string;
  ocr?: {
    current_version_id?: number | null;
    current_version_ocr_completed?: boolean;
    current_version_ocr_date?: string | null;
    extracted_text_preview?: string;
    extracted_text_length?: number;
  };
}

export interface DocumentsResponse {
  success: boolean;
  data: Document[];
  pagination: {
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  };
}

export interface DocumentDetailResponse {
  success: boolean;
  data: DocumentDetail;
}

export interface UploadDocumentRequest {
  department_id: number;
  document_type_id: number;
  title: string;
  file_data: string; // base64
  file_name: string;
  confidentiality_level: string;
  tags?: number[];
  custom_fields?: Record<string, any>;
}

export const documentsApi = {
  /**
   * Get list of documents
   */
  getDocuments: async (params?: {
    department_id?: number;
    document_type_id?: number;
    status?: string;
    search?: string;
    page?: number;
    per_page?: number;
  }): Promise<DocumentsResponse> => {
    const response = await apiClient.post('/api/documents', {
      jsonrpc: '2.0',
      method: 'call',
      params: params || {},
    });
    return response.data.result || response.data;
  },

  /**
   * Get single document details
   */
  getDocument: async (id: number): Promise<DocumentDetailResponse> => {
    const response = await apiClient.post(`/api/documents/${id}`, {
      jsonrpc: '2.0',
      method: 'call',
      params: { document_id: id },
    });
    return response.data.result || response.data;
  },

  /**
   * Upload new document
   */
  uploadDocument: async (data: any): Promise<{ success: boolean; data: { id: number; barcode: string }; error?: string }> => {
    const response = await apiClient.post('/api/documents/upload', data);
    return response.data;
  },

  /**
   * Download document or specific version
   */
  downloadDocument: async (documentId: number, versionId?: number): Promise<Blob> => {
    const url = versionId
      ? `/api/documents/${documentId}/download?version_id=${versionId}`
      : `/api/documents/${documentId}/download`;
    
    const response = await apiClient.get(url, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Archive document
   */
  archiveDocument: async (documentId: number): Promise<{ success: boolean }> => {
    const response = await apiClient.post(`/api/documents/${documentId}/archive`, {
      jsonrpc: '2.0',
      method: 'call',
      params: {},
    });
    return response.data.result || response.data;
  },

  /**
   * Unarchive document
   */
  unarchiveDocument: async (documentId: number): Promise<{ success: boolean }> => {
    const response = await apiClient.post(`/api/documents/${documentId}/unarchive`, {
      jsonrpc: '2.0',
      method: 'call',
      params: {},
    });
    return response.data.result || response.data;
  },

  /**
   * Get document versions
   */
  getVersions: async (documentId: number): Promise<{ success: boolean; data: DocumentVersion[] }> => {
    const response = await apiClient.post(`/api/documents/${documentId}/versions`, {
      jsonrpc: '2.0',
      method: 'call',
      params: { document_id: documentId },
    });
    return response.data.result || response.data;
  },

  /**
   * Upload new version (requires unlock token)
   */
  uploadVersion: async (
    documentId: number,
    file_data: string,
    file_name: string,
    unlock_token: string,
    change_description: string
  ): Promise<{ success: boolean }> => {
    const response = await apiClient.post(`/api/documents/${documentId}/upload-version`, {
      jsonrpc: '2.0',
      method: 'call',
      params: {
        document_id: documentId,
        file_data,
        file_name,
        unlock_token,
        change_description,
      },
    });
    return response.data.result || response.data;
  },
};
