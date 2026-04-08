import { useCallback, useEffect } from 'react';
import { useDashboardStore } from '../store/dashboardStore';
import type { VipCustomer } from '../store/dashboardStore';
import { dashboardService } from '../services/dashboardService';
import { customerService } from '../../customers/services/customerService';
import type { Notification, RecentOrder } from '../types';

/** Helper: safely extract items array from a paginated response data object */
function extractItems<T>(data: unknown): T[] {
  if (!data || typeof data !== 'object') return [];
  const d = data as Record<string, unknown>;
  if (Array.isArray(d['items'])) return d['items'] as T[];
  if (Array.isArray(d)) return data as T[];
  return [];
}

export function useDashboard(branchId?: number) {
  const store = useDashboardStore();

  const fetchDashboard = useCallback(async () => {
    store.setLoading(true);
    const [statsRes, notifRes, ordersRes, vipRes] = await Promise.all([
      dashboardService.getDashboardStats(branchId),
      dashboardService.getNotifications(),
      dashboardService.getRecentOrders(branchId),
      /** Top 5 VIP customers for the summary card */
      customerService.listCustomers({ vip_only: true, per_page: 5, page: 1 }),
    ]);

    if (statsRes.success && statsRes.data) store.setStats(statsRes.data);

    if (notifRes.success && notifRes.data) {
      const items = extractItems<Notification>(notifRes.data);
      store.setNotifications(items.map((n) => ({ is_read: false, ...n })));
    }

    if (ordersRes.success && ordersRes.data) {
      store.setRecentOrders(extractItems<RecentOrder>(ordersRes.data));
    }

    if (vipRes.success && vipRes.data) {
      /** Map customer records to VipCustomer shape */
      const raw = extractItems<Record<string, unknown>>(vipRes.data);
      const mapped: VipCustomer[] = raw.map((c) => ({
        id:     c['id'] as number,
        name:   (c['name'] as string) || '—',
        since:  c['create_date'] ? String(c['create_date']).substring(0, 10) : undefined,
        status: c['is_vip'] ? 'VIP' : 'نشط',
      }));
      store.setVipCustomers(mapped);
    }

    if (!statsRes.success) store.setError(statsRes.error ?? 'Failed to load dashboard');
    else store.setLoading(false);
  }, [branchId]);

  const markRead = useCallback(async (id: number) => {
    store.markRead(id);
    await dashboardService.markNotificationRead(id);
  }, [store]);

  const markAllRead = useCallback(async () => {
    store.markAllRead();
    await dashboardService.markAllRead();
  }, [store]);

  const removeNotification = useCallback((id: number) => {
    store.removeNotification(id);
  }, [store]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return {
    stats:              store.stats,
    notifications:      store.notifications,
    recentOrders:       store.recentOrders,
    vipCustomers:       store.vipCustomers,
    isLoading:          store.isLoading,
    error:              store.error,
    unreadCount:        store.notifications.filter((n) => !n.is_read).length,
    fetchDashboard,
    markRead,
    markAllRead,
    removeNotification,
  };
}
