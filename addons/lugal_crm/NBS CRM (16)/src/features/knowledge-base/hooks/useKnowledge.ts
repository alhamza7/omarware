import { useCallback, useEffect } from 'react';
import { useKnowledgeStore } from '../store/knowledgeStore';
import { knowledgeService } from '../services/knowledgeService';
import type { Article } from '../services/knowledgeService';

export function useKnowledge() {
  const store = useKnowledgeStore();

  const fetchArticles = useCallback(async () => {
    store.setLoading(true);
    const [artRes, circRes] = await Promise.all([
      knowledgeService.listArticles({
        search:   store.searchQuery || undefined,
        category: store.category ?? undefined,
      }),
      knowledgeService.listCirculars(),
    ]);
    if (artRes.success && artRes.data)   store.setArticles(artRes.data.items ?? [], artRes.data.total ?? 0);
    /** notifications/list returns { items: [] } — extract the array */
    if (circRes.success && circRes.data) store.setCirculars(circRes.data.items ?? []);
    if (!artRes.success) store.setError(artRes.error ?? 'Failed to load articles');
    else store.setLoading(false);
  }, [store.searchQuery, store.category]);

  const openArticle = useCallback(async (id: number) => {
    const result = await knowledgeService.getArticle(id);
    if (result.success && result.data) store.setSelectedArticle(result.data);
    return result;
  }, [store]);

  const createArticle = useCallback(async (payload: Partial<Article>) => {
    const result = await knowledgeService.createArticle(payload);
    if (result.success) await fetchArticles();
    return result;
  }, [fetchArticles]);

  const updateArticle = useCallback(async (id: number, payload: Partial<Article>) => {
    const result = await knowledgeService.updateArticle(id, payload);
    if (result.success && result.data) store.updateArticle(result.data);
    return result;
  }, [store]);

  useEffect(() => {
    fetchArticles();
  }, [fetchArticles]);

  return {
    articles:        store.articles,
    circulars:       store.circulars,
    selectedArticle: store.selectedArticle,
    total:           store.total,
    isLoading:       store.isLoading,
    error:           store.error,
    setSelected:     store.setSelectedArticle,
    setSearchQuery:  store.setSearchQuery,
    setCategory:     store.setCategory,
    fetchArticles,
    openArticle,
    createArticle,
    updateArticle,
  };
}
