# Issue Tracker: `is_read` / `read_at` / `recipient_read_at` — Sent Folder

> **Status:** ❌ UNRESOLVED — Multiple agents failed to produce a working end-to-end fix  
> **Agents that attempted this:** Sonnet 4.6, GPT-5.5, and others  
> **Last updated:** May 16, 2026  
> **Primary files involved:**
> - `addons/lugal_email/models/email_message.py`
> - `addons/lugal_email/models/email_account.py`
> - `addons/lugal_email/controllers/email_controller.py`
> - `addons/lugal_email/controllers/crm_email_controller.py`

---

## 1. What We Are Trying to Achieve

In the **Sent** folder, these three fields on `lugal.email.message` should behave as follows:

| Field | Desired Behaviour |
|---|---|
| `is_read` | `false` until the **recipient** actually opens the email. The sender viewing their own sent copy must NOT set this to `true`. |
| `read_at` | `null` until confirmed the recipient read the message. Should never equal the delivery/send timestamp. |
| `recipient_read_at` | Set only when an MDN (read receipt) arrives from the recipient's mail client. |

**The goal:** A sender looking at their sent folder should see `is_read=false` and `read_at=null` until there is confirmed evidence the recipient opened the email (either via internal propagation or MDN).

---

## 2. What Is Actually Happening (The Bug)

When a user **sends** an email and then opens their **Sent** folder in the API response:

- `is_read` is `true` immediately (or becomes `true` as soon as they view the sent folder)
- `read_at` equals the send/delivery timestamp — as if the recipient "read" it the moment it was sent
- `recipient_read_at` is mostly `null` (the MDN path is separate and works partially)

The net result: **The sent folder always shows all messages as "read" with a read_at timestamp that is just the send time.** There is no way for a user to know if the actual recipient ever opened the email.

---

## 3. Root Cause Analysis — Bugs Identified

Nine separate overlapping bugs were found across multiple code-review sessions:

---

### Bug A — IMAP sync stamping `read_at` with the email delivery date

**Location:** `email_account.py` → `_upsert_inbox_message()`

```python
# WRONG (original code):
if is_read:
    vals['read_at'] = dt   # dt = parsed Date: header (delivery time, NOT read time)
```

Any message arriving on IMAP already with `\Seen` flag got `read_at = delivery_timestamp`.
For sent messages, IMAP marks them `\Seen` immediately (the sender "saw" their outbox).

**Proposed fix:** Remove the `vals['read_at'] = dt` line entirely. `read_at` must only be set when the user explicitly opens the mail inside the Lugal app.

**Status:** Code was changed but the bug persists through other paths (see Bug H).

---

### Bug B — Model `create()` auto-stamping `read_at` during IMAP sync

**Location:** `email_message.py` → `create()`

```python
# WRONG (auto-stamps during sync):
if vals.get('is_read') and not vals.get('read_at'):
    vals['read_at'] = now
```

Even during IMAP sync, if a message was created with `is_read=True` (from `\Seen` IMAP flag), the model's `create()` would automatically add `read_at=now`.

**Proposed fix:** Added `lugal_imap_sync=True` context flag. All `_upsert_inbox_message` calls use `.with_context(lugal_imap_sync=True)`. The `create()` and `write()` overrides skip auto-stamping when this context flag is set.

**Status:** Context flag was added to the code. But the flag is not consistently applied in all code paths (e.g. `_sync_sent_folder` at line ~1648 does NOT use this context).

---

### Bug C — Send endpoints create the sent copy with `is_read=True`

**Location:** `email_controller.py` → `compose_send()`, `reply_email()`, `forward_email()`, `draft_to_sent()`

```python
# WRONG:
{'folder': 'sent', 'is_read': True, ...}
```

When the user sends an email, the local "sent copy" is created with `is_read=True`. This makes it appear as "read by recipient" immediately.

**Proposed fix:** Remove `'is_read': True` from all sent-message creation calls. Sent messages should start with `is_read=False`.

**Status:** Changed in some send paths but requires verification across ALL four send endpoints.

---

### Bug D — No model-level guard on sent rows

**Location:** `email_message.py` → `write()`

Without a guard, any `write({'is_read': True})` on a sent message updates `is_read`/`read_at`, reflecting the sender's own action rather than the recipient's.

**Proposed fix:** Add `_is_sent_folder_value()` check in `create()` and `write()`. Strip `is_read`/`read_at` from writes to sent-folder rows unless `context['lugal_recipient_read'] = True`.

```python
def write(self, vals):
    allow_recipient_read = bool(self.env.context.get('lugal_recipient_read'))
    read_fields = {'is_read', 'read_at'} & set(vals)
    if read_fields and not allow_recipient_read:
        sent_records = self.filtered(lambda rec: _is_sent_folder_value(rec.folder))
        if sent_records:
            # strip is_read/read_at for sent rows
            ...
```

**Status:** Guard was implemented in the code (visible in current `email_message.py`). BUT the guard only fires if `folder` is already set on the record. Race condition: during `create()`, the `folder` field might not be set yet when the guard runs.

---

### Bug E — Controller `toggle_read` and PATCH directly update sent messages

**Location:** `email_controller.py` → `toggle_read()`, `update_message()`

When the sender clicks "Mark as Read" on their own sent message (or the message is auto-marked when they open it), the controller directly sets `is_read=True` and stamps `read_at=now`.

**Proposed fix:** Add `_is_sent_folder()` helper. For sent messages, push IMAP `\Seen` flag (cosmetic) but do NOT modify DB `is_read` or `read_at`.

**Status:** `_is_sent_folder()` helper exists in the code. But the message detail endpoint (`GET /messages/<id>`) also auto-marks as read when fetched. That path doesn't always check if it's a sent folder.

---

### Bug F — No propagation from inbox-read to sender's sent copy

**Problem:** When the **recipient** marks their inbox copy as read inside Lugal (internal user), the sender's sent copy is never updated.

**Proposed fix:** `_propagate_read_to_sent_copies()` helper — called after every inbox read action. Finds sent copies by `message_id` and updates them with `lugal_recipient_read=True` context.

```python
def _propagate_read_to_sent_copies(env, message_id, read_at):
    sent_copies = env['lugal.email.message'].sudo().search([
        ('message_id', '=', message_id),
        ('folder', '=', 'sent'),
        ('is_read', '=', False),
    ])
    sent_copies.with_context(lugal_recipient_read=True).write({
        'is_read': True,
        'read_at': read_at,
    })
```

**Status:** Function exists in the code. But it only works when BOTH sender and recipient are on the same Lugal system. For external recipients (Gmail/Outlook users) this path is dead — only MDN can trigger it. MDN requires `request_read_receipt=True` to have been set when sending.

---

### Bug G — MDN handler didn't update `is_read`/`read_at`

**Location:** `email_account.py` → `_upsert_inbox_message()` MDN section

```python
# OLD (incomplete):
_sent.write({'recipient_read_at': _read_ts})

# CORRECT:
_sent.with_context(lugal_recipient_read=True).write({
    'recipient_read_at': _read_ts,
    'is_read':           True,
    'read_at':           _read_ts,
})
```

**Status:** Fixed in current code. MDN path appears correct.

---

### Bug H — IMAP `\Seen` flag applied to sent folder during sync

**Location:** `email_account.py` → `_upsert_inbox_message()`

When syncing the Sent IMAP folder, `_parse_flags_from_fetch_response()` returns `is_read=True` for messages with `\Seen` (which is ALL of them — the sender implicitly "saw" their outbox). This sets `is_read=True` on every sync, undoing any correct `is_read=False` state.

**Proposed fix:**
```python
is_read = self._parse_flags_from_fetch_response(flags_meta)
# For sent folder: \Seen means SENDER viewed their copy — not RECIPIENT read.
if folder_key == 'sent':
    is_read = False
```

**Status:** This reset is in the code. However, the `_sync_sent_folder()` method at line ~1648 is a SEPARATE code path that creates rows directly — it may bypass this reset.

---

### Bug I — `_sync_sent_folder()` creates rows with `is_read=True`

**Location:** `email_account.py` → `_sync_sent_folder()`

```python
# Still present in code (line ~1659):
Msg.create({
    ...
    'is_read': True,
    ...
})
```

The model `create()` guard SHOULD strip this (since `lugal_recipient_read` is not in context and `_is_sent_folder_value('sent')` returns True). But this guard fires AFTER `create()` receives the vals — need to verify the guard catches it before the DB insert.

**Status:** Theoretically safe via model guard, but NOT explicitly verified to work end-to-end.

---

## 4. Context Flags — How They Are Supposed to Work

| Context Key | Set By | Effect |
|---|---|---|
| `lugal_imap_sync=True` | `_upsert_inbox_message()` | Disables auto-stamping of `read_at` in `create()` and `write()` during IMAP import |
| `lugal_recipient_read=True` | `_propagate_read_to_sent_copies()`, MDN handler | Bypasses the sent-folder guard — allows writing `is_read`/`read_at` on sent rows |

**The problem with context flags:** They require perfect discipline across EVERY code path that touches `is_read`/`read_at`. Missing a single call-site without the flag means the guard is bypassed in one direction or enforced incorrectly in another.

---

## 5. The Intended Architecture (What Should Work)

```
OUTBOUND (Sender's perspective)
────────────────────────────────
1. Sender sends email
   → DB sent row created: is_read=False, read_at=NULL
   → IMAP APPEND to Sent folder (\Seen flag set to prevent "new mail" badge in webmail)
   → DB is NOT affected by the IMAP \Seen flag for sent rows

2. [IF recipient is internal Lugal user]
   → Recipient opens email in inbox
   → Their inbox copy: is_read=True, read_at=NOW
   → _propagate_read_to_sent_copies() called
   → Sender's sent copy updated: is_read=True, read_at=NOW (via lugal_recipient_read context)

3. [IF MDN was requested and recipient's client sends it]
   → MDN arrives in sender's inbox
   → _upsert_inbox_message() detects multipart/report
   → Finds sent row by Original-Message-ID
   → Writes: recipient_read_at, is_read=True, read_at (via lugal_recipient_read context)

4. [IF no MDN and external recipient]
   → sent copy stays: is_read=False, read_at=NULL FOREVER
   → This is CORRECT — we genuinely don't know if they read it
```

---

## 6. What Multiple Agents Attempted

### Attempt 1 (earliest sessions)
- Added `recipient_read_at` field
- Added partial guard in `write()`
- **Failed because:** Guard was incomplete — didn't cover `create()`. Also `_sync_sent_folder` still passed `is_read=True`.

### Attempt 2
- Added `lugal_imap_sync` context flag
- Added `_is_sent_folder()` helper to controllers
- Added `_propagate_read_to_sent_copies()`
- **Failed because:** Message detail endpoint (`GET /messages/<id>`) auto-reads the message without checking if it's a sent folder. Sent messages viewed by the sender still got `read_at` stamped.

### Attempt 3 (GPT-5.5)
- Tried to handle this at the controller level only
- Added checks in `toggle_read` and PATCH
- **Failed because:** The model-level `write()` guard was too aggressive — it was blocking legitimate recipient-read updates because the `lugal_recipient_read` context was not being passed through in all paths.

### Attempt 4
- Direct SQL bypass for setting `is_read`/`read_at` on sent rows
- **Failed because:** Bypasses Odoo ORM cache — causes stale reads and inconsistent behaviour. Also doesn't survive restarts cleanly.

### Attempt 5 (most recent)
- Comprehensive multi-bug fix as documented in sections 3A–3I above
- Code changes are IN the codebase right now
- **Current status unknown** — the guard and context flags are implemented but the end-to-end flow (sender sees is_read=false until recipient opens) has NOT been confirmed working

---

## 7. What Still Needs to Be Verified / Fixed

### HIGH PRIORITY

1. **Message detail auto-read for sent folder**
   - `GET /api/lugal/email/messages/<id>` marks the message as read when fetched
   - This happens at: `email_controller.py` → `message_detail()` → the line that calls `msg.write({'is_read': True, 'read_at': read_at})`
   - This MUST check `_is_sent_folder(msg.folder)` and skip the write for sent messages
   - **Verify this check exists and is actually working**

2. **`_sync_sent_folder()` bypasses the model guard**
   - At `email_account.py` line ~1648: `Msg.create({..., 'is_read': True, ...})`
   - The model guard SHOULD strip it — but needs explicit end-to-end test
   - If `Msg` here uses `with_context(lugal_imap_sync=True)`, the guard path is different from `lugal_recipient_read`
   - Trace: `_sync_sent_folder` → what context is on `Msg`? → does `create()` guard fire for sent rows WITHOUT `lugal_recipient_read`?

3. **CRM email controller paths not covered**
   - `crm_email_controller.py` has its own message detail endpoint
   - Does it also auto-read sent messages? Does it call `_propagate_read_to_sent_copies`?

### MEDIUM PRIORITY

4. **Initial state on first sync**
   - First time a user sets up their account, ALL historical sent messages get `is_read=False`
   - This is correct behavior, but UX may be confusing (thousands of "unread" sent messages)
   - Consider: sent folder should not show unread badge / unread count

5. **External recipients — user expectation**
   - If the recipient uses Gmail/Outlook and didn't request MDN, `is_read` will stay `false` forever
   - FE should show this as "Delivered, not confirmed read" not "Unread"

---

## 8. Files and Key Line References

| File | Key Location | Issue |
|---|---|---|
| `email_message.py` | `create()` override | Must NOT auto-stamp `read_at` for sent rows (guard at line ~175) |
| `email_message.py` | `write()` override | Must strip `is_read`/`read_at` for sent rows without `lugal_recipient_read` (guard at line ~195) |
| `email_account.py` | `_upsert_inbox_message()` | Must pass `lugal_imap_sync=True` context; must reset `is_read=False` for sent folder after flag parse |
| `email_account.py` | `_sync_sent_folder()` line ~1648 | Creates rows with `is_read=True` — relies on model guard to strip it |
| `email_account.py` | MDN handler (~line 1062) | Correctly uses `lugal_recipient_read=True` — this part appears correct |
| `email_controller.py` | `message_detail()` | Must NOT auto-read if `msg.folder == 'sent'` |
| `email_controller.py` | `toggle_read()` | Must NOT update DB `is_read`/`read_at` for sent messages |
| `email_controller.py` | `_propagate_read_to_sent_copies()` | Must be called after every inbox read action |
| `email_controller.py` | `compose_send()`, `reply()`, `forward()`, `draft_to_sent()` | Sent copy must be created with `is_read=False` |
| `crm_email_controller.py` | `message_detail()` | Same auto-read guard needed as main controller |

---

## 9. Suggested Debugging Steps for the Next Agent

1. **Reproduce the bug first:**
   - Send an email via `/api/lugal/email/send`
   - Immediately call `GET /api/lugal/email/messages?folder=sent`
   - Check if `is_read` is `true` or `false` for the just-sent message
   - If `true` — Bug C (creation) is still active
   - If `false` — open the sent message via `GET /api/lugal/email/messages/<id>`
   - Check `is_read` again — if NOW `true`, Bug E (message detail auto-read) is the culprit

2. **Enable verbose Odoo logging for the model:**
   ```python
   _logger.info("SENT_GUARD: folder=%s, allow=%s, vals=%s", rec.folder, allow_recipient_read, vals)
   ```
   Add this log inside the `write()` guard to confirm it's actually being triggered.

3. **Check context propagation:**
   - At the point where `_sync_sent_folder()` calls `Msg.create(...)`, add a log to print `self.env.context`
   - Verify whether `lugal_imap_sync` or any other context key is present

4. **Test the propagation path:**
   - Have two internal Lugal users (UserA sends to UserB)
   - UserA sends email → check sent folder `is_read=false`
   - UserB opens inbox message → check if UserA's sent folder message becomes `is_read=true`
   - If not — `_propagate_read_to_sent_copies()` is not being called or finding the wrong records

---

## 10. What a "Fix" Looks Like

The fix is NOT a single line change. It requires all of these to work together:

- [ ] Sent messages created with `is_read=False` (Bug C)
- [ ] Model `write()` guard blocks all sent-row `is_read` changes without `lugal_recipient_read` (Bug D)
- [ ] IMAP sync never stamps `read_at` (Bug A + B + H)
- [ ] `message_detail` doesn't auto-read sent messages (Bug E)
- [ ] `_propagate_read_to_sent_copies()` called after every inbox read (Bug F)
- [ ] MDN handler updates all three fields with correct context (Bug G)
- [ ] `_sync_sent_folder()` rows normalized correctly (Bug I)

All nine conditions must hold simultaneously. Previous attempts fixed some but not all, or introduced regressions in adjacent functionality.
