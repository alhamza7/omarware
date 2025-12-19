import apiClient from './client';

export interface Notification {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_date: string;
  related_document_id?: number;
}

export interface NotificationsResponse {
  success: boolean;
  data: Notification[];
  unread_count: number;
  pagination: {
    total: number;
    page: number;
    per_page: number;
  };
}

export const notificationsApi = {
  /**
   * Get notifications
   */
  getNotifications: async (params?: { unread_only?: boolean; page?: number; per_page?: number }): Promise<NotificationsResponse> => {
    const unread_only = params?.unread_only ?? false;
    const page = params?.page ?? 1;
    const per_page = params?.per_page ?? 20;
    const response = await apiClient.post('/api/notifications', {
      jsonrpc: '2.0',
      method: 'call',
      params: {
        unread_only,
        page,
        per_page,
      },
    });
    return response.data.result || response.data;
  },

  /**
   * Mark notification as read
   */
  markAsRead: async (notificationId: number): Promise<{ success: boolean }> => {
    const response = await apiClient.post(`/api/notifications/${notificationId}/mark-read`, {
      jsonrpc: '2.0',
      method: 'call',
      params: { notification_id: notificationId },
    });
    return response.data.result || response.data;
  },

  /**
   * Mark all notifications as read
   */
  markAllAsRead: async (): Promise<{ success: boolean }> => {
    const response = await apiClient.post('/api/notifications/mark-all-read', {
      jsonrpc: '2.0',
      method: 'call',
      params: {},
    });
    return response.data.result || response.data;
  },

  /**
   * Get unread count
   */
  getUnreadCount: async (): Promise<{ success: boolean; count: number }> => {
    const response = await apiClient.post('/api/notifications/unread-count', {
      jsonrpc: '2.0',
      method: 'call',
      params: {},
    });
    return response.data.result || response.data;
  },

  /**
   * Poll for new notifications (fallback to WebSocket)
   */
  pollNotifications: async (last_poll_id = 0): Promise<{ success: boolean; data: Notification[]; has_new: boolean }> => {
    const response = await apiClient.post('/api/ws/poll', {
      jsonrpc: '2.0',
      method: 'call',
      params: { last_poll_id },
    });
    return response.data.result || response.data;
  },
};
