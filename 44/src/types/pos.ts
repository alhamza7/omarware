// ============================================================
// POS Perfume — TypeScript Types
// ============================================================

// ─── Shared API wrapper ──────────────────────────────────────
export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error?: string;
}

export interface PaginatedResponse<T> {
  total:  number;
  offset: number;
  limit:  number;
  items:  T[];
}

// ─── Setup ──────────────────────────────────────────────────
export interface PosSetup {
  pricelists:           Pricelist[];
  default_pricelist_id: number;
  warehouses:           Warehouse[];
  users:                PosUser[];
  invoice_types:        InvoiceType[];
  exchange_rate:        number;
  currency:             string;            // "USD"
  secondary_currency:   string;            // "IQD"
}

export interface Pricelist  { id: number; name: string; currency_id: number; }
export interface Warehouse  { id: number; name: string; code: string; }
export interface PosUser    { id: number; name: string; }
export interface InvoiceType { key: string; label: string; }

// ─── Customer ───────────────────────────────────────────────
export interface Customer {
  id:           number;
  name:         string;
  ref:          string;
  phone:        string;
  mobile:       string;
  email:        string;
  street:       string;
  city:         string;
  country_id:   { id: number; name: string } | null;
  pricelist_id: { id: number; name: string } | null;
}

export interface CreateCustomerBody {
  name:        string;
  phone?:      string;
  mobile?:     string;
  email?:      string;
  street?:     string;
  city?:       string;
  ref?:        string;
  country_id?: number;
}

// ─── Product ────────────────────────────────────────────────
export interface Product {
  id:            number;
  name:          string;
  default_code:  string;
  foreign_name:  string;
  uom_id:        { id: number; name: string };
  list_price:    number;
  qty_available: number;
  color_class:   string;
  badge_text:    string;
  active:        boolean;
  sale_ok:       boolean;
  categ_id:      { id: number; name: string } | null;
  available_uoms?: ProductUom[];
  warehouses?:     ProductWarehouse[];
}

export interface ProductUom {
  id:    number;
  name:  string;
  price: number;
}

export interface ProductWarehouse {
  id:       number;
  name:     string;
  code:     string;
  quantity: number;
}

export interface ProductDataBody {
  product_id:    number;
  pricelist_id?: number | null;
  uom_id?:       number | null;
  warehouse_id?: number | null;
}

export interface UomPriceBody {
  product_id:   number;
  pricelist_id: number;
  uom_id:       number;
}

// ─── Order ──────────────────────────────────────────────────
export type OrderState      = 'draft' | 'quotation' | 'sale' | 'done' | 'cancel';
export type InvoiceTypeKey  = '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8';

export interface Order {
  id:               number;
  name:             string;
  date:             string;
  state:            OrderState;
  user_id:          { id: number; name: string } | null;
  partner_id:       { id: number; name: string; phone: string; mobile: string; email: string } | null;
  pricelist_id:     { id: number; name: string } | null;
  currency_id:      { id: number; name: string } | null;
  exchange_rate:    number;
  amount_subtotal:  number;
  amount_discount:  number;
  amount_tax:       number;
  amount_total:     number;
  amount_total_iqd: number;
  invoice_type:     InvoiceTypeKey | '';
  note:             string;
  sale_order_id:    { id: number; name: string; state: string } | null;
  sap_doc_num:      string;
  sap_doc_entry:    number;
  sap_synced:       boolean;
  order_lines:      OrderLine[];
}

export interface OrderSummary {
  id:               number;
  name:             string;
  date:             string;
  state:            OrderState;
  partner_name:     string;
  amount_total:     number;
  amount_total_iqd: number;
  sap_synced:       boolean;
  sap_doc_num:      string;
}

export interface CreateOrderBody {
  partner_id?:    number;
  pricelist_id?:  number;
  invoice_type?:  InvoiceTypeKey;
  note?:          string;
  exchange_rate?: number;
  user_id?:       number;
  order_lines?:   CreateOrderLineBody[];
}

export interface UpdateOrderBody {
  partner_id?:    number;
  pricelist_id?:  number;
  note?:          string;
  invoice_type?:  InvoiceTypeKey;
  exchange_rate?: number;
  user_id?:       number;
}

// ─── Order Line ─────────────────────────────────────────────
export interface OrderLine {
  id:                   number;
  sequence:             number;
  product_id:           { id: number; name: string; default_code: string; foreign_name: string } | null;
  product_uom_id:       { id: number; name: string } | null;
  warehouse_id:         { id: number; name: string; code: string } | null;
  location_id:          { id: number; name: string } | null;
  quantity:             number;
  unit_price:           number;
  discount_percent:     number;
  price_after_discount: number;
  line_subtotal:        number;
  discount_amount:      number;
  line_total:           number;
  available_qty:        number;
  custom_product_name:  string;
}

export interface CreateOrderLineBody {
  product_id:           number;
  warehouse_id:         number;
  product_uom_id?:      number;
  quantity?:            number;
  unit_price?:          number;
  discount_percent?:    number;
  custom_product_name?: string;
  location_id?:         number;
  sequence?:            number;
}

export interface UpdateOrderLineBody {
  product_id?:          number;
  product_uom_id?:      number;
  warehouse_id?:        number;
  location_id?:         number | null;
  quantity?:            number;
  unit_price?:          number;
  discount_percent?:    number;
  custom_product_name?: string | null;
  sequence?:            number;
}

// ─── Action results ──────────────────────────────────────────
export interface ConfirmResult {
  id:            number;
  name:          string;
  state:         OrderState;
  sale_order_id: { id: number; name: string; state: string } | null;
  sap_synced:    boolean;
  sap_doc_num:   string;
  sap_doc_entry: number;
}

export interface SapSyncResult {
  sap_synced:        boolean;
  sap_doc_num:       string;
  sap_doc_entry:     number;
  sap_error_message: string;
}

export interface ExchangeRateResult {
  id:               number;
  exchange_rate:    number;
  amount_total_iqd: number;
}
