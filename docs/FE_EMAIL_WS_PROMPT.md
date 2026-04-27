# FE Prompt — Real-time Email WebSocket Notifications

## What needs to change

The backend sends a **`crm.email.message.new`** event on the `supply_user.<uid>` WebSocket channel every time a new unread inbox email is created (via IMAP IDLE → `action_sync()`). The frontend needs to **listen for this event in `RealtimeProvider.tsx`** and update the email notification state.

---

## WebSocket event payload

```typescript
// Event type: 'crm.email.message.new'
// Channel:    supply_user.<uid>   (already subscribed for chat notifications)
interface EmailMessageNewPayload {
  message_id:   number;
  account_id:   number;
  subject:      string;
  from_name:    string;
  from_address: string;
  received_at:  string | null;  // ISO 8601 +03:00, e.g. "2026-04-25T11:30:00+03:00"
}
```

---

## Changes required in `RealtimeProvider.tsx`

In the section that handles bus events (inside the `onmessage` / event handler), add a branch for `crm.email.message.new` alongside the existing `CHAT_MESSAGE_NEW` handler:

```typescript
// ── New email (IMAP IDLE push) ───────────────────────────────────────────
if (type === 'crm.email.message.new') {
  const p = payload as EmailMessageNewPayload | undefined;
  if (!p) return;

  // 1. Invalidate the email notification query so the badge count refreshes
  void qc.invalidateQueries({ queryKey: ['crm', 'email', 'notifications'] });
  void qc.invalidateQueries({ queryKey: ['crm', 'email', 'unread'] });

  // 2. Optimistically increment the email unread badge (if you track it in a store)
  //    e.g. useUIStore.getState().incrementEmailUnread();

  // 3. Play notification sound (same as chat new message)
  playNotificationSound();

  // 4. Show a toast notification
  toast(`📧 ${p.from_name || p.from_address}`, {
    description: p.subject,
    duration: 4000,
  });

  return;
}
```

---

## Where to add the handler

Inside `RealtimeProvider.tsx`, in the `useEffect` that sets up the bus listener, find the block:

```typescript
if (type === BUS_EVENTS.CHAT_MESSAGE_NEW) {
  // ...existing chat message handler...
}
```

Add the email handler **after** the last `if (type === ...)` block in the same switch/if chain.

---

## Query key conventions

Make sure the query keys match what the app uses for email data. Common patterns:

```typescript
// Invalidate all email-related queries when a new email arrives:
void qc.invalidateQueries({ queryKey: ['crm', 'email'] });

// Or more specific if needed:
void qc.invalidateQueries({ queryKey: ['crm', 'notifications'] }); // unified badge
void qc.invalidateQueries({ queryKey: ['email', 'mailbox', 'inbox'] });
```

Adjust these to match the actual `queryKey` arrays used in your email API hooks.

---

## No changes needed to the subscription

The `supply_user.<uid>` channel is **already subscribed** (used for chat notifications). The `crm.email.message.new` event arrives on the same channel — no new subscription is needed.

---

## Summary checklist

- [ ] Add `crm.email.message.new` handler in `RealtimeProvider.tsx`
- [ ] Call `qc.invalidateQueries` for email inbox / notification queries
- [ ] Play notification sound
- [ ] Show toast with sender + subject
- [ ] (Optional) Optimistically increment email unread badge in store
