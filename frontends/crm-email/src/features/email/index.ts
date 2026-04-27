// ─────────────────────────────────────────────────────────────────────────────
// lugal_email feature — public exports
// Import from here in CRM pages to use the email system.
// ─────────────────────────────────────────────────────────────────────────────

// Hooks
export { useEmailForRecord }       from './hooks/useEmailForRecord';
export { useEmailNotifications }   from './hooks/useEmailNotifications';
export { useEmailSync }            from './hooks/useEmailSync';

// Store
export { useEmailStore }           from './store/emailStore';

// Types (re-export for convenience)
export type {
  UseEmailForRecordOptions,
  UseEmailForRecordResult,
}                                  from './hooks/useEmailForRecord';
export type { UseEmailNotificationsResult } from './hooks/useEmailNotifications';

// Domain types
export type {
  EmailAccount,
  EmailListItem,
  EmailDetail,
  EmailNotifications,
  EmailFolder,
  SyncStatus,
  AccountConfigPayload,
  SendEmailPayload,
  ComposeContext,
}                                  from '../../types/email';
