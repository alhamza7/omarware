/**
 * Aggregate dashboard KPI stats returned by /api/crm/analytics/dashboard_stats.
 * The backend returns nested objects grouped by entity type.
 */
export interface DashboardStats {
  customers: {
    total:     number;
    vip:       number;
    new_today: number;
  };
  tickets: {
    open:          number;
    resolved:      number;
    high_priority: number;
  };
  calls: {
    total:  number;
    missed: number;
  };
  messages: {
    inbound:       number;
    pending_reply: number;
    sla_breached:  number;
  };
  tasks: {
    overdue: number;
  };
}

/**
 * In-app notification from /api/crm/kb/notifications/list.
 * `is_read` is managed client-side only (no backend endpoint).
 */
export interface Notification {
  id:                 number;
  title:              string;
  body?:              string;
  notification_type?: string;
  branch_ids?:        number[];
  created_at:         string;
  is_read:            boolean;
}

/** Recent order item from /api/crm/delivery/customer_orders */
export interface RecentOrder {
  id:            number;
  name?:         string;
  partner_id?:   number;
  partner_name?: string;
  status?:       string;
  total?:        number;
  date?:         string;
}
