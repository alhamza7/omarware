import apiClient from './apiClient';

export interface Warehouse {
  id: number;
  name: string;
  code?: string;
  short_name?: string;
}

/** Fetch all available warehouses */
export async function fetchWarehouses(): Promise<Warehouse[]> {
  const res = await fetch('/api/inventory/v1/warehouses');
  if (!res.ok) return [];
  const json = (await res.json()) as { success: boolean; data: Warehouse[] };
  return json.success ? json.data : [];
}

/** Fetch warehouses using authenticated apiClient */
export async function fetchWarehousesAuth(): Promise<Warehouse[]> {
  try {
    const { data } = await apiClient.get<{ success: boolean; data: Warehouse[] }>('/warehouses');
    return data.success ? data.data : [];
  } catch {
    return [];
  }
}
