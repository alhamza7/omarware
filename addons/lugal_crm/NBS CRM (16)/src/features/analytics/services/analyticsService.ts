import { apiPost } from '../../../shared/services/apiClient';
import type { ApiResult } from '../../../shared/services/apiClient';
import type { KpiStats, BranchStats, EmployeeKpi, DashboardSummary, AnalyticsFilters } from '../types';

/**
 * POST /api/crm/analytics/dashboard_stats
 * Aggregate stats for the main dashboard (customers, tickets, calls).
 */
async function getDashboardSummary(
  filters: AnalyticsFilters = {},
): Promise<ApiResult<DashboardSummary>> {
  return apiPost('/api/crm/analytics/dashboard_stats', {
    branch_id:  filters.branch_id  ?? null,
    date_from:  filters.date_from  ?? null,
    date_to:    filters.date_to    ?? null,
  });
}

/**
 * POST /api/crm/analytics/dashboard_stats
 * Reuse the same endpoint — data includes all KPI fields.
 */
async function getKpiStats(filters: AnalyticsFilters = {}): Promise<ApiResult<KpiStats>> {
  return apiPost('/api/crm/analytics/dashboard_stats', {
    branch_id: filters.branch_id ?? null,
    date_from: filters.date_from ?? null,
    date_to:   filters.date_to   ?? null,
  });
}

/**
 * POST /api/crm/analytics/branch_report
 * Per-branch performance breakdown.
 */
async function getBranchStats(filters: AnalyticsFilters = {}): Promise<ApiResult<BranchStats[]>> {
  return apiPost('/api/crm/analytics/branch_report', {
    date_from: filters.date_from ?? null,
    date_to:   filters.date_to   ?? null,
  });
}

/**
 * POST /api/crm/analytics/all_employees_kpi
 * KPI data per agent/employee.
 */
async function getEmployeeKpis(filters: AnalyticsFilters = {}): Promise<ApiResult<EmployeeKpi[]>> {
  return apiPost('/api/crm/analytics/all_employees_kpi', {
    branch_id: filters.branch_id ?? null,
    date_from: filters.date_from ?? null,
    date_to:   filters.date_to   ?? null,
  });
}

/**
 * POST /api/crm/analytics/employee_kpi
 * KPI for a single employee.
 */
async function getSingleEmployeeKpi(
  agentId: number,
  filters: AnalyticsFilters = {},
): Promise<ApiResult<EmployeeKpi>> {
  return apiPost('/api/crm/analytics/employee_kpi', {
    employee_id: agentId,
    date_from:   filters.date_from ?? null,
    date_to:     filters.date_to   ?? null,
  });
}

/**
 * POST /api/crm/analytics/supervisor_dashboard
 * Supervisor-level metrics per branch.
 */
async function getSupervisorDashboard(branchId?: number): Promise<ApiResult<unknown>> {
  return apiPost('/api/crm/analytics/supervisor_dashboard', {
    branch_id: branchId ?? null,
  });
}

/**
 * POST /api/crm/analytics/export_kpi
 * Returns a CSV download URL for KPI data.
 */
async function exportKpiCsv(filters: AnalyticsFilters = {}): Promise<ApiResult<{ url: string }>> {
  return apiPost('/api/crm/analytics/export_kpi', {
    branch_id: filters.branch_id ?? null,
    date_from: filters.date_from ?? null,
    date_to:   filters.date_to   ?? null,
  });
}

/**
 * POST /api/crm/analytics/channel_report
 * Channel performance breakdown (WhatsApp, Instagram, etc.).
 */
async function getChannelReport(filters: AnalyticsFilters = {}): Promise<ApiResult<unknown>> {
  return apiPost('/api/crm/analytics/channel_report', {
    branch_id: filters.branch_id ?? null,
    date_from: filters.date_from ?? null,
    date_to:   filters.date_to   ?? null,
  });
}

/**
 * POST /api/crm/analytics/ai_vs_human
 * AI vs human interaction breakdown for analytics page.
 */
async function getAiVsHuman(filters: AnalyticsFilters = {}): Promise<ApiResult<unknown>> {
  return apiPost('/api/crm/analytics/ai_vs_human', {
    branch_id: filters.branch_id ?? null,
    date_from: filters.date_from ?? null,
    date_to:   filters.date_to   ?? null,
  });
}

export const analyticsService = {
  getDashboardSummary,
  getKpiStats,
  getBranchStats,
  getEmployeeKpis,
  getSingleEmployeeKpi,
  getSupervisorDashboard,
  exportKpiCsv,
  getChannelReport,
  getAiVsHuman,
};
