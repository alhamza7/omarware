import apiClient from './apiClient';

export interface ItemStats {
  total_items: number;
  total_barcodes: number;
  total_audits: number;
  uom_count: number;
  uom_distribution: { name: string; items: string; barcodes: string }[];
}

/** Fetch system stats including UoM distribution (single endpoint) */
export async function fetchStats(): Promise<ItemStats | null> {
  try {
    const { data } = await apiClient.get<{ success: boolean; data: ItemStats }>('/items/stats');
    return data.success ? data.data : null;
  } catch {
    return null;
  }
}

/** Fetch UoM distribution stats (uses stats endpoint, returns uom_distribution) */
export async function fetchUomStats(): Promise<{ name: string; items: string; barcodes: string }[]> {
  const stats = await fetchStats();
  return stats?.uom_distribution ?? [];
}
