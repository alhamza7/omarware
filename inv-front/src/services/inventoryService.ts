import apiClient from './apiClient';
import type { ItemData, BarcodeData, AuditData } from '../app/components/admin/types';

// ── Items ─────────────────────────────────────────────────────────────────────

interface ItemsApiResponse {
  success: boolean;
  data: { items: ItemData[]; total: number; page: number; per_page: number };
}

export interface FetchItemsResult { items: ItemData[]; total: number; }

/** Fetch paginated items list */
export async function fetchItems(page = 1, perPage = 50, search = ''): Promise<FetchItemsResult> {
  const { data } = await apiClient.get<ItemsApiResponse>('/items', {
    params: { page, per_page: perPage, search: search || undefined },
  });
  return { items: data.data.items ?? [], total: data.data.total ?? 0 };
}

// ── Barcodes ──────────────────────────────────────────────────────────────────

interface BarcodesApiResponse {
  success: boolean;
  data: { barcodes: BarcodeData[]; total: number };
}

export interface FetchBarcodesResult { barcodes: BarcodeData[]; total: number; }

/** Fetch paginated barcodes list */
export async function fetchBarcodes(page = 1, perPage = 50, search = ''): Promise<FetchBarcodesResult> {
  const { data } = await apiClient.get<BarcodesApiResponse>('/barcodes', {
    params: { page, per_page: perPage, search: search || undefined },
  });
  return { barcodes: data.data.barcodes ?? [], total: data.data.total ?? 0 };
}

// ── Audits ────────────────────────────────────────────────────────────────────

interface AuditsApiResponse {
  success: boolean;
  data: { audits: AuditData[]; total: number };
}

export interface FetchAuditsResult { audits: AuditData[]; total: number; }

/** Fetch paginated audits list */
export async function fetchAudits(params: {
  page?: number;
  per_page?: number;
  search?: string;
  warehouse_id?: number;
}): Promise<FetchAuditsResult> {
  const { data } = await apiClient.get<AuditsApiResponse>('/audits', { params });
  return { audits: data.data.audits ?? [], total: data.data.total ?? 0 };
}

/** Delete a single audit */
export async function deleteAudit(id: number): Promise<void> {
  await apiClient.delete(`/audits/${id}`);
}

/** Delete all audits for a warehouse */
export async function deleteWarehouseAudits(warehouseId: number): Promise<number> {
  const { data } = await apiClient.delete<{ success: boolean; deleted: number }>(`/audits/warehouse/${warehouseId}`);
  return data.deleted ?? 0;
}

// ── Product Search ─────────────────────────────────────────────────────────────

export interface ProductBarcode {
  id: number | null;
  barcode: string;
  uom: string;
  uom_id: number | null;
  sap_uom_entry: number;
  matched: boolean;
}

export interface WarehouseStock {
  warehouse_id: number;
  warehouse: string;
  warehouse_code: string;
  qty: number;
  qty_reserved?: number;
  source: string;
}

export interface ProductDetail {
  id: number;
  code: string;
  name: string;
  foreign_name: string;
  uom: string;
  uom_id: number | null;
  category: string;
  barcodes: ProductBarcode[];
  warehouses: WarehouseStock[];
  total_qty: number;
  matched_barcode: string | null;
}

interface SearchApiResponse {
  success: boolean;
  data: { products: ProductDetail[]; count: number };
}

/**
 * Search for products by barcode, code, or name.
 * Exact barcode/code match returns 1 result; text search returns up to `limit` results.
 * Returns an empty array if nothing is found.
 */
export async function searchProduct(
  query: string,
  warehouseId?: number,
  limit = 15,
): Promise<ProductDetail[]> {
  const { data } = await apiClient.post<SearchApiResponse>('/search', {
    query,
    warehouse_id: warehouseId ?? undefined,
    limit,
  });
  return data.data.products ?? [];
}

// ── Create Audit ───────────────────────────────────────────────────────────────

export interface CreateAuditPayload {
  product_id: number;
  warehouse_id: number;
  quantity: number;
  uom_id?: number;
  barcode_used?: string;
  note?: string;
}

/**
 * Submit an inventory count entry to the audit log.
 * Requires product_id, warehouse_id, and quantity.
 */
export async function createAudit(payload: CreateAuditPayload): Promise<void> {
  await apiClient.post('/audits', payload);
}
