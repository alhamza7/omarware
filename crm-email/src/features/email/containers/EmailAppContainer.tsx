import { useCallback, useState } from 'react';
import { toast } from 'sonner';
import emailApi from '../../../services/emailApi';
import { useEmailStore } from '../store/emailStore';
import { useEmailSync } from '../hooks/useEmailSync';
import { InboxPage } from '../pages/InboxPage';
import { EmailDetailContainer } from './EmailDetailContainer';
import { ComposeContainer } from './ComposeContainer';
import type { EmailFolder } from '../../../types/email';

/**
 * Root container for the email feature.
 * Mounts the sync hook and orchestrates all sub-containers.
 */
export function EmailAppContainer() {
  const {
    activeFolder,
    messages,
    total,
    unreadCount,
    isSyncing,
    isListLoading,
    searchQuery,
    selectedMessage,
    isComposeOpen,
    composeContext,
    setActiveFolder,
    setSelectedMessage,
    setDetailLoading,
    setDetailError,
    patchMessage,
    removeMessage,
    openCompose,
    closeCompose,
    setSearchQuery,
  } = useEmailStore();

  const { loadMessages, triggerSync } = useEmailSync();
  const [searchTimeout, setSearchTimeout] = useState<ReturnType<typeof setTimeout> | null>(null);

  // ── Folder change ────────────────────────────────────────
  const handleFolderChange = useCallback((folder: EmailFolder) => {
    setActiveFolder(folder);
  }, [setActiveFolder]);

  // ── Select message (load detail) ────────────────────────
  const handleSelect = useCallback(async (id: number) => {
    setDetailLoading(true);
    setDetailError(null);
    const res = await emailApi.getMessage(id);
    setDetailLoading(false);
    if (res.success && res.data) {
      setSelectedMessage(res.data);
      // Mark as read in the list
      patchMessage(id, { is_read: true });
    } else {
      setDetailError(res.error ?? 'Failed to load message');
      toast.error('Could not open message');
    }
  }, [patchMessage, setDetailError, setDetailLoading, setSelectedMessage]);

  // ── Toggle star ──────────────────────────────────────────
  const handleToggleStar = useCallback(async (id: number) => {
    const res = await emailApi.toggleStar(id);
    if (res.success && res.data) {
      patchMessage(id, { is_starred: res.data.is_starred });
    }
  }, [patchMessage]);

  // ── Delete (move to trash) ───────────────────────────────
  const handleDelete = useCallback(async (id: number) => {
    const res = await emailApi.deleteMessage(id);
    if (res.success) {
      removeMessage(id);
      toast.success('Moved to trash');
    } else {
      toast.error('Could not delete message');
    }
  }, [removeMessage]);

  // ── Search (debounced) ───────────────────────────────────
  const handleSearch = useCallback((q: string) => {
    setSearchQuery(q);
    if (searchTimeout) clearTimeout(searchTimeout);
    const t = setTimeout(() => loadMessages(activeFolder, q, 0), 350);
    setSearchTimeout(t);
  }, [activeFolder, loadMessages, searchQuery, searchTimeout, setSearchQuery]); // eslint-disable-line

  // ── Load more (pagination) ───────────────────────────────
  const handleLoadMore = useCallback(() => {
    loadMessages(activeFolder, searchQuery, messages.length);
  }, [activeFolder, loadMessages, messages.length, searchQuery]);

  return (
    <>
      <InboxPage
        activeFolder={activeFolder}
        messages={messages}
        total={total}
        unreadCount={unreadCount}
        isSyncing={isSyncing}
        isLoading={isListLoading}
        searchQuery={searchQuery}
        selectedId={selectedMessage?.id ?? null}
        onFolderChange={handleFolderChange}
        onSelect={handleSelect}
        onSync={triggerSync}
        onCompose={() => openCompose()}
        onSearch={handleSearch}
        onToggleStar={handleToggleStar}
        onDelete={handleDelete}
        onLoadMore={handleLoadMore}
      />

      {selectedMessage && (
        <div className="detail-panel">
          <EmailDetailContainer
            message={selectedMessage}
            onClose={() => setSelectedMessage(null)}
          />
        </div>
      )}

      {isComposeOpen && (
        <ComposeContainer
          replyTo={composeContext?.replyToMsg ?? null}
          forwardOf={composeContext?.forwardMsg ?? null}
          onClose={closeCompose}
        />
      )}
    </>
  );
}
