import type { PaginatedResponse } from '../../../shared/types';

export interface ChannelIdentity {
  channel:  string;
  handle:   string;
  verified: boolean;
}

export interface CustomerDoc {
  type: string;
  name: string;
  url:  string;
}

export interface Customer {
  // Identity
  id:                       number;
  name:                     string;
  name_ar:                  string;
  partner_id:               number | null;
  phone_1:                  string;
  phone_2:                  string;
  phone_3:                  string;
  email:                    string;
  address:                  string;
  city:                     string;
  country_id:               number | null;
  country_name:             string;
  // Classification
  stage_id:                 number | null;
  stage_name:               string;
  stage_type:               string;
  tag_ids:                  number[];
  tag_names:                string[];
  vip_status:               boolean;
  is_enterprise:            boolean;
  // Relations
  branch_ids:               number[];
  account_manager_id:       number | null;
  account_manager_name:     string;
  referral_source:          string;
  shop_name:                string;
  shop_location:            string;
  // Loyalty
  loyalty_points:           number;
  preferred_contact_time:   string;
  preferred_contact_channel: string;
  // Commerce
  credit_limit:             number;
  lifetime_value:           number;
  credit_debt:              number;
  // Dates
  member_since:             string | null;
  last_call_date:           string | null;
  last_purchase_date:       string | null;
  days_since_purchase:      number | null;
  // Status
  open_invoice_status:      string;
  delivery_status:          string;
  // Timestamps
  created_at:               string | null;
  updated_at:               string | null;
  // Social handles
  instagram_handle:         string;
  tiktok_handle:            string;
  whatsapp_number:          string;
  snapchat_handle:          string;
  twitter_handle:           string;
  telegram_handle:          string;
  pinterest_handle:         string;
  youtube_handle:           string;
  channel_identities:       ChannelIdentity[];
  // Extended classification
  activity_type:            string;
  customer_strength:        string;
  dealing_method:           string;
  customer_rating:          number;
  assigned_agent:           string;
  notes:                    string;
  // Media
  shop_images:              string[];
  customer_docs:            CustomerDoc[];
  // Soft-delete flags (internal — not needed by UI but included for completeness)
  is_deleted?:              boolean;
  active?:                  boolean;
}

export interface CustomerListParams {
  page?:       number;
  per_page?:   number;
  search?:     string;
  stage_id?:   number;
  branch_id?:  number;
  vip_only?:   boolean;
}

export type CustomerListResponse = PaginatedResponse<Customer>;

export interface CreateCustomerPayload {
  // Required
  name:                     string;
  // Identity
  name_ar?:                 string;
  phone_1?:                 string;
  phone_2?:                 string;
  phone_3?:                 string;
  email?:                   string;
  address?:                 string;
  city?:                    string;
  country_id?:              number;
  // Classification
  vip_status?:              boolean;
  is_enterprise?:           boolean;
  stage_id?:                number;
  branch_ids?:              number[];
  tag_ids?:                 number[];
  referral_source?:         string;
  shop_name?:               string;
  shop_location?:           string;
  // Loyalty
  loyalty_points?:          number;
  preferred_contact_time?:  string;
  preferred_contact_channel?: string;
  credit_limit?:            number;
  account_manager_id?:      number;
  // Social handles (stored as channel_identity records)
  instagram_handle?:        string;
  tiktok_handle?:           string;
  whatsapp_number?:         string;
  snapchat_handle?:         string;
  twitter_handle?:          string;
  telegram_handle?:         string;
  pinterest_handle?:        string;
  youtube_handle?:          string;
  // Extended classification (new)
  activity_type?:           string;
  customer_strength?:       string;
  dealing_method?:          string;
  customer_rating?:         number;
  assigned_agent?:          string;
  created_at?:              string;
  notes?:                   string;
  // Media (new)
  shop_images?:             string[];
  customer_docs?:           CustomerDoc[];
}

/** Partial update – same shape as create but all fields optional */
export type UpdateCustomerPayload = Omit<CreateCustomerPayload, 'name'> & {
  name?: string;
};

/** Single file entry returned by upload endpoints */
export interface UploadedFile {
  id:       number;
  url:      string;
  filename: string;
}

/** Response from POST /api/crm/upload/image */
export interface UploadImageResponse {
  success: boolean;
  data: {
    files: UploadedFile[];
  };
}

/** Response from POST /api/crm/upload/document */
export interface UploadDocumentResponse {
  success: boolean;
  data: {
    id:       number;
    url:      string;
    type:     string;
    name:     string;
    filename: string;
  };
}

/** Valid document types for upload */
export type CustomerDocType =
  | 'national_id'
  | 'shop_license'
  | 'tax_certificate'
  | 'commerce_registration'
  | 'residence_card'
  | 'other';

export interface Customer360 extends Customer {
  interactions?:  unknown[];
  call_history?:  unknown[];
  tickets?:       unknown[];
  open_invoices?: unknown[];
}

/** Response for delete customer: success with no data payload */
export type DeleteCustomerResponse = void;
