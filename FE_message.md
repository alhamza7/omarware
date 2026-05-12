# FE Message - Email + WebSocket Backend Contract

## 2026-05-12 Backend Fixes

### 1. WebSocket/session lifetime

Backend now keeps the Odoo WebSocket session bridge valid for one week instead of advertising/using a 1-hour session hint.

What changed:
- `POST /api/crm/ws/session` now returns `expires_in: 604800` and sets `session_id` cookie `Max-Age=604800`.
- `lugal_ws_migration` sets `sessions.max_inactivity_seconds=604800`.
- `odoo_simple.conf` sets `websocket_keep_alive_timeout=604800`.
- Logout/user-switch still closes stale sockets through the existing `session.reconnect_required` / `4001` path.

Why the old behavior failed:
- The previous WS bridge returned `expires_in=3600` and cookie/session hints were shorter than the desired inactive-tab lifetime.
- Background tabs can miss timer-driven refresh/reconnect work, so after 1-2 hours a socket could become stale even while normal FE logs looked current.
- Odoo also has a server-side forced WebSocket keep-alive timeout; it is now one week instead of one day.

FE requirement:
- Keep using `/api/crm/ws/session` before opening `/websocket`.
- Treat close code `4001` as session expired/logged out and re-run the session bridge if JWT is still valid.
- Treat close code `4002` as transient network/keepalive and reconnect with backoff.
- Do not intentionally stop/recreate the WS just because a tab is inactive; only close on logout or explicit user switch.
- When the FE receives `supply.chat.resubscribe` on `supply_user.<uid>`, immediately refresh/resubscribe bus channels. This now fires both when a new conversation is created and when a user is added to an existing group.
- If the FE still uses `/api/crm/supply/chat/bus_channels` for a polling fallback, it now returns `supply_chat.<id>`, `supply_user.<uid>`, `supply_stories`, and `supply_session.<sid>` for parity with WebSocket subscriptions.

### 2. Email list filters for `GET /api/lugal/email/sync`

`GET /api/lugal/email/sync` is a list alias for `messages_list`, so all params below also work on `/api/lugal/email/messages` and `/api/lugal/email/mailbox/<folder>`.

| Param | Accepted aliases | Backend behavior |
|-------|------------------|------------------|
| Unread | `filter_unread=true`, `unread=1` | Returns only `is_read === false` rows. Also filters `thread_messages` when `include_thread=1`, so read rows do not leak into unread responses. |
| Starred | `starred=1`, `filter_starred=true` | Returns only `is_starred === true`. |
| Flagged | `flagged=1`, `filter_flagged=true` | Returns only `is_flagged === true` (IMAP `\\Flagged`). This is intentionally separate from `is_starred`. |
| Important | `important=1`, `filter_important=true` | Returns only `is_important === true`. |
| Has attachments | `has_attachments=1`, `filter_has_attachment=true`, `filter_has_attachments=true` | Returns only messages with linked `ir.attachment` rows. |
| Mentioned | `mentioned=1`, `filter_mentioned=true` | Returns only `is_mentioned === true`. |
| Sent to me | `sent_to_me=1`, `filter_sent_to_me=true` | Matches current user/account email addresses in `to_addresses`. |

Sent/outbox status:
- Notification polling payloads now include `recently_sent[].smtp_status` (`pending` | `delivered` | `failed`) alongside `smtp_delivered` and `smtp_error`.
- Use `smtp_status === "pending"` for outbox/sending UI, `delivered` for sent, and `failed` for retry/error display.

Example unread request:

```http
GET /api/lugal/email/sync?account_id=4&folder=inbox&filter_unread=true&include_thread=true&limit=100&offset=0
```

Expected invariant for this request:
- Every top-level `data.items[]` row has `is_read: false`.
- Every nested `thread_messages[]` row also has `is_read: false`.

Example flagged request:

```http
GET /api/lugal/email/sync?account_id=4&folder=inbox&filter_flagged=true&limit=100&offset=0
```

### 3. Arabic / RTL compose support

Backend accepts and returns `written_in_arabic: boolean` on `lugal.email.message` payloads.

Supported write endpoints:
- `POST /api/lugal/email/send`
- `POST /api/lugal/email/messages/<id>/reply`
- `POST /api/lugal/email/messages/<id>/reply_all`
- `POST /api/lugal/email/messages/<id>/forward`
- `POST /api/lugal/email/drafts`
- `PUT/PATCH /api/lugal/email/drafts/<id>`
- `POST /api/lugal/email/drafts/<id>/send`

Response payloads:
- `_message_to_dict(...)` now includes `written_in_arabic` for list/detail/sent/draft/reply responses.
- WebSocket email previews also include `message_data.written_in_arabic`.

FE behavior:
- When composing Arabic mail, send `written_in_arabic: true` with the body.
- When rendering any message where `written_in_arabic === true`, render body containers with RTL direction/alignment, e.g. `dir="rtl"`, `text-align: right`, Arabic-capable font, and do not force LTR wrappers inside the message body.
- When false/missing, keep existing LTR behavior.

Example send body:

```json
{
  "account_id": 4,
  "to": ["customer@example.com"],
  "subject": "مرحبا",
  "body_html": "<p>مرحبا، هذا اختبار</p>",
  "body_text": "مرحبا، هذا اختبار",
  "written_in_arabic": true
}
```
