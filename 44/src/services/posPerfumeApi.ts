// ============================================================
// POS Perfume API Service — v1
// ============================================================
// Requests go through Vite proxy → forwarded to Odoo :8070
// Proxy config is in vite.config.ts  (server.proxy['/api'])
// ============================================================

import type {
  ApiResponse,
  PaginatedResponse,
  PosSetup,
  Customer,
  CreateCustomerBody,
  Product,
  ProductDataBody,
  UomPriceBody,
  Order,
  OrderSummary,
  OrderLine,
  OrderState,
  CreateOrderBody,
  UpdateOrderBody,
  CreateOrderLineBody,
  UpdateOrderLineBody,
  ConfirmResult,
  SapSyncResult,
  ExchangeRateResult,
  Pricelist,
  Warehouse,
  InvoiceTypeKey,
} from '../types/pos';

// ── Config ────────────────────────────────────────────────────
// BASE_URL is relative → Vite proxy forwards to Odoo :8070
// In production, set VITE_ODOO_URL to your server domain
const BASE_URL = (import.meta.env.VITE_ODOO_URL ?? '') + '/api/pos_perfume/v1';
const API_KEY  = import.meta.env.VITE_API_KEY ?? '';

// ── Core fetch helper ─────────────────────────────────────────
async function call<T>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  body?: unknown,
): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = {
    Authorization: `Bearer ${API_KEY}`,
  };
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  // For non-JSON responses (e.g. PDF), return a generic error wrapper
  const contentType = res.headers.get('content-type') ?? '';
  if (!contentType.includes('application/json')) {
    if (!res.ok) {
      return { success: false, message: '', data: null as T, error: `HTTP ${res.status}` };
    }
    return { success: true, message: 'OK', data: null as T };
  }

  const json = (await res.json()) as ApiResponse<T>;
  if (!json.success) {
    console.error(`[POS API] ${method} ${endpoint} →`, json.error);
  }
  return json;
}

// ── PDF helper (returns Blob) ─────────────────────────────────
async function callBlob(endpoint: string): Promise<Blob | null> {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    headers: { Authorization: `Bearer ${API_KEY}` },
  });
  if (!res.ok) return null;
  return res.blob();
}

// ── Query string builder ──────────────────────────────────────
function qs(params: Record<string, string | number | boolean | undefined>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '') q.set(k, String(v));
  }
  const str = q.toString();
  return str ? `?${str}` : '';
}

// ============================================================
// 1. SESSION
// ============================================================

/** Get current authenticated user info */
export const getSession = () =>
  call<{
    user_id: number; user_name: string; user_login: string;
    company_id: number; company_name: string;
    exchange_rate: number;
  }>('/session');

// ============================================================
// 2. SETUP  — call once on POS boot
// ============================================================

/** All data needed to start the POS: pricelists, warehouses, invoice types, exchange rate */
export const getSetup = () => call<PosSetup>('/setup');

// ============================================================
// 3. SETTINGS
// ============================================================

export const getSettings = () =>
  call<{ exchange_rate: number }>('/settings');

export const updateSettings = (exchange_rate: number) =>
  call<{ exchange_rate: number }>('/settings', 'PUT', { exchange_rate });

// ============================================================
// 4. CUSTOMERS
// ============================================================

export const listCustomers = (params?: {
  query?: string; limit?: number; offset?: number;
}) =>
  call<PaginatedResponse<Customer>>(
    `/customers${qs({ ...params })}`
  );

export const getCustomer = (id: number) =>
  call<Customer>(`/customers/${id}`);

export const createCustomer = (body: CreateCustomerBody) =>
  call<Customer>('/customers', 'POST', body);

export const updateCustomer = (id: number, body: Partial<CreateCustomerBody>) =>
  call<Customer>(`/customers/${id}`, 'PUT', body);

// ============================================================
// 5. PRODUCTS
// ============================================================

export const listProducts = (params?: {
  query?: string; limit?: number; offset?: number; pricelist_id?: number;
}) =>
  call<PaginatedResponse<Product>>(
    `/products${qs({ ...params })}`
  );

/** Single product with UoMs + warehouse stock */
export const getProduct = (id: number, pricelist_id?: number) =>
  call<Product>(`/products/${id}${qs({ pricelist_id })}`);

/** Full product data: all UoMs + prices + warehouses — use when product is selected in POS */
export const getProductData = (body: ProductDataBody) =>
  call<Product & { available_uoms: { id: number; name: string; price: number }[]; warehouses: { id: number; name: string; code: string; quantity: number }[] }>(
    '/products/data', 'POST', body
  );

/** Get updated price when the user changes the UoM */
export const getUomPrice = (body: UomPriceBody) =>
  call<{ price_unit: number }>('/products/uom_price', 'POST', body);

// ============================================================
// 6. ORDERS — list & create
// ============================================================

export const listOrders = (params?: {
  query?: string; state?: OrderState; partner_id?: number;
  date_from?: string; date_to?: string;
  limit?: number; offset?: number;
}) =>
  call<PaginatedResponse<OrderSummary>>(
    `/orders${qs({ ...params })}`
  );

export const createOrder = (body: CreateOrderBody) =>
  call<Order>('/orders', 'POST', body);

// ============================================================
// 7. ORDERS — get / update / delete
// ============================================================

/** Full order details with all lines */
export const getOrder = (id: number) =>
  call<Order>(`/orders/${id}`);

/** Update order header (partner, pricelist, note, invoice_type, exchange_rate) */
export const updateOrder = (id: number, body: UpdateOrderBody) =>
  call<Order>(`/orders/${id}`, 'PUT', body);

/** Soft-cancel: sets state → 'cancel' */
export const deleteOrder = (id: number) =>
  call<{ id: number; state: 'cancel' }>(`/orders/${id}`, 'DELETE');

// ============================================================
// 8. ORDER LINES
// ============================================================

export const addOrderLine = (orderId: number, body: CreateOrderLineBody) =>
  call<OrderLine>(`/orders/${orderId}/lines`, 'POST', body);

export const updateOrderLine = (orderId: number, lineId: number, body: UpdateOrderLineBody) =>
  call<OrderLine>(`/orders/${orderId}/lines/${lineId}`, 'PUT', body);

export const deleteOrderLine = (orderId: number, lineId: number) =>
  call<{ deleted: boolean; line_id: number }>(
    `/orders/${orderId}/lines/${lineId}`, 'DELETE'
  );

// ============================================================
// 9. ORDER ACTIONS
// ============================================================

/** Confirm order → creates sale.order + SAP sync */
export const confirmOrder = (id: number) =>
  call<ConfirmResult>(`/orders/${id}/confirm`, 'POST');

/** Set order state to 'quotation' */
export const quotationOrder = (id: number) =>
  call<{ id: number; state: OrderState }>(`/orders/${id}/quotation`, 'POST');

/** Cancel order → state = 'cancel' */
export const cancelOrder = (id: number) =>
  call<{ id: number; state: 'cancel' }>(`/orders/${id}/cancel`, 'POST');

/** Reset cancelled order back to 'draft' */
export const draftOrder = (id: number) =>
  call<{ id: number; state: OrderState }>(`/orders/${id}/draft`, 'POST');

// ============================================================
// 10. WHATSAPP
// ============================================================

export const sendWhatsApp = (id: number) =>
  call<{ message_id: number }>(`/orders/${id}/send_whatsapp`, 'POST');

export const sendWhatsAppImage = (id: number) =>
  call<{ message_id: number }>(`/orders/${id}/send_whatsapp_image`, 'POST');

// ============================================================
// 11. PDF REPORT
// ============================================================

/**
 * Download order PDF as a Blob.
 * Example:
 *   const blob = await downloadOrderReport(orderId);
 *   const url  = URL.createObjectURL(blob);
 *   window.open(url);
 */
export const downloadOrderReport = (id: number) =>
  callBlob(`/orders/${id}/report`);

/**
 * Returns a URL string you can use in an <a href> or window.open.
 * Note: The Authorization header is NOT sent with window.open.
 * Use downloadOrderReport() for proper auth.
 */
export const orderReportUrl = (id: number, download = true) =>
  `${BASE_URL}/orders/${id}/report?download=${download}`;

// ============================================================
// 12. SAP SYNC
// ============================================================

/** Force re-sync the linked sale order to SAP */
export const syncSap = (id: number) =>
  call<SapSyncResult>(`/orders/${id}/sync_sap`, 'POST');

// ============================================================
// 13. EXCHANGE RATE ON ORDER
// ============================================================

/**
 * Update exchange rate on a specific order.
 * Pass rate = undefined to use the current default from settings.
 */
export const updateOrderExchangeRate = (id: number, rate?: number) =>
  call<ExchangeRateResult>(
    `/orders/${id}/exchange_rate`, 'PUT',
    rate !== undefined ? { exchange_rate: rate } : {}
  );

// ============================================================
// 14. CONVENIENCE LISTS
// ============================================================

export const listPricelists = () =>
  call<{ items: (Pricelist & { currency_name: string })[]; total: number }>(
    '/pricelists'
  );

export const listWarehouses = () =>
  call<{ items: Warehouse[]; total: number }>('/warehouses');

// ── Default export (grouped) ──────────────────────────────────
const posPerfumeApi = {
  // Session & Setup
  getSession,
  getSetup,
  // Settings
  getSettings,
  updateSettings,
  // Customers
  listCustomers,
  getCustomer,
  createCustomer,
  updateCustomer,
  // Products
  listProducts,
  getProduct,
  getProductData,
  getUomPrice,
  // Orders
  listOrders,
  createOrder,
  getOrder,
  updateOrder,
  deleteOrder,
  // Order Lines
  addOrderLine,
  updateOrderLine,
  deleteOrderLine,
  // Order Actions
  confirmOrder,
  quotationOrder,
  cancelOrder,
  draftOrder,
  // WhatsApp
  sendWhatsApp,
  sendWhatsAppImage,
  // PDF
  downloadOrderReport,
  orderReportUrl,
  // SAP
  syncSap,
  // Exchange Rate
  updateOrderExchangeRate,
  // Lists
  listPricelists,
  listWarehouses,
};

export default posPerfumeApi;
