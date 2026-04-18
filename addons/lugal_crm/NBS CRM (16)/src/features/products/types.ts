/** POS product row from `/api/crm/pos/products` */
export interface Product {
  id: number;
  name: string;
  default_code?: string;
  foreign_name?: string;
  uom_id?: { id: number; name: string };
  list_price?: number;
  qty_available?: number;
}

/** Pricelist row from `/api/crm/pricelist/products` */
export interface PriceItem {
  id: number;
  name: string;
  foreign_name?: string;
  item_code?: string;
  category_id?: number | null;
  category_name?: string;
  uom_id?: number | null;
  uom_name?: string;
  price?: number;
  list_price?: number;
  currency?: string;
  image_url?: string;
  available_uoms?: { uom_id: number; uom_name: string; price: number }[];
  active?: boolean;
}

export type PriceListEntry = PriceItem;

export interface RequestedItem {
  id?: number;
  customer_id?: number;
  product_name?: string;
  status?: string;
  notes?: string;
}

export interface InvoicePayload {
  call_id?: number | null;
  partner_id?: number | null;
  pricelist_id?: number | null;
  invoice_type?: string;
  order_lines?: unknown[];
  exchange_rate?: number | null;
}

export interface InvoiceResult {
  id?: number;
  name?: string;
  [key: string]: unknown;
}
