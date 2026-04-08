import { create } from 'zustand';
import type { KpiStats, BranchStats, EmployeeKpi, AnalyticsFilters } from '../types';

interface AnalyticsStore {
  kpi:       KpiStats | null;
  branches:  BranchStats[];
  employees: EmployeeKpi[];
  filters:   AnalyticsFilters;
  isLoading: boolean;
  error:     string | null;

  setKpi:       (kpi: KpiStats) => void;
  setBranches:  (branches: BranchStats[]) => void;
  setEmployees: (employees: EmployeeKpi[]) => void;
  setFilters:   (filters: AnalyticsFilters) => void;
  setLoading:   (loading: boolean) => void;
  setError:     (error: string | null) => void;
}

export const useAnalyticsStore = create<AnalyticsStore>((set) => ({
  kpi:       null,
  branches:  [],
  employees: [],
  filters:   {},
  isLoading: false,
  error:     null,

  setKpi:       (kpi) => set({ kpi }),
  setBranches:  (branches) => set({ branches }),
  setEmployees: (employees) => set({ employees }),
  setFilters:   (filters) => set({ filters }),
  setLoading:   (isLoading) => set({ isLoading }),
  setError:     (error) => set({ error, isLoading: false }),
}));
