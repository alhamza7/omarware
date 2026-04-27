// ============================================================
// Supply Chain API Service — JSON-RPC
// ============================================================
// All supply chain endpoints use Odoo JSON-RPC format.
// JWT token stored in localStorage; refreshed on 401.
// Proxy: Vite forwards /api → http://192.168.116.204:8070
// ============================================================

import type {
  JrpcResult,
  AuthResult,
  Vendor,
  VendorListData,
  VendorCreateInput,
  Container,
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
export const vendorList = (search = '', page = 1, per_page = 50) =>
  rpc<VendorListData>('/api/crm/supply/vendors/list', { search, page, per_page });

export const vendorGet = (id: number) =>
  rpc<Vendor>(`/api/crm/supply/vendors/${id}/get`, {});

export const vendorCreate = (input: VendorCreateInput) =>
  rpc<Vendor>('/api/crm/supply/vendors/create', { ...input });

export const vendorUpdate = (id: number, vals: Partial<VendorCreateInput>) =>
  rpc<Vendor>(`/api/crm/supply/vendors/${id}/update`, { ...vals });

export const vendorDelete = (id: number) =>
  rpc<{ id: number; deleted: boolean }>(`/api/crm/supply/vendors/${id}/delete`, {});

// ═══════════════════════════════════════════════════════════════════════════
// CONTAINERS
// ═══════════════════════════════════════════════════════════════════════════
export const containerList = (filter: ContainerListFilter = {}) =>
  rpc<ContainerListData>('/api/crm/supply/containers/list', {
    page:      filter.page     ?? 1,
    per_page:  filter.per_page ?? 20,
    ...(filter.status   ? { status:   filter.status   } : {}),
    ...(filter.division ? { division: filter.division } : {}),
    ...(filter.search   ? { search:   filter.search   } : {}),
  });

export const containerGet = (id: number) =>
  rpc<Container>(`/api/crm/supply/containers/${id}/get`, {});

export const containerCreate = (input: ContainerCreateInput) =>
  rpc<Container>('/api/crm/supply/containers/create', { ...input });

export const containerUpdate = (id: number, vals: Partial<ContainerCreateInput>) =>
  rpc<Container>(`/api/crm/supply/containers/${id}/update`, { ...vals });

export const containerDelete = (id: number) =>
  rpc<{ id: number; deleted: boolean }>(`/api/crm/supply/containers/${id}/delete`, {});

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
// PURCHASE ORDERS
// ═══════════════════════════════════════════════════════════════════════════
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

// ── Named export bundle ────────────────────────────────────────────────────
const supplyApi = {
  login,
  getToken, saveToken, clearToken,
  // vendors
  vendorList, vendorGet, vendorCreate, vendorUpdate, vendorDelete,
  // containers
  containerList, containerGet, containerCreate, containerUpdate, containerDelete,
  containerMarkArrived, containerClearanceDelivered,
  containerAssignDriver, containerUnassignDriver, containerSetReminder,
  containerAttachList, containerAttachUpload, containerAttachUploadMultiple, containerAttachDelete,
  containerCommentList, containerCommentAdd, containerCommentDelete,
  containerAddPenalty, containerPenaltiesList, containerPenaltyDelete,
  // purchase orders
  poList, poGet, poCreate, poUpdate, poDelete,
  poConfirm, poShip, poReceive, poCancel, poReopen,
  poLineAdd, poLineUpdate, poLineDelete,
  poAttachList, poAttachUpload, poAttachUploadMultiple, poAttachDelete,
  poCommentList, poCommentAdd, poCommentDelete,
};

export default supplyApi;
