import type { EmailFolder, EmailListItem } from '../../../types/email';
import { formatDistanceToNow } from 'date-fns';
import {
  Star, Paperclip, Link2, RefreshCw, Search, Plus,
  Inbox, Send, FileText, Trash2, MailQuestion,
} from 'lucide-react';
import '../styles/InboxPage.css';

interface FolderConfig {
  key:   EmailFolder;
  label: string;
  icon:  React.ReactNode;
}

const FOLDERS: FolderConfig[] = [
  { key: 'inbox',   label: 'Inbox',   icon: <Inbox   size={16} /> },
  { key: 'sent',    label: 'Sent',    icon: <Send    size={16} /> },
  { key: 'drafts',  label: 'Drafts',  icon: <FileText size={16} /> },
  { key: 'trash',   label: 'Trash',   icon: <Trash2  size={16} /> },
  { key: 'spam',    label: 'Spam',    icon: <MailQuestion size={16} /> },
];

interface InboxPageProps {
  activeFolder:  EmailFolder;
  messages:      EmailListItem[];
  total:         number;
  unreadCount:   number;
  isSyncing:     boolean;
  isLoading:     boolean;
  searchQuery:   string;
  selectedId:    number | null;

  onFolderChange: (f: EmailFolder)  => void;
  onSelect:       (id: number)      => void;
  onSync:         ()                => void;
  onCompose:      ()                => void;
  onSearch:       (q: string)       => void;
  onToggleStar:   (id: number)      => void;
  onDelete:       (id: number)      => void;
  onLoadMore:     ()                => void;
}

/** Pure presentational component for the inbox layout. */
export function InboxPage({
  activeFolder,
  messages,
  total,
  unreadCount,
  isSyncing,
  isLoading,
  searchQuery,
  selectedId,
  onFolderChange,
  onSelect,
  onSync,
  onCompose,
  onSearch,
  onToggleStar,
  onDelete,
  onLoadMore,
}: InboxPageProps) {
  return (
    <div className="inbox-layout">
      {/* ── Sidebar ── */}
      <aside className="inbox-sidebar">
        <div className="sidebar-header">
          <span className="sidebar-logo">NBS Mail</span>
        </div>

        <button className="compose-btn" onClick={onCompose}>
          <Plus size={16} /> Compose
        </button>

        <nav className="folder-nav">
          {FOLDERS.map((f) => (
            <button
              key={f.key}
              className={`folder-item ${activeFolder === f.key ? 'active' : ''}`}
              onClick={() => onFolderChange(f.key)}
            >
              {f.icon}
              <span>{f.label}</span>
              {f.key === 'inbox' && unreadCount > 0 && (
                <span className="badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button
            className={`sync-btn ${isSyncing ? 'spinning' : ''}`}
            onClick={onSync}
            disabled={isSyncing}
            title="Sync inbox"
          >
            <RefreshCw size={15} />
            {isSyncing ? 'Syncing…' : 'Sync'}
          </button>
        </div>
      </aside>

      {/* ── Message list ── */}
      <main className="inbox-main">
        <div className="inbox-toolbar">
          <div className="search-wrap">
            <Search size={15} className="search-icon" />
            <input
              className="search-input"
              placeholder="Search messages…"
              value={searchQuery}
              onChange={(e) => onSearch(e.target.value)}
            />
          </div>
          <span className="total-label">{total} messages</span>
        </div>

        {isLoading ? (
          <div className="list-empty">Loading…</div>
        ) : messages.length === 0 ? (
          <div className="list-empty">No messages in {activeFolder}.</div>
        ) : (
          <ul className="message-list">
            {messages.map((msg) => (
              <MessageRow
                key={msg.id}
                msg={msg}
                isSelected={msg.id === selectedId}
                onSelect={() => onSelect(msg.id)}
                onToggleStar={(e) => { e.stopPropagation(); onToggleStar(msg.id); }}
                onDelete={(e) => { e.stopPropagation(); onDelete(msg.id); }}
              />
            ))}
          </ul>
        )}

        {messages.length < total && (
          <div className="load-more-wrap">
            <button className="load-more-btn" onClick={onLoadMore}>
              Load more ({total - messages.length} remaining)
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

interface MessageRowProps {
  msg:          EmailListItem;
  isSelected:   boolean;
  onSelect:     () => void;
  onToggleStar: (e: React.MouseEvent) => void;
  onDelete:     (e: React.MouseEvent) => void;
}

function MessageRow({ msg, isSelected, onSelect, onToggleStar, onDelete }: MessageRowProps) {
  const dateLabel = msg.date
    ? formatDistanceToNow(new Date(msg.date), { addSuffix: true })
    : '';

  const initials = (msg.from_name || msg.from_address)
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('');

  return (
    <li
      className={`message-row ${!msg.is_read ? 'unread' : ''} ${isSelected ? 'selected' : ''}`}
      onClick={onSelect}
    >
      <div className="msg-avatar">{initials}</div>

      <div className="msg-content">
        <div className="msg-header-row">
          <span className="msg-from">{msg.from_name || msg.from_address}</span>
          <span className="msg-date">{dateLabel}</span>
        </div>
        <div className="msg-subject">{msg.subject}</div>
        <div className="msg-preview">{msg.preview}</div>
      </div>

      <div className="msg-actions">
        {msg.attachment_count > 0 && (
          <Paperclip size={13} className="msg-icon" aria-label="Has attachments" />
        )}
        {(msg.crm_links?.customer || msg.crm_links?.ticket || msg.linked_record) && (
          <Link2 size={13} className="msg-icon linked" aria-label="Linked to CRM record" />
        )}
        <button
          className={`star-btn ${msg.is_starred ? 'starred' : ''}`}
          onClick={onToggleStar}
          title="Star"
        >
          <Star size={14} />
        </button>
        <button className="delete-btn" onClick={onDelete} title="Move to trash">
          <Trash2 size={13} />
        </button>
      </div>
    </li>
  );
}
