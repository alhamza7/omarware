import { useRef, useState } from 'react';
import type { EmailDetail, SendEmailPayload } from '../../../types/email';
import { X, Paperclip, Send } from 'lucide-react';
import '../styles/ComposePage.css';

interface ComposePageProps {
  /** When set, this is a reply — pre-fills To/Subject */
  replyTo?:     EmailDetail | null;
  /** When set, this is a forward — pre-fills Subject/Body */
  forwardOf?:   EmailDetail | null;
  isSending:    boolean;
  onSend:       (payload: SendEmailPayload) => Promise<void>;
  onClose:      () => void;
}

/** Compose / Reply / Forward modal panel. */
export function ComposePage({
  replyTo,
  forwardOf,
  isSending,
  onSend,
  onClose,
}: ComposePageProps) {
  const defaultTo = replyTo
    ? [replyTo.from_address]
    : [];
  const defaultSubject = replyTo
    ? `Re: ${replyTo.subject}`
    : forwardOf
    ? `Fwd: ${forwardOf.subject}`
    : '';
  const defaultBody = forwardOf
    ? `\n\n---------- Forwarded message ----------\nFrom: ${forwardOf.from_address}\nSubject: ${forwardOf.subject}\n\n${forwardOf.body_text || ''}`
    : replyTo
    ? `\n\nOn ${replyTo.date}, ${replyTo.from_name || replyTo.from_address} wrote:\n${replyTo.body_text ? replyTo.body_text.split('\n').map(l => `> ${l}`).join('\n') : ''}`
    : '';

  const [to,      setTo]      = useState(defaultTo.join(', '));
  const [cc,      setCc]      = useState('');
  const [subject, setSubject] = useState(defaultSubject);
  const [body,    setBody]    = useState(defaultBody);
  const [showCc,  setShowCc]  = useState(false);
  const bodyRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = async () => {
    const toList = to.split(',').map((s) => s.trim()).filter(Boolean);
    if (!toList.length || !subject.trim()) return;

    await onSend({
      to:        toList,
      subject:   subject.trim(),
      body_html: `<div style="white-space:pre-wrap">${body}</div>`,
      body_text: body,
      cc:        cc ? cc.split(',').map((s) => s.trim()).filter(Boolean) : [],
    });
  };

  return (
    <div className="compose-overlay">
      <div className="compose-card">
        {/* Header */}
        <div className="compose-header">
          <span className="compose-title">
            {replyTo ? 'Reply' : forwardOf ? 'Forward' : 'New Message'}
          </span>
          <button className="compose-close" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        {/* Fields */}
        <div className="compose-fields">
          <div className="compose-field">
            <label>To</label>
            <input
              value={to}
              onChange={(e) => setTo(e.target.value)}
              placeholder="recipient@example.com"
              autoFocus
            />
            <button className="cc-toggle" onClick={() => setShowCc(!showCc)}>
              {showCc ? 'Hide CC' : 'CC'}
            </button>
          </div>

          {showCc && (
            <div className="compose-field">
              <label>CC</label>
              <input
                value={cc}
                onChange={(e) => setCc(e.target.value)}
                placeholder="cc@example.com"
              />
            </div>
          )}

          <div className="compose-field">
            <label>Subject</label>
            <input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Subject"
            />
          </div>
        </div>

        {/* Body */}
        <textarea
          ref={bodyRef}
          className="compose-body"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Write your message…"
        />

        {/* Footer */}
        <div className="compose-footer">
          <button className="icon-btn" title="Attach file (coming soon)" disabled>
            <Paperclip size={16} />
          </button>
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={isSending || !to.trim() || !subject.trim()}
          >
            <Send size={15} />
            {isSending ? 'Sending…' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}
