// ============================================================
// Supply Chain — TypeScript Types
// ============================================================

// ─── JSON-RPC wrapper ───────────────────────────────────────
export interface JrpcResult<T> {
  success: boolean;
  data:    T;
  error?:  string;
  code?:   number;
  message?: string;
}

// ─── Auth ────────────────────────────────────────────────────
export interface AuthResult {
  access_token:  string;
  refresh_token: string;
  user_id:       number;
  name:          string;
}

// ─── Vendor / Contact ────────────────────────────────────────
export interface Vendor {
  id:           number;
  name:         string;
  name_ar:      string;
  contact_type: 'customer' | 'vendor' | 'both';
  phone:        string;
  email:        string;
  division:     string;
  city:         string;
  country_name: string;
}

export interface VendorListData {
  items:    Vendor[];
  total:    number;
  page:     number;
  per_page: number;
}

// ─── PO Line ─────────────────────────────────────────────────
export interface PoLine {
  id:                  number;
  sequence:            number;
  product_name:        string;
  item_code:           string;
  uom:                 string;
  quantity:            number;
  unit_price:          number;
  total_price:         number;
  currency_id:         number | null;
  currency_name:       string;
  last_purchase_price: number;
  last_purchase_date:  string | null;
  min_qty:             number;
  max_qty:             number;
}

export interface PoLineInput {
  product_name?: string;
  item_code?:    string;
  uom?:          string;
  quantity:      number;
  unit_price:    number;
  min_qty?:      number;
  max_qty?:      number;
  currency_id?:  number;
}

// ─── Purchase Order ──────────────────────────────────────────
export type PoStatus = 'draft' | 'confirmed' | 'shipped' | 'received' | 'cancelled';

export interface Po {
  id:                    number;
  name:                  string;
  vendor_customer_id:    number | null;
  vendor_customer_name:  string;
  vendor_customer_phone: string;
  vendor_id:             number | null;
  vendor_name:           string;
  division:              'europe' | 'china' | '';
  currency_id:           number | null;
  currency_name:         string;
  container_id:          number | null;
  container_name:        string;
  branch_id:             number | null;
  branch_name:           string;
  status:                PoStatus;
  status_label:          string;
  is_suggested:          boolean;
  line_count:            number;
  total_amount:          number;
  created_by_id:         number | null;
  created_by_name:       string;
  created_at:            string;
  updated_at:            string;
  lines:                 PoLine[];
}

export interface PoListData {
  items:    Po[];
  total:    number;
  page:     number;
  per_page: number;
}

// ─── Create / Filter forms ───────────────────────────────────
export interface PoCreateInput {
  name:               string;
  vendor_customer_id: number | null;
  division?:          'europe' | 'china' | '';
  currency_id?:       number;
  container_id?:      number;
  branch_id?:         number;
  lines:              PoLineInput[];
}

export interface PoListFilter {
  page?:               number;
  per_page?:           number;
  status?:             PoStatus | '';
  search?:             string;
  vendor_customer_id?: number | null;
  division?:           'europe' | 'china' | '';
}

// ─── Attachment ──────────────────────────────────────────────
export interface Attachment {
  id:               number;
  name:             string;
  mimetype:         string;
  size:             number;
  url:              string;
  uploaded_by_name: string;
  created_at:       string;
}

// ─── Comment ─────────────────────────────────────────────────
export interface Comment {
  id:          number;
  body:        string;
  type:        'comment' | 'note';
  author_id:   number;
  author_name: string;
  created_at:  string;
}
