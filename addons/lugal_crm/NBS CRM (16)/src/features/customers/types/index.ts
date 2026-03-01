import type { PaginatedResponse } from '../../../shared/types';

export interface ChannelIdentity {
  channel:  string;
  handle:   string;
  verified: boolean;
}

export interface Customer {
  id:                  number;
  name:                string;
  name_ar?:            string;
  phone_1:             string;
  phone_2?:            string;
  email?:              string;
  address?:            string;
  city?:               string;
  shop_location?:      string;
  billing_address?:    string;
  vip_status:          boolean;
  stage_id?:           number;
  stage_name?:         string;
  stage_type?:         string;
  lifetime_value?:     number;
  credit_debt?:        number;
  member_since?:       string;
  last_call_date?:     string;
  last_purchase_date?: string;
  account_manager?:    string;
  sample_version?:     string;
  branch_ids?:         number[];
  tag_ids?:            number[];
  tag_names?:          string[];
  channel_identities?: ChannelIdentity[];
  is_deleted:          boolean;
  active:              boolean;
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
  name:        string;
  phone_1:     string;
  email?:      string;
  address?:    string;
  city?:       string;
  vip_status?: boolean;
  stage_id?:   number;
  branch_ids?: number[];
  tag_ids?:    number[];
}

export interface Customer360 extends Customer {
  interactions?:  unknown[];
  call_history?:  unknown[];
  tickets?:       unknown[];
  open_invoices?: unknown[];
}
