# FE Prompt — WebSocket Message Deduplication Fix

## Why This is Needed

The backend now publishes every `supply.chat.message.new` event on **two channels**:

1. `supply_chat.<conv_id>` — the conversation channel (for users already subscribed)
2. `supply_user.<uid>` — the personal channel (fallback for race conditions on new conversations)

This guarantees that **every user on every account receives messages immediately**, even if their conversation channel subscription is still pending.

**Side effect:** A user who is already subscribed to the conversation channel will receive the event **twice** — once from each channel. Without deduplication, this causes:
- Duplicate message bubbles in the chat
- Double notification sounds/toasts
- Double badge increment

## What You Must Add in the FE

### 1. In `RealtimeProvider.tsx` — dedup `CHAT_MESSAGE_NEW` by `message_id`

Add a `useRef` set to track recently seen message IDs and skip duplicates:

```typescript
// near the top of RealtimeProvider component
const seenMsgIds = useRef<Set<number>>(new Set());

// inside the CHAT_MESSAGE_NEW handler, as the FIRST thing:
const msgId = raw?.id ?? raw?.message?.id ?? p?.id;
if (msgId != null) {
  if (seenMsgIds.current.has(Number(msgId))) {
    return; // duplicate from personal-channel fallback — skip
  }
  seenMsgIds.current.add(Number(msgId));
  // Optional: clean up old IDs to prevent memory leak
  if (seenMsgIds.current.size > 500) {
    const arr = [...seenMsgIds.current];
    seenMsgIds.current = new Set(arr.slice(-250));
  }
}
```

### 2. In `useSupplyChatBusListener.ts` — dedup `CHAT_MESSAGE_NEW` cache updates

When updating the query cache on receiving a new message, check if the message_id already exists in the current cache before adding:

```typescript
// In the CHAT_MESSAGE_NEW handler inside useSupplyChatBusListener
const msgId = payload?.id;
if (!msgId) return;

// Check if already in cache
const existing = qc.getQueryData<MessagePage>(['crm', 'supply', 'messages', convId]);
const alreadyExists = existing?.pages?.some(page =>
  page.items?.some((m: Message) => m.id === msgId)
);
if (alreadyExists) return; // duplicate — skip cache update
```

### 3. In `useSupplyChatBusListener.ts` — dedup notification badge increments

The notification badge increment should also be guarded:

```typescript
// Before incrementing the badge or playing a sound for CHAT_MESSAGE_NEW,
// check if this message_id was already processed:
const processedMsgIds = useRef<Set<number>>(new Set()); // at hook level

// in the handler:
if (processedMsgIds.current.has(msgId)) return;
processedMsgIds.current.add(msgId);
```

---

## Summary of Changes Needed

| File | Change |
|---|---|
| `RealtimeProvider.tsx` | Add `seenMsgIds` ref; skip duplicate `CHAT_MESSAGE_NEW` by `message_id` |
| `useSupplyChatBusListener.ts` | Guard cache update and badge increment against duplicate `message_id` |

---

## Expected Behaviour After Fix

| Scenario | Before fix | After fix |
|---|---|---|
| Message to existing conversation | Works ✓ | Works ✓ (one event via conv channel, personal copy deduplicated) |
| First message to a NEW conversation | Race condition — sometimes missed | Always delivered ✓ (personal channel fallback) |
| Reconnect after network drop | Sometimes missed | Always delivered ✓ |
| Multi-device (same user, 2 browsers) | Inconsistent | Consistent ✓ |
| Notification sound/toast | Double sound on some accounts | Single sound ✓ (deduplicated) |
