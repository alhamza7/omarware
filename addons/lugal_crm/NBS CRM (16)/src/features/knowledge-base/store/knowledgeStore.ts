import { create } from 'zustand';
import type { Article, Circular } from '../services/knowledgeService';

interface KnowledgeStore {
  articles:        Article[];
  circulars:       Circular[];
  selectedArticle: Article | null;
  total:           number;
  isLoading:       boolean;
  error:           string | null;
  searchQuery:     string;
  category:        string | null;

  setArticles:        (articles: Article[], total: number) => void;
  setCirculars:       (circulars: Circular[]) => void;
  setSelectedArticle: (article: Article | null) => void;
  setLoading:         (loading: boolean) => void;
  setError:           (error: string | null) => void;
  setSearchQuery:     (q: string) => void;
  setCategory:        (cat: string | null) => void;
  updateArticle:      (article: Article) => void;
}

export const useKnowledgeStore = create<KnowledgeStore>((set) => ({
  articles:        [],
  circulars:       [],
  selectedArticle: null,
  total:           0,
  isLoading:       false,
  error:           null,
  searchQuery:     '',
  category:        null,

  setArticles:        (articles, total) => set({ articles, total, isLoading: false }),
  setCirculars:       (circulars) => set({ circulars }),
  setSelectedArticle: (selectedArticle) => set({ selectedArticle }),
  setLoading:         (isLoading) => set({ isLoading }),
  setError:           (error) => set({ error, isLoading: false }),
  setSearchQuery:     (searchQuery) => set({ searchQuery }),
  setCategory:        (category) => set({ category }),
  updateArticle:      (updated) =>
    set((s) => ({
      articles:        s.articles.map((a) => (a.id === updated.id ? updated : a)),
      selectedArticle: s.selectedArticle?.id === updated.id ? updated : s.selectedArticle,
    })),
}));
