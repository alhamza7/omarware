// ─────────────────────────────────────────────────────────────────────────────
// useEmailForRecord
// ─────────────────────────────────────────────────────────────────────────────
// Loads emails linked to a specific CRM record (customer, ticket, etc.).
// Designed for embedding in CRM detail pages — no dependency on the
// global emailStore.
//
// Usage example (inside a CRM customer page):
//
//   const { messages, isLoading, refresh, totalLinked } =
//     useEmailForRecord('lugal.crm.customer', customer.id);
//
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useEffect, useCallback, useRef } from 'react';
import type { EmailFolder, EmailListItem } from '../../../types/email';
import { getMessagesForRecord } from '../../../services/emailApi';

export interface UseEmailForRecordOptions {
  /** IMAP folder to filter by.  Default: all folders (no folder filter). */
  folder?:    EmailFolder;
  /** Page size.  Default: 20 */
  limit?:     number;
  /** Auto-refresh interval in ms.  Default: 60 000 (1 min).  0 = disabled. */
  pollMs?:    number;
}

export interface UseEmailForRecordResult {
  messages:     EmailListItem[];
  isLoading:    boolean;
  error:        string | null;
  total:        number;
  offset:       number;
  hasMore:      boolean;
  refresh:      () => void;
  loadNextPage: () => void;
  loadPrevPage: () => void;
  setOffset:    (offset: number) => void;
}

/**
 * Loads emails linked to a specific Odoo record.
 *
 * @param model     Odoo model technical name, e.g. 'lugal.crm.customer'
 * @param recordId  Odoo record ID
 * @param options   Optional folder filter, page size, and poll interval
 */
export function useEmailForRecord(
  model:     string,
  recordId:  number,
  options:   UseEmailForRecordOptions = {},
): UseEmailForRecordResult {
  const { folder, limit = 20, pollMs = 60_000 } = options;

  const [messages,  setMessages]  = useState<EmailListItem[]>([]);
  const [total,     setTotal]     = useState(0);
  const [offset,    setOffset]    = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error,     setError]     = useState<string | null>(null);

  // Keep stable refs to avoid stale closure in poll interval
  const offsetRef   = useRef(offset);
  const modelRef    = useRef(model);
  const recordIdRef = useRef(recordId);
  offsetRef.current   = offset;
  modelRef.current    = model;
  recordIdRef.current = recordId;

  const load = useCallback(async (currentOffset: number) => {
    if (!model || !recordId) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await getMessagesForRecord(model, recordId, {
        ...(folder ? { folder } : {}),
        limit,
        offset: currentOffset,
      });
      if (res.success && res.data) {
        setMessages(res.data.items);
        setTotal(res.data.total);
      } else {
        setError(res.error ?? 'Failed to load messages');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected error');
    } finally {
      setIsLoading(false);
    }
  }, [model, recordId, folder, limit]);

  // Initial load and reload when key params change
  useEffect(() => {
    setOffset(0);
    load(0);
  }, [load]);

  // Re-load when offset changes (pagination)
  useEffect(() => {
    load(offset);
  }, [offset, load]);

  // Background polling
  useEffect(() => {
    if (!pollMs) return;
    const id = setInterval(() => load(offsetRef.current), pollMs);
    return () => clearInterval(id);
  }, [pollMs, load]);

  const refresh      = useCallback(() => load(offset), [load, offset]);
  const loadNextPage = useCallback(() => {
    const next = offset + limit;
    if (next < total) setOffset(next);
  }, [offset, limit, total]);
  const loadPrevPage = useCallback(() => {
    setOffset(Math.max(0, offset - limit));
  }, [offset, limit]);

  return {
    messages,
    isLoading,
    error,
    total,
    offset,
    hasMore: offset + limit < total,
    refresh,
    loadNextPage,
    loadPrevPage,
    setOffset,
  };
}

export default useEmailForRecord;
