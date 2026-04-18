import { apiPost } from '../../../shared/services/apiClient';
import type { ApiResult } from '../../../shared/services/apiClient';
import type { Product, PriceItem, RequestedItem, InvoicePayload, InvoiceResult } from '../types';

export type { Product, PriceItem, PriceListEntry, RequestedItem, InvoicePayload, InvoiceResult } from '../types';

export type CreateInvoicePayload = InvoicePayload;

/**
 * POST /api/crm/pos/products
 * Fetch POS products. ``search`` is sent as ``search`` + ``query`` so Odoo accepts either.
 */
async function listProducts(params: {
  query?: string;
  search?: string;
  pricelist_id?: number;
  /** Legacy offset pagination */
  limit?: number;
  offset?: number;
  page?: number;
  per_page?: number;
  fetch_all?: boolean;
  category_id?: number | null;
  include_inactive?: boolean;
  sale_ok?: boolean;
} = {}): Promise<ApiResult<{ items: Product[]; total: number; returned?: number }>> {
  const searchText = (params.search ?? params.query ?? '').trim();
  const body: Record<string, unknown> = {
    search: searchText,
    query: searchText,
    pricelist_id: params.pricelist_id ?? null,
    category_id: params.category_id ?? null,
    include_inactive: params.include_inactive ?? false,
    sale_ok: params.sale_ok ?? true,
  };
  if (params.fetch_all) {
    body.fetch_all = true;
    body.limit = 0;
  } else if (params.page != null || params.per_page != null) {
    body.fetch_all = false;
    body.page = params.page ?? 1;
    body.per_page = params.per_page ?? 80;
  } else {
    body.fetch_all = false;
    body.limit = params.limit ?? 80;
    body.offset = params.offset ?? 0;
  }
  return apiPost('/api/crm/pos/products', body);
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
 * Fetch pricelist-specific product list (with optional server-side filters).
 * Use ``fetch_all: true`` (default in ``useProducts``) to load the full catalog (server-capped).
 */
async function getPriceList(params: {
  branchId?: number;
  pricelistId?: number;
  search?: string;
  query?: string;
  categoryId?: number | null;
  categoryIds?: number[];
  page?: number;
  perPage?: number;
  fetchAll?: boolean;
  uomId?: number | null;
  newReleasesOnly?: boolean;
  newWithinDays?: number;
  discountOnly?: boolean;
  itemCodes?: string[];
  defaultCodePrefix?: string;
  productIds?: number[];
  includeInactive?: boolean;
  saleOk?: boolean;
} = {}): Promise<
  ApiResult<{
    items: PriceItem[];
    total: number;
    page?: number;
    per_page?: number;
    returned?: number;
  }>
> {
  const text = (params.search ?? params.query ?? '').trim();
  const fetchAll = params.fetchAll !== false;
  return apiPost('/api/crm/pricelist/products', {
    branch_id: params.branchId ?? null,
    pricelist_id: params.pricelistId ?? null,
    search: text || null,
    query: text || null,
    category_id: params.categoryId ?? null,
    category_ids: params.categoryIds?.length ? params.categoryIds : null,
    page: params.page ?? 1,
    per_page: fetchAll ? 0 : (params.perPage ?? 50),
    fetch_all: fetchAll,
    uom_id: params.uomId ?? null,
    new_releases_only: params.newReleasesOnly ?? false,
    new_within_days: params.newWithinDays ?? 60,
    discount_only: params.discountOnly ?? false,
    item_codes: params.itemCodes?.length ? params.itemCodes : null,
    default_code_prefix: params.defaultCodePrefix ?? null,
    product_ids: params.productIds?.length ? params.productIds : null,
    include_inactive: params.includeInactive ?? false,
    sale_ok: params.saleOk !== false,
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

async function createInvoiceFromCall(callId: number, payload: CreateInvoicePayload): Promise<ApiResult<InvoiceResult>> {
  return createInvoice({ ...payload, call_id: callId });
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
  createInvoiceFromCall,
  getInvoiceContext,
  listRequestedItems,
  createRequestedItem,
};
