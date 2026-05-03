import { useCallback } from 'react';
import { toast } from 'sonner';
import emailApi from '../../../services/emailApi';
import { useEmailStore } from '../store/emailStore';
import { EmailDetailPage } from '../pages/EmailDetailPage';
import type { EmailDetail } from '../../../types/email';

interface EmailDetailContainerProps {
  message: EmailDetail;
  onClose: () => void;
}

/**
 * Handles all business logic for the email detail view:
 * reply, forward, star, delete, link/unlink to CRM record.
 */
export function EmailDetailContainer({ message, onClose }: EmailDetailContainerProps) {
  const { patchMessage, removeMessage, openCompose } = useEmailStore();

  // ── Reply ─────────────────────────────────────────────────────────────────
  const handleReply = useCallback(() => {
    openCompose({ mode: 'reply', replyToMsg: message });
  }, [message, openCompose]);

  // ── Forward ───────────────────────────────────────────────────────────────
  const handleForward = useCallback(() => {
    openCompose({ mode: 'forward', forwardMsg: message });
  }, [message, openCompose]);

  // ── Toggle star ───────────────────────────────────────────────────────────
  const handleToggleStar = useCallback(async () => {
    const res = await emailApi.toggleStar(message.id);
    if (res.success && res.data) {
      patchMessage(message.id, { is_starred: res.data.is_starred });
    }
  }, [message.id, patchMessage]);

  // ── Delete (move to trash) ────────────────────────────────────────────────
  const handleDelete = useCallback(async () => {
    const res = await emailApi.deleteMessage(message.id);
    if (res.success) {
      removeMessage(message.id);
      toast.success('Moved to trash');
      onClose();
    } else {
      toast.error('Could not delete message');
    }
  }, [message.id, onClose, removeMessage]);

  // ── Link to CRM record ────────────────────────────────────────────────────
  const handleLinkToRecord = useCallback(() => {
    const model = window.prompt(
      'Enter model (e.g. lugal.crm.customer or lugal.crm.ticket):'
    );
    if (!model) return;
    const recordIdStr = window.prompt('Enter record ID:');
    if (!recordIdStr) return;
    const recordId = parseInt(recordIdStr, 10);
    if (isNaN(recordId)) { toast.error('Invalid ID'); return; }

    emailApi.linkToRecord(message.id, { model, record_id: recordId }).then((res) => {
      if (res.success && res.data) {
        const linked = res.data.linked;
        // Patch crm_links for immediate UI update
        const currentCrmLinks = message.crm_links ?? { customer: null, ticket: null };
        patchMessage(message.id, {
          has_link: true,
          linked_record: { model: linked.model, id: linked.id, name: linked.name },
          crm_links: {
            customer: model === 'lugal.crm.customer'
              ? { id: linked.id, name: linked.name }
              : currentCrmLinks.customer,
            ticket: model === 'lugal.crm.ticket'
              ? { id: linked.id, name: linked.name }
              : currentCrmLinks.ticket,
          },
        });
        toast.success(`Linked to ${linked.name}`);
      } else {
        toast.error(res.error ?? 'Link failed');
      }
    });
  }, [message, patchMessage]);

  // ── Unlink record ─────────────────────────────────────────────────────────
  const handleUnlinkRecord = useCallback(async () => {
    const res = await emailApi.unlinkRecord(message.id);
    if (res.success) {
      patchMessage(message.id, {
        has_link:       false,
        linked_record:  null,
        crm_links:      { customer: null, ticket: null },
      });
      toast.success('Link removed');
    } else {
      toast.error(res.error ?? 'Could not remove link');
    }
  }, [message.id, patchMessage]);

  return (
    <EmailDetailPage
      message={message}
      onBack={onClose}
      onReply={handleReply}
      onForward={handleForward}
      onToggleStar={handleToggleStar}
      onDelete={handleDelete}
      onLinkToRecord={handleLinkToRecord}
      onUnlinkRecord={handleUnlinkRecord}
    />
  );
}
