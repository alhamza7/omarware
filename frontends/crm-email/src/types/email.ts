// ─────────────────────────────────────────────────────────────────────────────
// Lugal Email — TypeScript types
// Reflects the exact JSON shapes returned by /api/lugal/email/*
// ─────────────────────────────────────────────────────────────────────────────

// ── Primitives ────────────────────────────────────────────────────────────────

export type EmailFolder =
  | 'inbox'
  | 'sent'
  | 'drafts'
  | 'trash'
  | 'spam'
  | 'archive';

export type SyncStatus = 'ok' | 'error' | 'never';

export interface EmailAddress {
  name:  string;
  email: string;
}

export interface EmailAttachment {
  id:       number;
  name:     string;
  mimetype: string;
  url:      string;
}

// ── Linked record ─────────────────────────────────────────────────────────────

/** Generic link — returned by the base lugal_email model */
export interface LinkedRecord {
  model: string;
  id:    number;
  name:  string;
}

/** CRM-specific typed links — added by lugal_crm's crm_email_extension */
export interface CrmLinks {
  customer: { id: number; name: string } | null;
  ticket:   { id: number; name: string } | null;
}

// ── Message shapes ─────────────────────────────────────────────────────────────

/**
 * Lightweight shape used in list / inbox views.
 * Corresponds to `_to_list_dict()` on the Odoo model.
 */
export interface EmailListItem {
  id:               number;
  subject:          string;
  from_address:     string;
  from_name:        string;
  preview:          string;
  date:             string | null;   // ISO 8601
  folder:           EmailFolder;
  is_read:          boolean;
  is_starred:       boolean;
  attachment_count: number;
  has_link:         boolean;
  /** Generic link (always present when has_link=true) */
  linked_record:    LinkedRecord | null;
  /**
   * CRM-specific typed links.
   * Present only when lugal_crm is installed (crm_email_extension).
   * May be undefined when lugal_email runs without lugal_crm.
   */
  crm_links?: CrmLinks;
}

/**
 * Full message detail — extends list shape with body and addresses.
 * Corresponds to `_to_detail_dict()` on the Odoo model.
 */
export interface EmailDetail extends EmailListItem {
  body_html:    string;
  body_text:    string;
  to_addresses: EmailAddress[];
  cc_addresses: EmailAddress[];
  message_id:   string;
  in_reply_to:  string;
  attachments:  EmailAttachment[];
}

// ── API responses ─────────────────────────────────────────────────────────────

export interface ApiResponse<T> {
  success: boolean;
  data?:   T;
  error?:  string;
}

export interface EmailListResponse {
  total:        number;
  offset:       number;
  limit:        number;
  folder:       EmailFolder;
  unread_count: number;
  /** Unread count per folder for sidebar badges */
  per_folder:   Partial<Record<EmailFolder, number>>;
  items:        EmailListItem[];
}

export interface EmailAccount {
  id:             number;
  /** Friendly label: "Work Gmail", "Personal Outlook"… */
  name:           string;
  email_address:  string;
  display_name:   string;
  imap_host:      string;
  imap_port:      number;
  imap_use_ssl:   boolean;
  smtp_host:      string;
  smtp_port:      number;
  smtp_use_tls:   boolean;
  username:       string;
  is_active:      boolean;
  is_default:     boolean;
  sync_status:    SyncStatus;
  last_sync_date: string | null;
  unread_count:   number;
}

/** Shape returned by GET /notifications */
export interface EmailNotifications {
  inbox:              number;
  total:              number;
  /** Unread count per folder */
  per_folder:         Partial<Record<EmailFolder, number>>;
  account_configured: boolean;
  /** Per-account summary (multi-account support) */
  accounts:           Array<{
    id:           number;
    name:         string;
    email:        string;
    is_default:   boolean;
    unread_count: number;
    sync_status:  SyncStatus;
  }>;
  /** null when account_configured=false */
  sync_status:        SyncStatus | null;
  /** null when account_configured=false */
  last_sync_date:     string | null;
  /** Present when sync_status='error' */
  error_message:      string | null;
}

// ── Compose / Send payloads ────────────────────────────────────────────────────

export interface SendEmailPayload {
  /** Which account to send from; omit to use the user's default account */
  account_id?:     number;
  to:              string[];
  subject:         string;
  body_html?:      string;
  body_text?:      string;
  cc?:             string[];
  bcc?:            string[];
  attachment_ids?: number[];
}

export interface ReplyPayload extends Partial<SendEmailPayload> {
  to?:         string[];
  subject?:    string;
}

export interface ForwardPayload extends Partial<SendEmailPayload> {
  to:          string[];
  subject?:    string;
}

/** Used to drive the ComposePage — 'new' | 'reply' | 'forward' */
export type ComposeMode = 'new' | 'reply' | 'forward';

export interface ComposeContext {
  mode:          ComposeMode;
  replyToMsg?:   EmailDetail;
  forwardMsg?:   EmailDetail;
}

// ── Link payloads ─────────────────────────────────────────────────────────────

export interface LinkRecordPayload {
  model:        string;
  record_id:    number;
  record_name?: string;
}

// ── Account config payload ────────────────────────────────────────────────────

export interface AccountConfigPayload {
  /** Required when creating */
  name?:               string;
  email_address?:      string;
  display_name_field?: string;
  username?:           string;
  password?:           string;
  is_active?:          boolean;
  is_default?:         boolean;
  imap_host?:          string;
  imap_port?:          number;
  imap_use_ssl?:       boolean;
  smtp_host?:          string;
  smtp_port?:          number;
  smtp_use_tls?:       boolean;
}

// ── Sync result (returned by POST /accounts/<id>/sync) ───────────────────────

export interface SyncResult {
  account_id:     number;
  status:         SyncStatus;
  last_sync_date: string | null;
  unread_count:   number;
  per_folder:     Partial<Record<EmailFolder, number>>;
}
