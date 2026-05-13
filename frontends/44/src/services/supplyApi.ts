// ============================================================
// Supply Chain API Service — JSON-RPC
// ============================================================
// All supply chain endpoints use Odoo JSON-RPC format.
// JWT token stored in localStorage; refreshed on 401.
// With VITE_ODOO_URL empty, fetch('/api/...') hits Vite → proxied to VITE_PROXY_TARGET (see vite.config.ts).
// ============================================================

import type {
  JrpcResult,
  AuthResult,
  Vendor,
  VendorListData,
  VendorCreateInput,
  Container,
  ContainerStatus,
  ContainerListData,
  ContainerCreateInput,
  ContainerListFilter,
  Po,
  PoListData,
  PoLine,
  PoListFilter,
  PoCreateInput,
  PoUpdateInput,
  PoLineInput,
  Attachment,
  Comment,
  Penalty,
  PenaltyInput,
  Negotiation,
  NegotiationListData,
  NegotiationListFilter,
  NegotiationCommentRow,
  PaymentPoListData,
  PaymentCurrenciesListData,
  PaymentCreateInput,
  SupplyPayment,
} from '../types/supply';

// ── Config ─────────────────────────────────────────────────────────────────
const BASE      = (import.meta.env.VITE_ODOO_URL ?? '');
const TOKEN_KEY = 'supply_jwt';

export const getToken   = ()           => localStorage.getItem(TOKEN_KEY) ?? '';
export const saveToken  = (t: string)  => localStorage.setItem(TOKEN_KEY, t);
export const clearToken = ()           => localStorage.removeItem(TOKEN_KEY);

// ── JSON-RPC core ──────────────────────────────────────────────────────────
async function rpc<T>(
  endpoint: string,
  params: Record<string, unknown> = {},
): Promise<JrpcResult<T>> {
  const token = getToken();
  const res = await fetch(`${BASE}${endpoint}`, {
    method:  'POST',
    headers: {
      'Content-Type':  'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params }),
  });

  const json = await res.json().catch(() => null);
  // Odoo JSON-RPC wraps result in { result: ... }
  const result = json?.result ?? json;

  if (!result) {
    return { success: false, data: null as T, error: `HTTP ${res.status}` };
  }
  return result as JrpcResult<T>;
}

// ── Multipart upload helpers ───────────────────────────────────────────────
async function uploadMultiple(
  endpoint: string,
  files: File[],
): Promise<JrpcResult<{ attachments: Attachment[]; uploaded_count: number; total_attachments: number }>> {
  const form = new FormData();
  for (const file of files) {
    form.append('files[]', file);
  }
  const res = await fetch(`${BASE}${endpoint}`, {
    method:  'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body:    form,
  });
  return res.json().catch(() => ({ success: false, error: `HTTP ${res.status}` }));
}

// Kept for single-file callers
async function upload(
  endpoint: string,
  file: File,
  label?: string,
): Promise<JrpcResult<{ attachments: Attachment[]; uploaded_count: number; total_attachments: number }>> {
  const form = new FormData();
  form.append('file', file);
  if (label) form.append('label', label);
  const res = await fetch(`${BASE}${endpoint}`, {
    method:  'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body:    form,
  });
  return res.json().catch(() => ({ success: false, error: `HTTP ${res.status}` }));
}

// ═══════════════════════════════════════════════════════════════════════════
// AUTH
// ═══════════════════════════════════════════════════════════════════════════
export async function login(username: string, password: string): Promise<JrpcResult<AuthResult>> {
  const res = await fetch(`${BASE}/lugal/auth/login`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { username, password } }),
  });
  const json = await res.json().catch(() => null);
  const result = json?.result ?? json;
  if (result?.success && result?.data?.access_token) {
    saveToken(result.data.access_token);
  }
  return result;
}

// ═══════════════════════════════════════════════════════════════════════════
// VENDORS
// ═══════════════════════════════════════════════════════════════════════════
export const vendorList = (
  search = '',
  page = 1,
  per_page = 50,
  division?: '' | 'europe' | 'china' | 'other',
) =>
  rpc<VendorListData>('/api/crm/supply/vendors/list', {
    search,
    page,
    per_page,
    ...(division ? { division } : {}),
  });

export const vendorGet = (id: number) =>
  rpc<Vendor>(`/api/crm/supply/vendors/${id}/get`, {});

export const vendorCreate = (input: VendorCreateInput) =>
  rpc<Vendor>('/api/crm/supply/vendors/create', { ...input });

export const vendorUpdate = (id: number, vals: Partial<VendorCreateInput>) =>
  rpc<Vendor>(`/api/crm/supply/vendors/${id}/update`, { ...vals });

export const vendorDelete = (id: number) =>
  rpc<{ id: number; deleted: boolean }>(`/api/crm/supply/vendors/${id}/delete`, {});

// ═══════════════════════════════════════════════════════════════════════════
// CONTAINERS / SHIPMENTS (CRUD uses `/shipments/*`; actions use `/containers/*`)
// ═══════════════════════════════════════════════════════════════════════════

const CRM_CONTAINER_STATUSES: readonly ContainerStatus[] = ['waiting', 'active', 'at_port', 'completed'];

/** Map `/shipments/*` payload to the SPA `Container` shape (aliases + defaults). */
function normalizeShipmentRow(raw: unknown): Container {
  const r = raw && typeof raw === 'object' ? (raw as Record<string, unknown>) : {};
  const stRaw = r.status;
  const status: ContainerStatus =
    typeof stRaw === 'string' && (CRM_CONTAINER_STATUSES as readonly string[]).includes(stRaw)
      ? (stRaw as ContainerStatus)
      : 'waiting';
  const linked = r.linked_orders;
  return {
    id: Number(r.id ?? 0),
    shipment_id: typeof r.shipment_id === 'string' ? r.shipment_id : undefined,
    shipment_tracking_state: typeof r.shipment_tracking_state === 'string' ? r.shipment_tracking_state : undefined,
    ...(Array.isArray(linked) ? { linked_orders: linked as Container['linked_orders'] } : {}),
    name: String(r.name ?? ''),
    container_number: String(r.container_number ?? ''),
    bl_number: String(r.bl_number ?? ''),
    clearance_company_id: (r.clearance_company_id as number | null) ?? null,
    clearance_company_name: String(r.clearance_company_name ?? ''),
    origin_location: String(r.origin_location ?? r.origin ?? ''),
    destination_port: String(r.destination_port ?? r.destination ?? ''),
    departure_date: (r.departure_date ?? r.etd ?? null) as string | null,
    eta: (r.eta ?? null) as string | null,
    arrived_at: (r.arrived_at ?? null) as string | null,
    status,
    division: String(r.division ?? ''),
    tracking_url: String(r.tracking_url ?? ''),
    total_weight_kg: Number(r.total_weight_kg ?? 0),
    total_cbm: Number(r.total_cbm ?? 0),
    driver_id: (r.driver_id as number | null) ?? null,
    driver_name: String(r.driver_name ?? ''),
    driver_phone: String(r.driver_phone ?? ''),
    driver_assigned_at: (r.driver_assigned_at ?? null) as string | null,
    driver_assigned_by: String(r.driver_assigned_by ?? ''),
    clearance_info_delivered: Boolean(r.clearance_info_delivered),
    clearance_info_delivered_at: (r.clearance_info_delivered_at ?? null) as string | null,
    clearance_info_delivered_by: String(r.clearance_info_delivered_by ?? ''),
    attachment_count: Number(r.attachment_count ?? 0),
    penalty_count: Number(r.penalty_count ?? 0),
    vendor_id: (r.vendor_id as number | null) ?? (r.supplier_id as number | null) ?? null,
    vendor_name: String(r.vendor_name ?? r.supplier_name ?? ''),
    reminder_date: (r.reminder_date ?? null) as string | null,
    reminder_note: String(r.reminder_note ?? ''),
    notes: String(r.notes ?? ''),
    created_at: String(r.created_at ?? ''),
    updated_at: String(r.updated_at ?? ''),
  };
}

export async function containerList(filter: ContainerListFilter = {}): Promise<JrpcResult<ContainerListData>> {
  const res = await rpc<ContainerListData>('/api/crm/supply/shipments/list', {
    page:      filter.page     ?? 1,
    per_page:  filter.per_page ?? 20,
    ...(filter.status   ? { status:   filter.status   } : {}),
    ...(filter.division ? { division: filter.division } : {}),
    ...(filter.search   ? { search:   filter.search   } : {}),
  });
  if (!res.success || !res.data) return res;
  const d = res.data;
  return {
    ...res,
    data: {
      ...d,
      items: (d.items ?? []).map(normalizeShipmentRow),
    },
  };
}

export async function containerGet(id: number): Promise<JrpcResult<Container>> {
  const res = await rpc<Container>(`/api/crm/supply/shipments/${id}/get`, {});
  if (!res.success || !res.data) return res;
  return { ...res, data: normalizeShipmentRow(res.data) };
}

export async function containerCreate(input: ContainerCreateInput): Promise<JrpcResult<Container>> {
  const res = await rpc<Container>('/api/crm/supply/shipments/create', {
    name:               input.name,
    container_number:   input.container_number,
    bl_number:          input.bl_number,
    origin:             input.origin_location,
    destination:        input.destination_port,
    etd:                input.departure_date,
    eta:                input.eta,
    division:           input.division,
    tracking_url:       input.tracking_url,
    notes:              input.notes,
  });
  if (!res.success || !res.data) return res;
  return { ...res, data: normalizeShipmentRow(res.data) };
}

export async function containerUpdate(
  id: number,
  vals: Partial<ContainerCreateInput>,
): Promise<JrpcResult<Container>> {
  const payload: Record<string, unknown> = {};
  if (vals.name !== undefined) payload.name = vals.name;
  if (vals.container_number !== undefined) payload.container_number = vals.container_number;
  if (vals.bl_number !== undefined) payload.bl_number = vals.bl_number;
  if (vals.origin_location !== undefined) payload.origin = vals.origin_location;
  if (vals.destination_port !== undefined) payload.destination = vals.destination_port;
  if (vals.departure_date !== undefined) payload.etd = vals.departure_date;
  if (vals.eta !== undefined) payload.eta = vals.eta;
  if (vals.division !== undefined) payload.division = vals.division;
  if (vals.tracking_url !== undefined) payload.tracking_url = vals.tracking_url;
  if (vals.notes !== undefined) payload.notes = vals.notes;
  const res = await rpc<Container>(`/api/crm/supply/shipments/${id}/update`, payload);
  if (!res.success || !res.data) return res;
  return { ...res, data: normalizeShipmentRow(res.data) };
}

export const containerDelete = (id: number) =>
  rpc<{ id: number; deleted: boolean }>(`/api/crm/supply/shipments/${id}/delete`, {});

/** Attach POs to a shipment/container (`order_ids` or `po_ids`). */
export async function shipmentLinkOrders(
  shipmentId: number,
  orderIds: number[],
): Promise<JrpcResult<Container>> {
  const res = await rpc<Container>(`/api/crm/supply/shipments/${shipmentId}/link_orders`, {
    order_ids: orderIds,
  });
  if (!res.success || !res.data) return res;
  return { ...res, data: normalizeShipmentRow(res.data) };
}

export const containerMarkArrived = (id: number) =>
  rpc<Container>(`/api/crm/supply/containers/${id}/mark_arrived`, {});

export const containerClearanceDelivered = (id: number) =>
  rpc<Container>(`/api/crm/supply/containers/${id}/clearance_delivered`, {});

export const containerAssignDriver = (
  id: number,
  payload: { driver_id?: number; driver_name?: string; driver_phone?: string },
) => rpc<Container>(`/api/crm/supply/containers/${id}/assign_driver`, { ...payload });

export const containerUnassignDriver = (id: number) =>
  rpc<Container>(`/api/crm/supply/containers/${id}/unassign_driver`, {});

export const containerSetReminder = (
  id: number,
  payload: { reminder_date?: string; reminder_note?: string; clear_reminder?: boolean },
) => rpc<Container>(`/api/crm/supply/containers/${id}/set_reminder`, { ...payload });

// ── Container Attachments ──────────────────────────────────────────────────
export const containerAttachList = (containerId: number) =>
  rpc<{ container_id: number; attachments: Attachment[] }>(
    `/api/crm/supply/containers/${containerId}/attachments/list`, {},
  );

export const containerAttachUpload = (containerId: number, file: File, label?: string) =>
  upload(`/api/crm/supply/containers/${containerId}/attachments/upload`, file, label);

export const containerAttachUploadMultiple = (containerId: number, files: File[]) =>
  uploadMultiple(`/api/crm/supply/containers/${containerId}/attachments/upload`, files);

export const containerAttachDelete = (containerId: number, attId: number) =>
  rpc<{ deleted_id: number }>(
    `/api/crm/supply/containers/${containerId}/attachments/${attId}/delete`, {},
  );

// ── Container Comments ─────────────────────────────────────────────────────
export const containerCommentList = (containerId: number, page = 1) =>
  rpc<{ total: number; items: Comment[] }>(
    `/api/crm/supply/containers/${containerId}/comments/list`, { page },
  );

export const containerCommentAdd = (containerId: number, body: string, is_note = false) =>
  rpc<Comment>(`/api/crm/supply/containers/${containerId}/comments/add`, { body, is_note });

export const containerCommentDelete = (containerId: number, msgId: number) =>
  rpc<{ id: number }>(`/api/crm/supply/containers/${containerId}/comments/${msgId}/delete`, {});

// ── Container Penalties ────────────────────────────────────────────────────
export const containerAddPenalty = (containerId: number, input: PenaltyInput) =>
  rpc<Penalty>(`/api/crm/supply/containers/${containerId}/add_penalty`, {
    penalty_type:  input.penalty_type,
    amount:        input.amount,
    ...(input.reason       ? { reason:       input.reason       } : {}),
    ...(input.penalty_date ? { penalty_date: input.penalty_date } : {}),
    ...(input.currency_id  ? { currency_id:  input.currency_id  } : {}),
  });

export const containerPenaltiesList = (containerId: number) =>
  rpc<{ container_id: number; container_name: string; total: number; total_amount: number; items: Penalty[] }>(
    `/api/crm/supply/containers/${containerId}/penalties/list`, {},
  );

export const containerPenaltyDelete = (containerId: number, penaltyId: number) =>
  rpc<{ deleted_id: number; container_id: number }>(
    `/api/crm/supply/containers/${containerId}/penalties/${penaltyId}/delete`, {},
  );

// ═══════════════════════════════════════════════════════════════════════════
// NEGOTIATIONS
// ═══════════════════════════════════════════════════════════════════════════
export const negotiationList = (filter: NegotiationListFilter = {}) =>
  rpc<NegotiationListData>('/api/crm/supply/negotiations/list', {
    page:     filter.page     ?? 1,
    per_page: filter.per_page ?? 20,
    ...(filter.state           ? { state: filter.state } : {}),
    ...(filter.vendor_id       ? { vendor_id: filter.vendor_id } : {}),
    ...(filter.item_request_id ? { item_request_id: filter.item_request_id } : {}),
    ...(filter.search          ? { search: filter.search } : {}),
  });

export const negotiationGet = (negId: number) =>
  rpc<Negotiation>(`/api/crm/supply/negotiations/${negId}/get`, {});

/** Record e-sign only; negotiation stays ``ongoing`` until confirm/finalize. */
export const negotiationESignApprove = (negId: number) =>
  rpc<Negotiation>(`/api/crm/supply/negotiations/${negId}/e_sign_approve`, {});

/** Finalize negotiation (sets state to ``finalized``). */
export const negotiationConfirm = (negId: number) =>
  rpc<Negotiation>(`/api/crm/supply/negotiations/${negId}/confirm`, {});

/** Same as ``negotiationConfirm`` — backend alias route ``/finalize``. */
export const negotiationFinalize = (negId: number) =>
  rpc<Negotiation>(`/api/crm/supply/negotiations/${negId}/finalize`, {});

export const negotiationCommentList = (negId: number, page = 1, per_page = 50) =>
  rpc<{ total: number; page: number; per_page: number; items: NegotiationCommentRow[] }>(
    `/api/crm/supply/negotiations/${negId}/comments/list`,
    { page, per_page },
  );

export const negotiationCommentAdd = (negId: number, body: string) =>
  rpc<{ posted: boolean }>(`/api/crm/supply/negotiations/${negId}/comments/add`, { body });

export const negotiationCommentDelete = (negId: number, msgId: number) =>
  rpc<{ id: number; deleted: boolean }>(
    `/api/crm/supply/negotiations/${negId}/comments/${msgId}/delete`,
    {},
  );

// ═══════════════════════════════════════════════════════════════════════════
// PURCHASE ORDERS
// ═══════════════════════════════════════════════════════════════════════════
/** POST /api/crm/supply/po/suggested — POs with `is_suggested=true` */
export const poSuggested = (page = 1, per_page = 20, division?: '' | 'europe' | 'china') =>
  rpc<PoListData>('/api/crm/supply/po/suggested', {
    page,
    per_page,
    ...(division ? { division } : {}),
  });

export const poList = (filter: PoListFilter = {}) =>
  rpc<PoListData>('/api/crm/supply/po/list', {
    page:               filter.page     ?? 1,
    per_page:           filter.per_page ?? 20,
    ...(filter.status               ? { status:               filter.status               } : {}),
    ...(filter.search               ? { search:               filter.search               } : {}),
    ...(filter.vendor_customer_id   ? { vendor_customer_id:   filter.vendor_customer_id   } : {}),
    ...(filter.division             ? { division:             filter.division             } : {}),
  });

export const poGet = (id: number) =>
  rpc<Po>(`/api/crm/supply/po/${id}/get`, {});

export const poCreate = (input: PoCreateInput) =>
  rpc<Po>('/api/crm/supply/po/create', {
    name:               input.name,
    vendor_customer_id: input.vendor_customer_id ?? undefined,
    ...(input.division    ? { division:    input.division    } : {}),
    ...(input.currency_id ? { currency_id: input.currency_id } : {}),
    ...(input.container_id? { container_id:input.container_id} : {}),
    ...(input.branch_id   ? { branch_id:   input.branch_id   } : {}),
    lines: input.lines,
  });

export const poUpdate = (id: number, vals: PoUpdateInput) =>
  rpc<Po>(`/api/crm/supply/po/${id}/update`, vals as Record<string, unknown>);

export const poDelete = (id: number) =>
  rpc<{ id: number; deleted: boolean }>(`/api/crm/supply/po/${id}/delete`, {});

// Status transitions
export const poSubmit   = (id: number) => rpc<Po>(`/api/crm/supply/po/${id}/submit`,  {});
export const poConfirm  = (id: number) => rpc<Po>(`/api/crm/supply/po/${id}/confirm`,  {});
export const poShip     = (id: number) => rpc<Po>(`/api/crm/supply/po/${id}/ship`,     {});
export const poReceive  = (id: number) => rpc<Po>(`/api/crm/supply/po/${id}/receive`,  {});
export const poCancel   = (id: number) => rpc<Po>(`/api/crm/supply/po/${id}/cancel`,   {});
export const poReopen   = (id: number) => rpc<Po>(`/api/crm/supply/po/${id}/reopen`,   {});

// ── PO Lines ───────────────────────────────────────────────────────────────
export const poLineAdd = (poId: number, line: PoLineInput) =>
  rpc<PoLine>(`/api/crm/supply/po/${poId}/lines/add`, line as unknown as Record<string, unknown>);

export const poLineUpdate = (poId: number, lineId: number, vals: Partial<PoLineInput>) =>
  rpc<PoLine>(`/api/crm/supply/po/${poId}/lines/${lineId}/update`, vals as Record<string, unknown>);

export const poLineDelete = (poId: number, lineId: number) =>
  rpc<{ id: number; deleted: boolean }>(`/api/crm/supply/po/${poId}/lines/${lineId}/delete`, {});

// ── PO Attachments ────────────────────────────────────────────────────────
export const poAttachList   = (poId: number) =>
  rpc<{ po_id: number; attachments: Attachment[] }>(`/api/crm/supply/po/${poId}/attachments/list`, {});

export const poAttachUpload = (poId: number, file: File, label?: string) =>
  upload(`/api/crm/supply/po/${poId}/attachments/upload`, file, label);

export const poAttachUploadMultiple = (poId: number, files: File[]) =>
  uploadMultiple(`/api/crm/supply/po/${poId}/attachments/upload`, files);

export const poAttachDelete = (poId: number, attId: number) =>
  rpc<{ deleted_id: number }>(`/api/crm/supply/po/${poId}/attachments/${attId}/delete`, {});

// ── PO Comments ───────────────────────────────────────────────────────────
export const poCommentList = (poId: number, page = 1) =>
  rpc<{ total: number; items: Comment[] }>(`/api/crm/supply/po/${poId}/comments/list`, { page });

export const poCommentAdd = (poId: number, body: string, is_note = false) =>
  rpc<Comment>(`/api/crm/supply/po/${poId}/comments/add`, { body, is_note });

export const poCommentDelete = (poId: number, msgId: number) =>
  rpc<{ id: number }>(`/api/crm/supply/po/${poId}/comments/${msgId}/delete`, {});

/** Packing list — plain text for share / clipboard */
export const poPackingListShare = (poId: number) =>
  rpc<{ title: string; text: string; url?: string }>(`/api/crm/supply/po/${poId}/packing-list/share`, {});

/** Packing list — PDF as base64 for client download */
export const poPackingListPdf = (poId: number) =>
  rpc<{ filename: string; pdf_base64: string; mimetype: string }>(
    `/api/crm/supply/po/${poId}/packing-list/pdf`,
    {},
  );

// ═══════════════════════════════════════════════════════════════════════════
// PAYMENTS
// ═══════════════════════════════════════════════════════════════════════════
/** Lightweight searchable PO list for payment forms (`po_id` = `item.id`). */
export const paymentsPoList = (filter: {
  search?:   string;
  page?:     number;
  per_page?: number;
  status?:   string;
  division?: '' | 'europe' | 'china';
} = {}) =>
  rpc<PaymentPoListData>('/api/crm/supply/payments/po/list', {
    page:     filter.page     ?? 1,
    per_page: filter.per_page ?? 25,
    ...(filter.search   ? { search:   filter.search   } : {}),
    ...(filter.status   ? { status:   filter.status   } : {}),
    ...(filter.division ? { division: filter.division } : {}),
  });

/** Active currencies for payment form dropdown (`item.id` = `currency_id` on create). */
export const paymentsCurrenciesList = (filter: { search?: string; page?: number; per_page?: number } = {}) =>
  rpc<PaymentCurrenciesListData>('/api/crm/supply/currencies/list', {
    page:     filter.page     ?? 1,
    per_page: filter.per_page ?? 200,
    ...(filter.search ? { search: filter.search } : {}),
  });

export const paymentsCreate = (input: PaymentCreateInput) =>
  rpc<SupplyPayment>('/api/crm/supply/payments/create', {
    po_id:  input.po_id,
    amount: input.amount,
    ...(input.payment_type   ? { payment_type:   input.payment_type   } : {}),
    ...(input.notes          ? { notes:          input.notes          } : {}),
    ...(input.payment_date   ? { payment_date:   input.payment_date   } : {}),
    ...(input.currency_id    != null ? { currency_id:    input.currency_id    } : {}),
    ...(input.payment_method ? { payment_method: input.payment_method } : {}),
    ...(input.paid_to        ? { paid_to:        input.paid_to        } : {}),
    ...(input.payee_partner_id != null ? { payee_partner_id: input.payee_partner_id } : {}),
  });

// ── Named export bundle ────────────────────────────────────────────────────
const supplyApi = {
  login,
  getToken, saveToken, clearToken,
  // negotiations
  negotiationList, negotiationGet, negotiationESignApprove, negotiationConfirm, negotiationFinalize,
  negotiationCommentList, negotiationCommentAdd, negotiationCommentDelete,
  // vendors
  vendorList, vendorGet, vendorCreate, vendorUpdate, vendorDelete,
  // containers
  containerList, containerGet, containerCreate, containerUpdate, containerDelete,
  shipmentLinkOrders,
  containerMarkArrived, containerClearanceDelivered,
  containerAssignDriver, containerUnassignDriver, containerSetReminder,
  containerAttachList, containerAttachUpload, containerAttachUploadMultiple, containerAttachDelete,
  containerCommentList, containerCommentAdd, containerCommentDelete,
  containerAddPenalty, containerPenaltiesList, containerPenaltyDelete,
  // purchase orders
  poSuggested, poList, poGet, poCreate, poUpdate, poDelete,
  poSubmit, poConfirm, poShip, poReceive, poCancel, poReopen,
  poLineAdd, poLineUpdate, poLineDelete,
  poAttachList, poAttachUpload, poAttachUploadMultiple, poAttachDelete,
  poCommentList, poCommentAdd, poCommentDelete,
  poPackingListShare, poPackingListPdf,
  paymentsPoList, paymentsCurrenciesList, paymentsCreate,
};

export default supplyApi;
