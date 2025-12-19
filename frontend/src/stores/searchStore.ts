import { create } from 'zustand';
import { searchApi } from '../api/search.api';
import { handleApiError } from '../api/client';

interface SearchState {
  results: any[];
  query: string;
  isLoading: boolean;
  error: string | null;
  took_ms: number;
  pagination: {
    total: number;
    page: number;
    per_page: number;
  };

  // Actions
  search: (query: string, filters?: any, page?: number) => Promise<void>;
  globalSearch: (query: string, page?: number) => Promise<void>;
  searchByBarcode: (barcode: string) => Promise<any>;
  clearResults: () => void;
  clearError: () => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  results: [],
  query: '',
  isLoading: false,
  error: null,
  took_ms: 0,
  pagination: {
    total: 0,
    page: 1,
    per_page: 20,
  },

  search: async (query, filters = {}, page = 1) => {
    set({ isLoading: true, error: null, query });
    
    try {
      const response = await searchApi.searchDocuments({
        query,
        filters,
        fuzzy: true,
        page,
        per_page: 20,
      });
      
      const data = (response as any)?.data ?? [];
      set({
        results: Array.isArray(data) ? data : [],
        pagination: (response as any)?.pagination || { total: 0, page: 1, per_page: 20 },
        took_ms: (response as any)?.took_ms || 0,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: handleApiError(error),
        results: [],
        isLoading: false,
      });
    }
  },

  globalSearch: async (query, page = 1) => {
    set({ isLoading: true, error: null, query });

    try {
      const response = await (searchApi as any).globalSearch({
        query,
        search_in_content: true,
        fuzzy: true,
        page,
        per_page: 50,
      });

      const data = (response as any)?.data ?? [];
      set({
        results: Array.isArray(data) ? data : [],
        pagination: (response as any)?.pagination || { total: 0, page: 1, per_page: 50 },
        took_ms: (response as any)?.took_ms || 0,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: handleApiError(error),
        results: [],
        isLoading: false,
      });
    }
  },

  searchByBarcode: async (barcode) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await searchApi.searchByBarcode(barcode);
      
      set({ isLoading: false });
      
      return response;
    } catch (error) {
      set({
        error: handleApiError(error),
        isLoading: false,
      });
      throw error;
    }
  },

  clearResults: () => set({ results: [], query: '', pagination: { total: 0, page: 1, per_page: 20 } }),
  
  clearError: () => set({ error: null }),
}));


