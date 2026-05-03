// ─────────────────────────────────────────────────────────────────────────────
// Lugal Email API Service
// All requests go through Vite proxy → Odoo :8070
// Auth: Bearer JWT token from localStorage
// ─────────────────────────────────────────────────────────────────────────────

import type {
  AccountConfigPayload,
  ApiResponse,
  EmailAccount,
  EmailDetail,
  EmailFolder,
  EmailListResponse,
  EmailNotifications,
  ForwardPayload,
  LinkRecordPayload,
  ReplyPayload,
  SendEmailPayload,
  SyncResult,
} from '../types/email';

const BASE = '/api/lugal/email';

/** Retrieve JWT token stored after CRM login. */
function getToken(): string {
  return localStorage.getItem('crm_jwt_token') ?? '';
}

/** Core HTTP helper — wraps fetch with auth headers and JSON parsing. */
async function call<T>(
  endpoint: string,
  method:   'GET' | 'POST' | 'PATCH' | 'DELETE' = 'GET',
  body?:    unknown,
): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = {
    Authorization: `Bearer ${getToken()}`,
  };
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const res = await fetch(`${BASE}${endpoint}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    const contentType = res.headers.get('content-type') ?? '';
    if (!contentType.includes('application/json')) {
      return { success: false, error: `HTTP ${res.status}` };
    }

    const json = (await res.json()) as ApiResponse<T>;
    if (!json.success) {
      console.error(`[EmailAPI] ${method} ${endpoint} →`, json.error);
    }
    return json;
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Network error';
    console.error(`[EmailAPI] ${method} ${endpoint} →`, message);
    return { success: false, error: message };
  }
}

// ─────────────────────────────────────────────────────────
// Account
// ─────────────────────────────────────────────────────────

/** Fetch all email accounts for the current user. */
export const listAccounts = () =>
  call<EmailAccount[]>('/accounts');

/** Create a new email account. */
export const createAccount = (payload: AccountConfigPayload) =>
  call<EmailAccount>('/accounts', 'POST', payload);

/** Update an existing email account by ID. */
export const updateAccount = (id: number, payload: AccountConfigPayload) =>
  call<EmailAccount>(`/accounts/${id}`, 'PATCH', payload);

/** Delete an email account (and all its messages) by ID. */
export const deleteAccount = (id: number) =>
  call<{ deleted: boolean; id: number }>(`/accounts/${id}`, 'DELETE');

/** Test IMAP connection for a specific account. */
export const testConnection = (id: number) =>
  call<{ status: string; account_id: number }>(`/accounts/${id}/test`, 'POST');

/** Trigger IMAP sync for a specific account. */
export const syncAccount = (id: number) =>
  call<SyncResult>(`/accounts/${id}/sync`, 'POST');

/** Set a specific account as the user's default for sending. */
export const setDefaultAccount = (id: number) =>
  call<{ id: number; is_default: boolean }>(`/accounts/${id}/set_default`, 'POST');

// ─────────────────────────────────────────────────────────
// Messages — list & detail
// ─────────────────────────────────────────────────────────

export interface ListMessagesParams {
  /** Filter by a specific account ID (omit to see all accounts) */
  account_id?:   number;
  folder?:       EmailFolder;
  limit?:        number;
  offset?:       number;
  query?:        string;
  starred?:      boolean;
  /** Filter by linked record model (for CRM embedding) */
  linked_model?: string;
  /** Filter by linked record id   (requires linked_model) */
  linked_id?:    number;
}

/** List messages in a folder with optional search / pagination / record filter. */
export const listMessages = (params?: ListMessagesParams) => {
  const qs = new URLSearchParams();
  if (params?.account_id)   qs.set('account_id',   String(params.account_id));
  if (params?.folder)       qs.set('folder',        params.folder);
  if (params?.limit)        qs.set('limit',        String(params.limit));
  if (params?.offset)       qs.set('offset',       String(params.offset));
  if (params?.query)        qs.set('query',        params.query);
  if (params?.starred)      qs.set('starred',      '1');
  if (params?.linked_model) qs.set('linked_model', params.linked_model);
  if (params?.linked_id)    qs.set('linked_id',    String(params.linked_id));
  const suffix = qs.toString() ? `?${qs}` : '';
  return call<EmailListResponse>(`/messages${suffix}`);
};

/** Fetch all messages linked to a specific CRM record (any folder). */
export const getMessagesForRecord = (model: string, recordId: number, params?: {
  folder?:  EmailFolder;
  limit?:   number;
  offset?:  number;
}) =>
  listMessages({
    ...params,
    linked_model: model,
    linked_id:    recordId,
  });

/** Get full email detail (also marks it as read server-side). */
export const getMessage = (id: number) =>
  call<EmailDetail>(`/messages/${id}`);

// ─────────────────────────────────────────────────────────
// Send / Reply / Forward
// ─────────────────────────────────────────────────────────

/** Compose and send a new email. */
export const sendEmail = (payload: SendEmailPayload) =>
  call<{ sent: boolean }>('/send', 'POST', payload);

/** Reply to an existing message. */
export const replyMessage = (id: number, payload: ReplyPayload) =>
  call<{ sent: boolean }>(`/messages/${id}/reply`, 'POST', payload);

/** Forward a message to new recipients. */
export const forwardMessage = (id: number, payload: ForwardPayload) =>
  call<{ sent: boolean }>(`/messages/${id}/forward`, 'POST', payload);

// ─────────────────────────────────────────────────────────
// Status actions
// ─────────────────────────────────────────────────────────

/** Mark a message as read or unread. */
export const markRead = (id: number, is_read: boolean) =>
  call<{ id: number; is_read: boolean }>(`/messages/${id}/read`, 'POST', { is_read });

/** Toggle the starred flag. */
export const toggleStar = (id: number) =>
  call<{ id: number; is_starred: boolean }>(`/messages/${id}/star`, 'POST');

/** Move message to trash (soft-delete). */
export const deleteMessage = (id: number) =>
  call<{ id: number; folder: string }>(`/messages/${id}`, 'DELETE');

/** Restore a trashed / archived message back to inbox. */
export const restoreMessage = (id: number) =>
  call<{ id: number; folder: string }>(`/messages/${id}/restore`, 'POST');

/** Move a message to the archive folder. */
export const archiveMessage = (id: number) =>
  call<{ id: number; folder: string }>(`/messages/${id}/archive`, 'POST');

// ─────────────────────────────────────────────────────────
// Record linking
// ─────────────────────────────────────────────────────────

/** Link an email to a CRM record (customer, ticket, etc.). */
export const linkToRecord = (id: number, payload: LinkRecordPayload) =>
  call<{ id: number; linked: { model: string; id: number; name: string } }>(
    `/messages/${id}/link`, 'POST', payload
  );

/** Remove any record association from a message. */
export const unlinkRecord = (id: number) =>
  call<{ id: number; linked: null }>(`/messages/${id}/unlink`, 'POST');

// ─────────────────────────────────────────────────────────
// Notifications
// ─────────────────────────────────────────────────────────

/** Get unread counts for the notification badge and sidebar. */
export const getNotifications = () =>
  call<EmailNotifications>('/notifications');

// ── Default export (grouped object for convenience) ───────
const emailApi = {
  // accounts (multi-account)
  listAccounts,
  createAccount,
  updateAccount,
  deleteAccount,
  testConnection,
  syncAccount,
  setDefaultAccount,
  // messages
  listMessages,
  getMessagesForRecord,
  getMessage,
  // compose
  sendEmail,
  replyMessage,
  forwardMessage,
  // status
  markRead,
  toggleStar,
  deleteMessage,
  restoreMessage,
  archiveMessage,
  // linking
  linkToRecord,
  unlinkRecord,
  // notifications
  getNotifications,
};

export default emailApi;
