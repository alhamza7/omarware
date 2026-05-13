import { apiPost } from '../../../shared/services/apiClient';
import type { ApiResult } from '../../../shared/services/apiClient';
import type { PurchaseOrder, Vendor, Container, CreatePoPayload } from '../types';
import type { PaginatedResponse } from '../../../shared/types';

/**
 * POST /api/crm/supply/po/list
 * List purchase orders with optional status filter.
 */
async function listPurchaseOrders(params: {
  page?: number;
  status?: string;
  customer_id?: number;
  branch_id?: number;
  vendor_id?: number;
}): Promise<ApiResult<PaginatedResponse<PurchaseOrder>>> {
  return apiPost('/api/crm/supply/po/list', {
    page:        params.page      ?? 1,
    per_page:    20,
    status:      params.status    ?? null,
    vendor_id:   params.vendor_id ?? null,
  });
}

/** POST /api/crm/supply/po/:id — get single PO with lines */
async function getPurchaseOrder(id: number): Promise<ApiResult<PurchaseOrder>> {
  return apiPost(`/api/crm/supply/po/${id}`, {});
}

/** POST /api/crm/supply/po/create */
async function createPurchaseOrder(payload: CreatePoPayload): Promise<ApiResult<PurchaseOrder>> {
  return apiPost('/api/crm/supply/po/create', payload as Record<string, unknown>);
}

/**
 * POST /api/crm/supply/po/:id/update
 * Update PO — pass { status: 'confirmed' } to confirm it.
 */
async function confirmPurchaseOrder(id: number): Promise<ApiResult<PurchaseOrder>> {
  return apiPost(`/api/crm/supply/po/${id}/update`, { status: 'confirmed' });
}

/**
 * POST /api/crm/supply/po/:id/update
 * Cancel a purchase order.
 */
async function cancelPurchaseOrder(id: number): Promise<ApiResult<PurchaseOrder>> {
  return apiPost(`/api/crm/supply/po/${id}/update`, { status: 'cancelled' });
}

/** POST /api/crm/supply/po/:id/lines — get PO lines */
async function getPoLines(id: number): Promise<ApiResult<unknown[]>> {
  return apiPost(`/api/crm/supply/po/${id}/lines`, {});
}

/** POST /api/crm/supply/po/:id/lines/add */
async function addPoLine(
  poId: number,
  payload: { product_name: string; quantity: number; unit_price: number },
): Promise<ApiResult<unknown>> {
  return apiPost(`/api/crm/supply/po/${poId}/lines/add`, payload as Record<string, unknown>);
}

/** POST /api/crm/supply/po/suggested — AI-suggested reorder items */
async function getSuggestedOrders(): Promise<ApiResult<unknown[]>> {
  return apiPost('/api/crm/supply/po/suggested', {});
}

/**
 * POST /api/crm/supply/vendors/list
 * List all vendors (from lugal_crm supply module).
 */
async function listVendors(): Promise<ApiResult<Vendor[]>> {
  return apiPost('/api/crm/supply/vendors/list', {});
}

/** POST /api/crm/supply/vendors/create */
async function createVendor(payload: Partial<Vendor>): Promise<ApiResult<Vendor>> {
  return apiPost('/api/crm/supply/vendors/create', payload as Record<string, unknown>);
}

/** POST /api/crm/supply/vendors/:id — get single vendor */
async function getVendor(id: number): Promise<ApiResult<Vendor>> {
  return apiPost(`/api/crm/supply/vendors/${id}`, {});
}

/**
 * POST /api/crm/supply/containers/list
 * List shipping containers with optional status filter.
 */
async function listContainers(params: { status?: string } = {}): Promise<ApiResult<PaginatedResponse<Container>>> {
  return apiPost('/api/crm/supply/containers/list', {
    status:   params.status ?? null,
    per_page: 50,
  });
}

/** POST /api/crm/supply/containers/create */
async function createContainer(payload: Partial<Container>): Promise<ApiResult<Container>> {
  return apiPost('/api/crm/supply/containers/create', payload as Record<string, unknown>);
}

/** POST /api/crm/supply/containers/:id/clearance_delivered */
async function markContainerDelivered(id: number): Promise<ApiResult<Container>> {
  return apiPost(`/api/crm/supply/containers/${id}/clearance_delivered`, {});
}

/** POST /api/crm/supply/po/:id/packing-list/share — plain text for Web Share / clipboard */
export interface PackingListShareData {
  title: string;
  text: string;
  url?: string;
}

async function getPackingListShare(poId: number): Promise<ApiResult<PackingListShareData>> {
  return apiPost(`/api/crm/supply/po/${poId}/packing-list/share`, {});
}

/** POST /api/crm/supply/po/:id/packing-list/pdf — base64 PDF for client download */
export interface PackingListPdfData {
  filename: string;
  pdf_base64: string;
  mimetype: string;
}

async function getPackingListPdf(poId: number): Promise<ApiResult<PackingListPdfData>> {
  return apiPost(`/api/crm/supply/po/${poId}/packing-list/pdf`, {});
}

export const supplyService = {
  listPurchaseOrders,
  getPurchaseOrder,
  createPurchaseOrder,
  confirmPurchaseOrder,
  cancelPurchaseOrder,
  getPoLines,
  addPoLine,
  getSuggestedOrders,
  listVendors,
  createVendor,
  getVendor,
  listContainers,
  createContainer,
  markContainerDelivered,
  getPackingListShare,
  getPackingListPdf,
};
