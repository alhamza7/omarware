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
  Po,
  PoListData,
  PoLine,
  PoListFilter,
  PoCreateInput,
  PoLineInput,
  Attachment,
  Comment,
} from '../types/supply';

// ── Config ─────────────────────────────────────────────────────────────────
const BASE   = (import.meta.env.VITE_ODOO_URL ?? '');
const TOKEN_KEY = 'supply_jwt';

export const getToken  = ()           => localStorage.getItem(TOKEN_KEY) ?? '';
export const saveToken = (t: string)  => localStorage.setItem(TOKEN_KEY, t);
export const clearToken= ()           => localStorage.removeItem(TOKEN_KEY);

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
// Single file
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

// Multiple files — uses files[] field name so the server collects them all
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

export const poUpdate = (id: number, vals: Partial<{ name: string; division: string; container_id: number; branch_id: number; currency_id: number; is_suggested: boolean }>) =>
  rpc<Po>(`/api/crm/supply/po/${id}/update`, vals);

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
  rpc<PoLine>(`/api/crm/supply/po/${poId}/lines/${lineId}/update`, vals);

export const poLineDelete = (poId: number, lineId: number) =>
  rpc<{ id: number; deleted: boolean }>(`/api/crm/supply/po/${poId}/lines/${lineId}/delete`, {});

// ── Attachments ────────────────────────────────────────────────────────────
export const poAttachList   = (poId: number) =>
  rpc<{ po_id: number; attachments: Attachment[] }>(`/api/crm/supply/po/${poId}/attachments/list`, {});

export const poAttachUpload = (poId: number, file: File, label?: string) =>
  upload(`/api/crm/supply/po/${poId}/attachments/upload`, file, label);

export const poAttachUploadMultiple = (poId: number, files: File[]) =>
  uploadMultiple(`/api/crm/supply/po/${poId}/attachments/upload`, files);

export const poAttachDelete = (poId: number, attId: number) =>
  rpc<{ deleted_id: number }>(`/api/crm/supply/po/${poId}/attachments/${attId}/delete`, {});

// ── Container Attachments ──────────────────────────────────────────────────
export const containerAttachList = (containerId: number) =>
  rpc<{ container_id: number; attachments: Attachment[] }>(
    `/api/crm/supply/containers/${containerId}/attachments/list`, {},
  );

/** Upload a single file to a container */
export const containerAttachUpload = (containerId: number, file: File, label?: string) =>
  upload(`/api/crm/supply/containers/${containerId}/attachments/upload`, file, label);

/** Upload multiple files to a container in one request (uses files[] field) */
export const containerAttachUploadMultiple = (containerId: number, files: File[]) =>
  uploadMultiple(`/api/crm/supply/containers/${containerId}/attachments/upload`, files);

export const containerAttachDelete = (containerId: number, attId: number) =>
  rpc<{ deleted_id: number }>(
    `/api/crm/supply/containers/${containerId}/attachments/${attId}/delete`, {},
  );

// ── Comments ───────────────────────────────────────────────────────────────
export const poCommentList = (poId: number, page = 1) =>
  rpc<{ total: number; items: Comment[] }>(`/api/crm/supply/po/${poId}/comments/list`, { page });

export const poCommentAdd = (poId: number, body: string, is_note = false) =>
  rpc<Comment>(`/api/crm/supply/po/${poId}/comments/add`, { body, is_note });

export const poCommentDelete = (poId: number, msgId: number) =>
  rpc<{ id: number }>(`/api/crm/supply/po/${poId}/comments/${msgId}/delete`, {});

// ═══════════════════════════════════════════════════════════════════════════
// CONTAINER PENALTIES
// ═══════════════════════════════════════════════════════════════════════════
export interface PenaltyInput {
  penalty_type: 'storage' | 'damage' | 'late' | 'customs' | 'demurrage' | 'other';
  amount:       number;
  reason?:      string;
  penalty_date?: string;  // YYYY-MM-DD
  currency_id?:  number;
}

export interface Penalty {
  id:              number;
  container_id:    number;
  container_name:  string;
  penalty_type:    string;
  amount:          number;
  currency_id:     number | null;
  currency_name:   string;
  reason:          string;
  penalty_date:    string;
  created_by_name: string;
  created_at:      string;
}

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

// ── Named export bundle ────────────────────────────────────────────────────
const supplyApi = {
  login,
  getToken, saveToken, clearToken,
  vendorList,
  poList, poGet, poCreate, poUpdate, poDelete,
  poConfirm, poShip, poReceive, poCancel, poReopen,
  poLineAdd, poLineUpdate, poLineDelete,
  poAttachList, poAttachUpload, poAttachUploadMultiple, poAttachDelete,
  poCommentList, poCommentAdd, poCommentDelete,
  containerAttachList, containerAttachUpload, containerAttachUploadMultiple, containerAttachDelete,
  containerAddPenalty, containerPenaltiesList, containerPenaltyDelete,
};

export default supplyApi;
