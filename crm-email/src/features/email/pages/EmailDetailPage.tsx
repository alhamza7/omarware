import type { EmailDetail } from '../../../types/email';
import { format } from 'date-fns';
import {
  ArrowLeft, Reply, Forward, Star, Trash2, Link2,
  Unlink, Paperclip, ExternalLink,
} from 'lucide-react';
import '../styles/EmailDetailPage.css';

interface EmailDetailPageProps {
  message:          EmailDetail;
  onBack:           () => void;
  onReply:          () => void;
  onForward:        () => void;
  onToggleStar:     () => void;
  onDelete:         () => void;
  onLinkToRecord:   () => void;
  onUnlinkRecord?:  () => void;
}

/** Pure presentational component — email detail / reading pane. */
export function EmailDetailPage({
  message,
  onBack,
  onReply,
  onForward,
  onToggleStar,
  onDelete,
  onLinkToRecord,
  onUnlinkRecord,
}: EmailDetailPageProps) {
  const dateLabel = message.date
    ? format(new Date(message.date), 'PPpp')
    : '';

  const toLabel = message.to_addresses
    .map((a) => a.name ? `${a.name} <${a.email}>` : a.email)
    .join(', ');

  const ccLabel = message.cc_addresses
    .map((a) => a.name ? `${a.name} <${a.email}>` : a.email)
    .join(', ');

  // Build a human-readable linked record label from crm_links or linked_record
  const crmCustomer = message.crm_links?.customer;
  const crmTicket   = message.crm_links?.ticket;
  const linkedLabel =
    crmCustomer ? `Customer: ${crmCustomer.name}` :
    crmTicket   ? `Ticket: ${crmTicket.name}` :
    message.linked_record ? message.linked_record.name :
    null;

  return (
    <div className="detail-layout">
      {/* ── Toolbar ── */}
      <div className="detail-toolbar">
        <button className="icon-btn back-btn" onClick={onBack} aria-label="Back">
          <ArrowLeft size={18} />
        </button>

        <div className="detail-actions">
          <button className="action-btn" onClick={onReply} aria-label="Reply">
            <Reply size={15} /> Reply
          </button>
          <button className="action-btn" onClick={onForward} aria-label="Forward">
            <Forward size={15} /> Forward
          </button>
          <button
            className={`action-btn star-btn ${message.is_starred ? 'starred' : ''}`}
            onClick={onToggleStar}
            aria-label="Star"
          >
            <Star size={15} />
          </button>
          {message.has_link && onUnlinkRecord ? (
            <button className="action-btn unlink-btn" onClick={onUnlinkRecord} aria-label="Remove link">
              <Unlink size={15} /> Unlink
            </button>
          ) : (
            <button className="action-btn link-btn" onClick={onLinkToRecord} aria-label="Link to CRM record">
              <Link2 size={15} /> Link to record
            </button>
          )}
          <button className="action-btn danger-btn" onClick={onDelete} aria-label="Delete">
            <Trash2 size={15} />
          </button>
        </div>
      </div>

      {/* ── Message header ── */}
      <div className="detail-header">
        <h2 className="detail-subject">{message.subject}</h2>

        <div className="detail-meta">
          <div className="meta-row">
            <span className="meta-label">From</span>
            <span className="meta-value">
              {message.from_name
                ? `${message.from_name} <${message.from_address}>`
                : message.from_address}
            </span>
          </div>
          <div className="meta-row">
            <span className="meta-label">To</span>
            <span className="meta-value">{toLabel}</span>
          </div>
          {ccLabel && (
            <div className="meta-row">
              <span className="meta-label">CC</span>
              <span className="meta-value">{ccLabel}</span>
            </div>
          )}
          <div className="meta-row">
            <span className="meta-label">Date</span>
            <span className="meta-value">{dateLabel}</span>
          </div>
          {linkedLabel && (
            <div className="meta-row linked-record-row">
              <span className="meta-label">
                <Link2 size={13} /> Linked
              </span>
              <span className="meta-value linked-badge">
                {linkedLabel}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* ── Body ── */}
      <div className="detail-body">
        {message.body_html ? (
          <div
            className="email-html-body"
            dangerouslySetInnerHTML={{ __html: message.body_html }}
          />
        ) : (
          <pre className="email-text-body">{message.body_text}</pre>
        )}
      </div>

      {/* ── Attachments ── */}
      {message.attachments.length > 0 && (
        <div className="detail-attachments">
          <h4 className="attachments-title">
            <Paperclip size={14} /> Attachments ({message.attachments.length})
          </h4>
          <div className="attachments-list">
            {message.attachments.map((att) => (
              <a
                key={att.id}
                href={att.url}
                target="_blank"
                rel="noopener noreferrer"
                className="attachment-item"
              >
                <Paperclip size={13} />
                <span>{att.name}</span>
                <ExternalLink size={11} />
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
