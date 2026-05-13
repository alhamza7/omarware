import { useState } from 'react';
import { toast } from 'sonner';
import emailApi from '../../../services/emailApi';
import { ComposePage } from '../pages/ComposePage';
import type { EmailDetail, SendEmailPayload } from '../../../types/email';

interface ComposeContainerProps {
  replyTo?:   EmailDetail | null;
  forwardOf?: EmailDetail | null;
  onClose:    () => void;
}

/**
 * Handles send logic and loading state for the compose modal.
 */
export function ComposeContainer({ replyTo, forwardOf, onClose }: ComposeContainerProps) {
  const [isSending, setIsSending] = useState(false);

  const handleSend = async (payload: SendEmailPayload) => {
    setIsSending(true);
    try {
      let res;
      if (replyTo) {
        res = await emailApi.replyMessage(replyTo.id, payload);
      } else if (forwardOf) {
        res = await emailApi.forwardMessage(forwardOf.id, {
          to:        payload.to,
          subject:   payload.subject,
          body_html: payload.body_html,
        });
      } else {
        res = await emailApi.sendEmail(payload);
      }

      if (res.success) {
        toast.success('Message sent');
        onClose();
      } else {
        toast.error(res.error ?? 'Failed to send message');
      }
    } catch {
      toast.error('Network error while sending');
    } finally {
      setIsSending(false);
    }
  };

  return (
    <ComposePage
      replyTo={replyTo}
      forwardOf={forwardOf}
      isSending={isSending}
      onSend={handleSend}
      onClose={onClose}
    />
  );
}
