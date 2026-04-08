import { apiPost } from '../../../shared/services/apiClient';
import type { ApiResult } from '../../../shared/services/apiClient';
import type { Product, PriceItem, RequestedItem, InvoicePayload, InvoiceResult } from '../types';

/**
 * POST /api/crm/pos/products
 * Fetch POS products with optional search query.
 */
async function listProducts(params: {
  query?: string;
  pricelist_id?: number;
  limit?: number;
} = {}): Promise<ApiResult<Product[]>> {
  return apiPost('/api/crm/pos/products', {
    query:        params.query        ?? '',
    pricelist_id: params.pricelist_id ?? null,
    limit:        params.limit        ?? 80,
  });
}

/**
 * POST /api/crm/pos/product_detail
 * Get detailed info for a single product (all UOMs, prices).
 */
async function getProductDetail(productId: number, pricelistId?: number): Promise<ApiResult<Product>> {
  return apiPost('/api/crm/pos/product_detail', {
    product_id:   productId,
    pricelist_id: pricelistId ?? null,
  });
}

/**
 * POST /api/crm/pos/uom_price
 * Get price for a specific product + UOM + pricelist combination.
 */
async function getUomPrice(
  productId: number,
  pricelistId: number,
  uomId: number,
): Promise<ApiResult<{ unit_price: number; uom_name: string }>> {
  return apiPost('/api/crm/pos/uom_price', {
    product_id:   productId,
    pricelist_id: pricelistId,
    uom_id:       uomId,
  });
}

/**
 * POST /api/crm/pricelist/products
 * Fetch pricelist-specific product list.
 */
async function getPriceList(
  branchId?: number,
  pricelistId?: number,
): Promise<ApiResult<PriceItem[]>> {
  return apiPost('/api/crm/pricelist/products', {
    branch_id:    branchId    ?? null,
    pricelist_id: pricelistId ?? null,
  });
}

/** POST /api/crm/pricelist/pricelists — get available pricelists */
async function listPricelists(): Promise<ApiResult<unknown[]>> {
  return apiPost('/api/crm/pricelist/pricelists', {});
}

/** POST /api/crm/pricelist/categories — get product categories */
async function listCategories(): Promise<ApiResult<unknown[]>> {
  return apiPost('/api/crm/pricelist/categories', {});
}

/**
 * POST /api/crm/pos/orders/create
 * Create an invoice (order) — called from the call dialog.
 */
async function createInvoice(payload: InvoicePayload): Promise<ApiResult<InvoiceResult>> {
  return apiPost('/api/crm/pos/orders/create', {
    call_id:       payload.call_id      ?? null,
    partner_id:    payload.partner_id   ?? null,
    pricelist_id:  payload.pricelist_id ?? null,
    invoice_type:  payload.invoice_type ?? '1',
    order_lines:   payload.order_lines  ?? [],
    exchange_rate: payload.exchange_rate ?? null,
  });
}

/**
 * POST /api/crm/pos/invoice_context
 * Get context for creating an invoice (customer + call info).
 */
async function getInvoiceContext(callId?: number, customerId?: number): Promise<ApiResult<unknown>> {
  return apiPost('/api/crm/pos/invoice_context', {
    call_id:     callId     ?? null,
    customer_id: customerId ?? null,
  });
}

/**
 * POST /api/crm/pricelist/requested_items
 * Get price-requested items list.
 */
async function listRequestedItems(): Promise<ApiResult<RequestedItem[]>> {
  return apiPost('/api/crm/pricelist/requested_items', {});
}

/**
 * POST /api/crm/pricelist/requested_items/create
 * Create a new price request for an item.
 */
async function createRequestedItem(payload: Partial<RequestedItem>): Promise<ApiResult<RequestedItem>> {
  return apiPost('/api/crm/pricelist/requested_items/create', payload as Record<string, unknown>);
}

export const productService = {
  listProducts,
  getProductDetail,
  getUomPrice,
  getPriceList,
  listPricelists,
  listCategories,
  createInvoice,
  getInvoiceContext,
  listRequestedItems,
  createRequestedItem,
};
