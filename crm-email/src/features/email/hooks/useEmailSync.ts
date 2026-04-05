// ─────────────────────────────────────────────────────────────────────────────
// useEmailSync
// ─────────────────────────────────────────────────────────────────────────────
// Orchestrates inbox loading, IMAP sync, and background polling.
// Mount once at the root of the email feature (EmailAppContainer).
// ─────────────────────────────────────────────────────────────────────────────

import { useCallback, useEffect, useRef } from 'react';
import { toast } from 'sonner';
import emailApi from '../../../services/emailApi';
import { useEmailStore } from '../store/emailStore';
import type { EmailFolder } from '../../../types/email';

const NOTIFICATION_POLL_MS = 60_000; // background badge update every 60 s

export function useEmailSync() {
  const {
    account,
    activeFolder,
    limit,
    offset,
    searchQuery,
    setAccount,
    setMessages,
    setListLoading,
    setListError,
    setUnreadCount,
    setPerFolderCounts,
    setSyncing,
  } = useEmailStore();

  const pollTimer    = useRef<ReturnType<typeof setInterval> | null>(null);
  // Stable refs to avoid stale captures in intervals
  const activeFolderRef = useRef(activeFolder);
  activeFolderRef.current = activeFolder;

  /** Load accounts once on mount (pick first / default for backward compat). */
  const loadAccount = useCallback(async () => {
    try {
      const res = await emailApi.listAccounts();
      if (res.success && res.data && res.data.length > 0) {
        const def = res.data.find(a => a.is_default) ?? res.data[0];
        setAccount(def);
      }
    } catch {
      // non-fatal — user may not have configured an account yet
    }
  }, [setAccount]);

  /**
   * Load the message list for a folder.
   *
   * @param folder   target folder (defaults to activeFolder)
   * @param search   search query override
   * @param page     offset override (used when paginating)
   */
  const loadMessages = useCallback(
    async (
      folder: EmailFolder,
      search?: string,
      page?:   number,
    ) => {
      setListLoading(true);
      setListError(null);
      try {
        const res = await emailApi.listMessages({
          folder,
          limit,
          offset:  page ?? offset,
          query:   search ?? searchQuery,
        });
        if (res.success && res.data) {
          setMessages(res.data.items, res.data.total, res.data.offset);
          setUnreadCount(res.data.unread_count);
          setPerFolderCounts(res.data.per_folder);
        } else {
          setListError(res.error ?? 'Failed to load messages');
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Network error';
        setListError(msg);
      } finally {
        setListLoading(false);
      }
    },
    // offset is intentionally excluded — callers pass it explicitly via `page`
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [limit, searchQuery, setListLoading, setListError, setMessages, setUnreadCount, setPerFolderCounts],
  );

  /** Trigger a manual IMAP sync then refresh the current folder. */
  const triggerSync = useCallback(async () => {
    if (!account) {
      toast.error('Configure your email account first');
      return;
    }
    setSyncing(true);
    try {
      const res = await emailApi.syncAccount(account.id);
      if (res.success && res.data) {
        setUnreadCount(res.data.unread_count);
        setPerFolderCounts(res.data.per_folder);
        toast.success('Inbox synced');
        await loadMessages(activeFolderRef.current, undefined, 0);
      } else {
        toast.error(res.error ?? 'Sync failed');
      }
    } catch {
      toast.error('Sync failed — check your connection');
    } finally {
      setSyncing(false);
    }
  }, [account, loadMessages, setSyncing, setUnreadCount, setPerFolderCounts]);

  /** Background notification poll — updates badge only, no full list reload. */
  const pollNotifications = useCallback(async () => {
    try {
      const res = await emailApi.getNotifications();
      if (res.success && res.data) {
        setUnreadCount(res.data.inbox);
        setPerFolderCounts(res.data.per_folder);
      }
    } catch {
      // silent — polling failures shouldn't disrupt the UI
    }
  }, [setUnreadCount, setPerFolderCounts]);

  // ── Effects ──────────────────────────────────────────────────────────────

  // Load account on first render
  useEffect(() => { loadAccount(); }, [loadAccount]);

  // Reload messages when folder or search changes (reset to page 0)
  useEffect(() => {
    loadMessages(activeFolder, searchQuery, 0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeFolder, searchQuery]);

  // When offset changes (user paginates), reload the current page
  useEffect(() => {
    loadMessages(activeFolder, searchQuery, offset);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offset]);

  // Start background notification polling
  useEffect(() => {
    pollTimer.current = setInterval(pollNotifications, NOTIFICATION_POLL_MS);
    return () => {
      if (pollTimer.current) clearInterval(pollTimer.current);
    };
  }, [pollNotifications]);

  return { loadMessages, triggerSync };
}
