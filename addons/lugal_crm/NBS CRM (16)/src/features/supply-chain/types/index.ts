export interface PurchaseOrder {
  id:            number;
  po_number:     string;
  customer_id?:  number;
  customer_name?:string;
  branch_id?:    number;
  status:        'draft' | 'confirmed' | 'received' | 'cancelled';
  order_date:    string;
  expected_date?:string;
  total_amount:  number;
  currency:      string;
  lines?:        PurchaseOrderLine[];
  vendor_id?:    number;
  container_id?: number;
  is_deleted:    boolean;
}

export interface PurchaseOrderLine {
  id:          number;
  product_name:string;
  quantity:    number;
  unit_price:  number;
  subtotal:    number;
}

export interface Vendor {
  id:            number;
  name:          string;
  contact_name?: string;
  phone?:        string;
  email?:        string;
  country?:      string;
  active:        boolean;
}

export interface Container {
  id:              number;
  container_number:string;
  vendor_id?:      number;
  vendor_name?:    string;
  status:          'pending' | 'in_transit' | 'customs' | 'delivered';
  origin_country?: string;
  eta?:            string;
  cleared_at?:     string;
}

export interface CreatePoPayload {
  customer_id?:  number;
  branch_id?:    number;
  order_date?:   string;
  vendor_id?:    number;
  lines?:        Omit<PurchaseOrderLine, 'id' | 'subtotal'>[];
}
