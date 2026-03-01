// ─── POS Bridge API Types ─────────────────────────────────────────────────────

/** Product from GET /api/crm/pos/products */
export interface ApiProduct {
  id: number;
  name: string;
  default_code: string;
  foreign_name: string;
  uom_id: { id: number; name: string };
  list_price: number;
  qty_available: number;
}

/** Full product detail from POST /api/crm/pos/product_detail */
export interface ApiProductDetail {
  product_id: number;
  product_name: string;
  product_uom_id: number;
  product_uom_name: string;
  price_unit: number;
  available_qty: number;
  default_code: string;
  foreign_name: string;
  available_uoms: { id: number; name: string; price: number }[];
  warehouses: { id: number; name: string; code: string; quantity: number }[];
}

/** Warehouse from invoice context */
export interface ApiWarehouse {
  id: number;
  name: string;
  code: string;
}

/** Pricelist from invoice context */
export interface ApiPricelist {
  id: number;
  name: string;
  currency_id: number;
}

/** Invoice type option */
export interface ApiInvoiceType {
  key: string;
  label: string;
}

/** Full response from POST /api/crm/pos/invoice_context */
export interface ApiInvoiceContext {
  pricelists: ApiPricelist[];
  default_pricelist_id: number;
  warehouses: ApiWarehouse[];
  invoice_types: ApiInvoiceType[];
  exchange_rate: number;
  currency: string;
  secondary_currency: string;
  partner_id: number | null;
  last_order: {
    id: number;
    name: string;
    date: string | null;
    amount_total: number;
    state: string;
  } | null;
}

/** Single order line sent to POST /api/crm/pos/orders/create */
export interface CreateOrderLine {
  product_id: number;
  product_uom_id: number;
  warehouse_id: number;
  quantity: number;
  unit_price: number;
  discount_percent: number;
  custom_product_name?: string;
  sequence?: number;
}

/** Payload for POST /api/crm/pos/orders/create */
export interface CreateOrderPayload {
  partner_id: number;
  pricelist_id: number;
  invoice_type: string;
  order_lines: CreateOrderLine[];
  exchange_rate?: number;
  call_id?: number;
}

/** Response data from POST /api/crm/pos/orders/create */
export interface CreatedOrder {
  order_id: number;
  order_name: string;
  state: string;
  amount_total: number;
  sale_order_name: string;
}

/** Internal state shape for InvoiceCreationContainer */
export interface PosInvoiceState {
  context: ApiInvoiceContext | null;
  products: ApiProduct[];
  isLoadingContext: boolean;
  isSearchingProducts: boolean;
  isSubmitting: boolean;
  createdOrder: CreatedOrder | null;
  error: string | null;
  partnerId: number | null;
  selectedPricelistId: number | null;
}
