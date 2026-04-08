import { create } from 'zustand';
import type { DashboardStats, Notification, RecentOrder } from '../types';

export interface VipCustomer {
  id:   number;
  name: string;
  since?: string;
  status: string;
}

interface DashboardStore {
  stats:         DashboardStats | null;
  notifications: Notification[];
  recentOrders:  RecentOrder[];
  vipCustomers:  VipCustomer[];
  isLoading:     boolean;
  error:         string | null;

  setStats:           (stats: DashboardStats) => void;
  setNotifications:   (notifications: Notification[]) => void;
  setRecentOrders:    (orders: RecentOrder[]) => void;
  setVipCustomers:    (customers: VipCustomer[]) => void;
  markRead:           (id: number) => void;
  markAllRead:        () => void;
  removeNotification: (id: number) => void;
  setLoading:         (loading: boolean) => void;
  setError:           (error: string | null) => void;
}

export const useDashboardStore = create<DashboardStore>((set) => ({
  stats:         null,
  notifications: [],
  recentOrders:  [],
  vipCustomers:  [],
  isLoading:     false,
  error:         null,

  setStats:         (stats) => set({ stats }),
  setNotifications: (notifications) => set({ notifications }),
  setRecentOrders:  (recentOrders) => set({ recentOrders }),
  setVipCustomers:  (vipCustomers) => set({ vipCustomers }),
  markRead:         (id) =>
    set((s) => ({
      notifications: s.notifications.map((n) =>
        n.id === id ? { ...n, is_read: true } : n,
      ),
    })),
  markAllRead: () =>
    set((s) => ({
      notifications: s.notifications.map((n) => ({ ...n, is_read: true })),
    })),
  removeNotification: (id) =>
    set((s) => ({ notifications: s.notifications.filter((n) => n.id !== id) })),
  setLoading: (isLoading) => set({ isLoading }),
  setError:   (error) => set({ error, isLoading: false }),
}));
