import { useCallback, useEffect } from 'react';
import { useAnalyticsStore } from '../store/analyticsStore';
import { analyticsService } from '../services/analyticsService';
import type { AnalyticsFilters } from '../types';

export function useAnalytics() {
  const store = useAnalyticsStore();

  const fetchAll = useCallback(async () => {
    store.setLoading(true);
    const [kpiRes, branchRes, empRes] = await Promise.all([
      analyticsService.getKpiStats(store.filters),
      analyticsService.getBranchStats(store.filters),
      analyticsService.getEmployeeKpis(store.filters),
    ]);
    if (kpiRes.success && kpiRes.data)       store.setKpi(kpiRes.data);
    /** branch_report returns { branches: [] } */
    if (branchRes.success && branchRes.data) {
      const d = branchRes.data as Record<string, unknown>;
      store.setBranches((d['branches'] ?? d['items'] ?? []) as import('../types').BranchStats[]);
    }
    /** all_employees_kpi returns { employees: [] } or { items: [] } */
    if (empRes.success && empRes.data) {
      const d = empRes.data as Record<string, unknown>;
      store.setEmployees((d['employees'] ?? d['items'] ?? []) as import('../types').EmployeeKpi[]);
    }
    if (!kpiRes.success) store.setError(kpiRes.error ?? 'Failed to load analytics');
    else store.setLoading(false);
  }, [store.filters]);

  const applyFilters = useCallback((filters: AnalyticsFilters) => {
    store.setFilters(filters);
  }, [store]);

  const exportCsv = useCallback(async () => {
    const result = await analyticsService.exportKpiCsv(store.filters);
    if (result.success && result.data?.url) {
      window.open(result.data.url, '_blank');
    }
    return result;
  }, [store.filters]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return {
    kpi:       store.kpi,
    branches:  store.branches,
    employees: store.employees,
    filters:   store.filters,
    isLoading: store.isLoading,
    error:     store.error,
    fetchAll,
    applyFilters,
    exportCsv,
  };
}
