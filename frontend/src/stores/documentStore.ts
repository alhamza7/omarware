import { create } from 'zustand';
import { documentsApi, Document, DocumentDetail } from '../api/documents.api';
import { handleApiError } from '../api/client';

interface DocumentState {
  documents: Document[];
  currentDocument: DocumentDetail | null;
  isLoading: boolean;
  error: string | null;
  pagination: {
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  };

  // Actions
  fetchDocuments: (params?: any) => Promise<void>;
  fetchDocument: (id: number) => Promise<void>;
  uploadDocument: (data: any) => Promise<number>;
  uploadVersion: (documentId: number, data: any) => Promise<void>;
  downloadVersion: (documentId: number, versionId: number, fileName: string) => Promise<void>;
  archiveDocument: (documentId: number) => Promise<void>;
  clearError: () => void;
  clearCurrentDocument: () => void;
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  currentDocument: null,
  isLoading: false,
  error: null,
  pagination: {
    total: 0,
    page: 1,
    per_page: 20,
    total_pages: 0,
  },

  fetchDocuments: async (params) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await documentsApi.getDocuments(params);
      
      console.log('Documents response:', response);
      
      set({
        documents: response?.data || [],
        pagination: response?.pagination || { total: 0, page: 1, per_page: 20, total_pages: 0 },
        isLoading: false,
      });
    } catch (error) {
      console.error('Fetch documents error:', error);
      set({
        documents: [], // Set empty array on error
        error: handleApiError(error),
        isLoading: false,
      });
    }
  },

  fetchDocument: async (id) => {
    if (!id || isNaN(id)) {
      console.error('Invalid document ID:', id);
      set({ error: 'Invalid document ID', isLoading: false });
      return;
    }
    
    set({ isLoading: true, error: null });
    
    try {
      const response = await documentsApi.getDocument(id);
      
      set({
        currentDocument: response?.data || null,
        isLoading: false,
      });
    } catch (error) {
      console.error('Fetch document error:', error);
      set({
        currentDocument: null,
        error: handleApiError(error),
        isLoading: false,
      });
    }
  },

  uploadDocument: async (data) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await documentsApi.uploadDocument(data);
      
      set({ isLoading: false });
      
      return response.data.id;
    } catch (error) {
      set({
        error: handleApiError(error),
        isLoading: false,
      });
      throw error;
    }
  },

  uploadVersion: async (documentId, data) => {
    set({ isLoading: true, error: null });
    
    try {
      await documentsApi.uploadVersion(
        documentId,
        data.file_data,
        data.file_name,
        data.unlock_token,
        data.change_description
      );
      
      // Refresh document details
      await get().fetchDocument(documentId);
      
      set({ isLoading: false });
    } catch (error) {
      set({
        error: handleApiError(error),
        isLoading: false,
      });
      throw error;
    }
  },

  downloadVersion: async (documentId, versionId, fileName) => {
    set({ isLoading: true, error: null });
    
    try {
      const blob = await documentsApi.downloadDocument(documentId, versionId);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      set({ isLoading: false });
    } catch (error) {
      set({
        error: handleApiError(error),
        isLoading: false,
      });
    }
  },

  archiveDocument: async (documentId) => {
    set({ isLoading: true, error: null });
    
    try {
      await documentsApi.archiveDocument(documentId);
      
      // Refresh documents list
      await get().fetchDocuments();
      
      set({ isLoading: false });
    } catch (error) {
      set({
        error: handleApiError(error),
        isLoading: false,
      });
      throw error;
    }
  },

  clearError: () => set({ error: null }),
  
  clearCurrentDocument: () => set({ currentDocument: null }),
}));

