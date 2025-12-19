import apiClient from './client';
import { Document } from './documents.api';

export interface SearchParams {
  query: string;
  search_in_content?: boolean;
  department_id?: number;
  document_type_id?: number;
  filters?: any;
  date_from?: string;
  date_to?: string;
  fuzzy?: boolean;
  page?: number;
  per_page?: number;
}

export interface SearchResponse {
  success: boolean;
  data: Document[];
  content_matches?: any[];
  pagination: {
    total: number;
    page: number;
    per_page: number;
  };
}

export const searchApi = {
  /**
   * Search documents
   */
  searchDocuments: async (params: SearchParams): Promise<SearchResponse> => {
    const response = await apiClient.post('/api/search', {
      jsonrpc: '2.0',
      method: 'call',
      params,
    });
    return response.data.result || response.data;
  },

  /**
   * Global search (documents + folders + attachments + OCR matches if available)
   */
  globalSearch: async (params: { query: string; search_in_content?: boolean; fuzzy?: boolean; page?: number; per_page?: number }) => {
    const response = await apiClient.post('/api/search/global', {
      jsonrpc: '2.0',
      method: 'call',
      params,
    });
    return response.data.result || response.data;
  },

  /**
   * Search by barcode
   */
  searchByBarcode: async (barcode: string): Promise<{ success: boolean; found: boolean; data?: any }> => {
    const response = await apiClient.post('/api/search/barcode', {
      jsonrpc: '2.0',
      method: 'call',
      params: { barcode },
    });
    return response.data.result || response.data;
  },
};
