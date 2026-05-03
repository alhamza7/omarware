// ─────────────────────────────────────────────────────────────────────────────
// Email Zustand Store
// Global state for the email feature.
// All API calls happen in containers/hooks — not here.
// ─────────────────────────────────────────────────────────────────────────────

import { create } from 'zustand';
import type {
  ComposeContext,
  EmailAccount,
  EmailDetail,
  EmailFolder,
  EmailListItem,
} from '../../../types/email';

export interface EmailStore {
  // ── Account ────────────────────────────────────────────────────────────────
  account:         EmailAccount | null;
  isAccountLoaded: boolean;

  // ── Folder & list ──────────────────────────────────────────────────────────
  activeFolder:    EmailFolder;
  messages:        EmailListItem[];
  total:           number;
  offset:          number;
  limit:           number;
  isListLoading:   boolean;
  listError:       string | null;
  searchQuery:     string;

  // ── Selected message (detail view) ────────────────────────────────────────
  selectedMessage: EmailDetail | null;
  isDetailLoading: boolean;
  detailError:     string | null;

  // ── Compose ────────────────────────────────────────────────────────────────
  isComposeOpen:   boolean;
  composeContext:  ComposeContext | null;

  // ── Notifications / unread ─────────────────────────────────────────────────
  unreadCount:     number;
  /** Unread count per folder — drives sidebar badges */
  perFolderCounts: Partial<Record<EmailFolder, number>>;
  isSyncing:       boolean;

  // ── Actions ────────────────────────────────────────────────────────────────
  setAccount:         (a: EmailAccount | null) => void;

  setActiveFolder:    (f: EmailFolder) => void;
  setOffset:          (n: number) => void;

  setMessages:        (msgs: EmailListItem[], total: number, offset: number) => void;
  prependMessage:     (msg: EmailListItem) => void;
  patchMessage:       (id: number, patch: Partial<EmailListItem>) => void;
  removeMessage:      (id: number) => void;

  setListLoading:     (v: boolean) => void;
  setListError:       (e: string | null) => void;
  setSearchQuery:     (q: string) => void;

  setSelectedMessage: (m: EmailDetail | null) => void;
  setDetailLoading:   (v: boolean) => void;
  setDetailError:     (e: string | null) => void;

  openCompose:        (ctx?: ComposeContext) => void;
  closeCompose:       () => void;

  setUnreadCount:     (n: number) => void;
  setPerFolderCounts: (counts: Partial<Record<EmailFolder, number>>) => void;
  setSyncing:         (v: boolean) => void;
}

export const useEmailStore = create<EmailStore>((set) => ({
  // ── Initial state ──────────────────────────────────────────────────────────
  account:          null,
  isAccountLoaded:  false,

  activeFolder:     'inbox',
  messages:         [],
  total:            0,
  offset:           0,
  limit:            50,
  isListLoading:    false,
  listError:        null,
  searchQuery:      '',

  selectedMessage:  null,
  isDetailLoading:  false,
  detailError:      null,

  isComposeOpen:    false,
  composeContext:   null,

  unreadCount:      0,
  perFolderCounts:  {},
  isSyncing:        false,

  // ── Actions ────────────────────────────────────────────────────────────────

  setAccount: (account) => set({ account, isAccountLoaded: true }),

  setActiveFolder: (activeFolder) => set({
    activeFolder,
    messages:        [],
    total:           0,
    offset:          0,
    selectedMessage: null,
    searchQuery:     '',
    listError:       null,
  }),

  /** Set pagination offset (triggers reload in useEmailSync via useEffect). */
  setOffset: (offset) => set({ offset }),

  setMessages: (messages, total, offset) => set({ messages, total, offset }),

  /** Prepend a new message to the top of the list (optimistic send). */
  prependMessage: (msg) =>
    set((s) => ({ messages: [msg, ...s.messages], total: s.total + 1 })),

  /** Apply a partial update to one message in the list and in detail view. */
  patchMessage: (id, patch) =>
    set((s) => ({
      messages: s.messages.map((m) => (m.id === id ? { ...m, ...patch } : m)),
      selectedMessage:
        s.selectedMessage?.id === id
          ? { ...s.selectedMessage, ...patch }
          : s.selectedMessage,
    })),

  /** Remove a message from the list (used after hard-delete if ever needed). */
  removeMessage: (id) =>
    set((s) => ({
      messages:        s.messages.filter((m) => m.id !== id),
      total:           Math.max(0, s.total - 1),
      selectedMessage: s.selectedMessage?.id === id ? null : s.selectedMessage,
    })),

  setListLoading: (isListLoading) => set({ isListLoading }),
  setListError:   (listError)     => set({ listError }),
  setSearchQuery: (searchQuery)   => set({ searchQuery, offset: 0 }),

  setSelectedMessage: (selectedMessage) => set({ selectedMessage }),
  setDetailLoading:   (isDetailLoading) => set({ isDetailLoading }),
  setDetailError:     (detailError)     => set({ detailError }),

  openCompose: (ctx) => set({
    isComposeOpen:  true,
    composeContext: ctx ?? { mode: 'new' },
  }),
  closeCompose: () => set({ isComposeOpen: false, composeContext: null }),

  setUnreadCount:     (unreadCount)    => set({ unreadCount }),
  setPerFolderCounts: (perFolderCounts) => set({ perFolderCounts }),
  setSyncing:         (isSyncing)      => set({ isSyncing }),
}));
