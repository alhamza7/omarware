import { apiPost } from '../../../shared/services/apiClient';
import type { ApiResult } from '../../../shared/services/apiClient';
import type { DashboardStats, Notification, RecentOrder } from '../types';

/**
 * POST /api/crm/analytics/dashboard_stats
 * Fetch all aggregate counts for the dashboard KPI cards.
 */
async function getDashboardStats(branchId?: number): Promise<ApiResult<DashboardStats>> {
  return apiPost('/api/crm/analytics/dashboard_stats', {
    branch_id: branchId ?? null,
  });
}

/**
 * POST /api/crm/kb/notifications/list
 * Fetch latest system/agent notifications (used as in-app notifications).
 */
async function listNotifications(branchId?: number): Promise<ApiResult<Notification[]>> {
  return apiPost('/api/crm/kb/notifications/list', {
    branch_id: branchId ?? null,
    per_page:  20,
  });
}

/**
 * POST /api/crm/delivery/customer_orders
 * Fetch recent orders shown on the dashboard feed.
 */
async function getRecentOrders(
  partnerId?: number,
  limit = 10,
): Promise<ApiResult<RecentOrder[]>> {
  return apiPost('/api/crm/delivery/customer_orders', {
    partner_id: partnerId ?? null,
    limit,
  });
}

/**
 * POST /api/crm/analytics/supervisor_dashboard
 * Supervisor-level metrics for branch managers.
 */
async function getSupervisorStats(branchId?: number): Promise<ApiResult<unknown>> {
  return apiPost('/api/crm/analytics/supervisor_dashboard', {
    branch_id: branchId ?? null,
  });
}

/**
 * Client-side stub — backend has no per-notification read endpoint.
 * Optimistically marks as read in store; no API call needed.
 */
async function markNotificationRead(_id: number): Promise<void> {
  // No backend endpoint — handled in-store only
}

/**
 * Client-side stub — backend has no bulk-read endpoint.
 * Optimistically marks all as read in store; no API call needed.
 */
async function markAllRead(): Promise<void> {
  // No backend endpoint — handled in-store only
}

/** Alias for listNotifications — keeps existing hook signatures working */
const getNotifications = listNotifications;

export const dashboardService = {
  getDashboardStats,
  listNotifications,
  getNotifications,
  getRecentOrders,
  getSupervisorStats,
  markNotificationRead,
  markAllRead,
};
