export interface KpiStats {
  total_customers:      number;
  new_customers_month:  number;
  active_customers:     number;
  vip_customers:        number;
  total_calls:          number;
  missed_calls:         number;
  resolved_tickets:     number;
  open_tickets:         number;
  avg_call_duration:    number;
  sla_breach_rate:      number;
}

export interface BranchStats {
  branch_id:    number;
  branch_name:  string;
  total_calls:  number;
  resolved:     number;
  open_tickets: number;
  vip_count:    number;
}

export interface EmployeeKpi {
  agent_id:          number;
  agent_name:        string;
  total_calls:       number;
  avg_call_duration: number;
  resolution_rate:   number;
  qa_avg_score:      number;
  tickets_resolved:  number;
}

export interface DashboardSummary {
  kpi:      KpiStats;
  branches: BranchStats[];
}

export interface AnalyticsFilters {
  branch_id?:   number;
  date_from?:   string;
  date_to?:     string;
  agent_id?:    number;
}
