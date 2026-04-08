import { useAnalytics } from '../hooks/useAnalytics';
import { AnalyticsDashboard } from '../../../app/components/analytics/analytics-dashboard';

/** Connects AnalyticsDashboard with live KPI data from API */
export function AnalyticsContainer() {
  const { kpi, branches, employees, isLoading, error, filters, applyFilters, exportCsv } =
    useAnalytics();

  return (
    <AnalyticsDashboard
      kpi={kpi as never}
      branches={branches as never}
      employees={employees as never}
      isLoading={isLoading}
      error={error}
      filters={filters as never}
      onFilterChange={applyFilters as never}
      onExportCsv={exportCsv}
    />
  );
}
