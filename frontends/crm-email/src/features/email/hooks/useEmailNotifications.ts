// ─────────────────────────────────────────────────────────────────────────────
// useEmailNotifications
// ─────────────────────────────────────────────────────────────────────────────
// Lightweight hook for the top-bar notification badge.
// Can be used independently in the CRM sidebar / navbar without importing
// the full email store — useful when the email app is not the active view.
//
// Usage:
//   const { inboxCount, syncStatus, isConfigured } = useEmailNotifications();
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useEffect, useCallback } from 'react';
import type { EmailFolder, SyncStatus } from '../../../types/email';
import { getNotifications } from '../../../services/emailApi';

const DEFAULT_POLL_MS = 60_000;

export interface UseEmailNotificationsResult {
  inboxCount:        number;
  perFolder:         Partial<Record<EmailFolder, number>>;
  isConfigured:      boolean;
  syncStatus:        SyncStatus | null;
  lastSyncDate:      string | null;
  syncErrorMessage:  string | null;
  isLoading:         boolean;
  refresh:           () => void;
}

/**
 * Polls /api/lugal/email/notifications and exposes unread counts.
 *
 * @param pollMs  Polling interval in ms.  Default: 60 000.  0 = disabled.
 */
export function useEmailNotifications(pollMs = DEFAULT_POLL_MS): UseEmailNotificationsResult {
  const [inboxCount,       setInboxCount]       = useState(0);
  const [perFolder,        setPerFolder]        = useState<Partial<Record<EmailFolder, number>>>({});
  const [isConfigured,     setIsConfigured]     = useState(false);
  const [syncStatus,       setSyncStatus]       = useState<SyncStatus | null>(null);
  const [lastSyncDate,     setLastSyncDate]     = useState<string | null>(null);
  const [syncErrorMessage, setSyncErrorMessage] = useState<string | null>(null);
  const [isLoading,        setIsLoading]        = useState(false);

  const fetch = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await getNotifications();
      if (res.success && res.data) {
        const d = res.data;
        setInboxCount(d.inbox);
        setPerFolder(d.per_folder ?? {});
        setIsConfigured(d.account_configured);
        setSyncStatus(d.sync_status);
        setLastSyncDate(d.last_sync_date);
        setSyncErrorMessage(d.error_message);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => { fetch(); }, [fetch]);

  // Polling
  useEffect(() => {
    if (!pollMs) return;
    const id = setInterval(fetch, pollMs);
    return () => clearInterval(id);
  }, [fetch, pollMs]);

  return {
    inboxCount,
    perFolder,
    isConfigured,
    syncStatus,
    lastSyncDate,
    syncErrorMessage,
    isLoading,
    refresh: fetch,
  };
}

export default useEmailNotifications;
