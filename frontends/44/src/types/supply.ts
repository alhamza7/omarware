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
  website:      string;
  whatsapp:     string;
  telegram:     string;
  wechat:       string;
  division:     string;
  city:         string;
  country_name: string;
  address:      string;
  payment_terms: string;
  lead_time_days: number;
  min_order_value: number;
  contact_name: string;
  notes:        string;
  created_at:   string;
}

export interface VendorListData {
  items:    Vendor[];
  total:    number;
  page:     number;
  per_page: number;
}

export interface VendorCreateInput {
  name:          string;
  name_ar?:      string;
  contact_type?: 'customer' | 'vendor' | 'both';
  division?:     'europe' | 'china' | '';
  contact_name?: string;
  phone?:        string;
  email?:        string;
  website?:      string;
  whatsapp?:     string;
  telegram?:     string;
  city?:         string;
  address?:      string;
  payment_terms?: string;
  lead_time_days?: number;
  min_order_value?: number;
  notes?:        string;
}

// ─── PO Line ─────────────────────────────────────────────────
export interface PoLine {
  id:                  number;
  sequence:            number;
  product_name:        string;
  item_code:           string;
  uom:                 string;
  quantity_pcs?:       number;
  quantity_carton?:    number;
  quantity:            number;
  size?:               string;
  capacity?:           string;
  packing_pcs_per_carton?: number;
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
export type PoStatus = 'draft' | 'confirmed' | 'cancelled';

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
  attachment_ids?:       number[];
  attachment_count?:     number;
  attachments?:          SupplyAttachment[];
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

export interface PoUpdateInput {
  name?:         string;
  division?:     'europe' | 'china' | '';
  container_id?: number | null;
  branch_id?:    number | null;
  currency_id?:  number | null;
  is_suggested?: boolean;
}

export interface PoListFilter {
  page?:               number;
  per_page?:           number;
  status?:             PoStatus | '';
  search?:             string;
  vendor_customer_id?: number | null;
  division?:           'europe' | 'china' | '';
}

// ─── Container ───────────────────────────────────────────────
export type ContainerStatus = 'waiting' | 'active' | 'at_port' | 'completed';

export interface Container {
  id:                          number;
  name:                        string;
  container_number:            string;
  bl_number:                   string;
  clearance_company_id:        number | null;
  clearance_company_name:      string;
  origin_location:             string;
  destination_port:            string;
  departure_date:              string | null;
  eta:                         string | null;
  arrived_at:                  string | null;
  status:                      ContainerStatus;
  division:                    string;
  tracking_url:                string;
  total_weight_kg:             number;
  total_cbm:                   number;
  driver_id:                   number | null;
  driver_name:                 string;
  driver_phone:                string;
  driver_assigned_at:          string | null;
  driver_assigned_by:          string;
  clearance_info_delivered:    boolean;
  clearance_info_delivered_at: string | null;
  clearance_info_delivered_by: string;
  attachment_count:            number;
  penalty_count:               number;
  vendor_id:                   number | null;
  vendor_name:                 string;
  reminder_date:               string | null;
  reminder_note:               string;
  notes:                       string;
  created_at:                  string;
  updated_at:                  string;
}

export interface ContainerListData {
  items:    Container[];
  total:    number;
  page:     number;
  per_page: number;
}

export interface ContainerCreateInput {
  name:                string;
  container_number?:   string;
  bl_number?:          string;
  clearance_company_id?: number;
  origin_location?:    string;
  destination_port?:   string;
  departure_date?:     string;
  eta?:                string;
  division?:           string;
  tracking_url?:       string;
  total_weight_kg?:    number;
  total_cbm?:          number;
  notes?:              string;
}

export interface ContainerListFilter {
  page?:      number;
  per_page?:  number;
  status?:    ContainerStatus | '';
  division?:  string;
  search?:    string;
}

// ─── Attachment (supply-chain API §2.5) ───────────────────────
export interface SupplyAttachment {
  id:               number;
  name:             string;
  mimetype:         string;
  size:             number;
  url:              string;
  file_url:         string;
  uploaded_by_name: string;
  created_at:       string;
}

/** @deprecated Use SupplyAttachment; kept for older imports */
export type Attachment = SupplyAttachment;

// ─── Comment ─────────────────────────────────────────────────
// Backend returns is_note (boolean); type field was removed.
export interface Comment {
  id:           number;
  body:         string;
  body_html:    string;
  is_note:      boolean;
  author_id:    number | null;
  author_name:  string;
  author_avatar: string | null;
  message_type: string;
  subtype:      string;
  created_at:   string;
}

// ─── Penalty (Container) ─────────────────────────────────────
export type PenaltyType = 'storage' | 'damage' | 'late' | 'customs' | 'demurrage' | 'other';

export interface Penalty {
  id:              number;
  container_id:    number;
  container_name:  string;
  penalty_type:    PenaltyType;
  amount:          number;
  currency_id:     number | null;
  currency_name:   string;
  reason:          string;
  penalty_date:    string;
  created_by_name: string;
  created_at:      string;
}

export interface PenaltyInput {
  penalty_type:  PenaltyType;
  amount:        number;
  reason?:       string;
  penalty_date?: string;
  currency_id?:  number;
}
