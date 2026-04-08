import { apiPost } from '../../../shared/services/apiClient';
import type { ApiResult } from '../../../shared/services/apiClient';
import type { PaginatedResponse } from '../../../shared/types';

export interface Article {
  id:           number;
  title:        string;
  title_ar?:    string;
  body?:        string;
  content?:     string;
  category?:    string;
  author_id?:   number;
  author_name?: string;
  branch_id?:   number;
  published:    boolean;
  created_at:   string;
  updated_at?:  string;
}

export interface KbNotification {
  id:           number;
  title:        string;
  body?:        string;
  notification_type?: string;
  branch_ids?:  number[];
  created_at:   string;
}

/**
 * POST /api/crm/kb/articles/list
 * List knowledge base articles with optional filters.
 */
async function listArticles(params: {
  page?: number;
  category?: string;
  search?: string;
  branch_id?: number;
  published_only?: boolean;
}): Promise<ApiResult<PaginatedResponse<Article>>> {
  return apiPost('/api/crm/kb/articles/list', {
    page:           params.page          ?? 1,
    per_page:       20,
    category:       params.category      ?? null,
    branch_id:      params.branch_id     ?? null,
    published_only: params.published_only ?? true,
  });
}

/**
 * POST /api/crm/kb/articles/search
 * Full-text search across articles.
 */
async function searchArticles(query: string, branchId?: number): Promise<ApiResult<Article[]>> {
  return apiPost('/api/crm/kb/articles/search', {
    query,
    branch_id: branchId ?? null,
    limit:     30,
  });
}

/** POST /api/crm/kb/articles/:id — get a single article */
async function getArticle(id: number): Promise<ApiResult<Article>> {
  return apiPost(`/api/crm/kb/articles/${id}`, {});
}

/** POST /api/crm/kb/articles/create */
async function createArticle(payload: Partial<Article>): Promise<ApiResult<Article>> {
  return apiPost('/api/crm/kb/articles/create', {
    title:     payload.title     ?? '',
    title_ar:  payload.title_ar  ?? null,
    content:   payload.content   ?? null,
    category:  payload.category  ?? 'document',
    branch_id: payload.branch_id ?? null,
  });
}

/** POST /api/crm/kb/articles/:id/update */
async function updateArticle(id: number, payload: Partial<Article>): Promise<ApiResult<Article>> {
  return apiPost(`/api/crm/kb/articles/${id}/update`, payload as Record<string, unknown>);
}

/** POST /api/crm/kb/articles/:id/delete */
async function deleteArticle(id: number): Promise<ApiResult<void>> {
  return apiPost(`/api/crm/kb/articles/${id}/delete`, {});
}

/**
 * POST /api/crm/kb/notifications/list
 * List circulars / KB push notifications.
 */
async function listCirculars(branchId?: number): Promise<ApiResult<KbNotification[]>> {
  return apiPost('/api/crm/kb/notifications/list', {
    branch_id: branchId ?? null,
    per_page:  50,
  });
}

/**
 * POST /api/crm/kb/notifications/push
 * Push a new circular / announcement to agents.
 */
async function pushNotification(payload: {
  title: string;
  body?: string;
  branch_ids?: number[];
  notification_type?: string;
}): Promise<ApiResult<KbNotification>> {
  return apiPost('/api/crm/kb/notifications/push', {
    title:             payload.title,
    body:              payload.body              ?? null,
    branch_ids:        payload.branch_ids        ?? null,
    notification_type: payload.notification_type ?? 'announcement',
  });
}

export const knowledgeService = {
  listArticles,
  searchArticles,
  getArticle,
  createArticle,
  updateArticle,
  deleteArticle,
  listCirculars,
  pushNotification,
};
