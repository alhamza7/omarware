# Chat & Calling System — Improvement & Odoo Integration Plan

> **Date:** 2026-03-30  
> **Scope:** Chat system, Calling system, Odoo native integration

---

## Executive Summary

The current chat and calling systems are **custom-built REST/JSON-RPC APIs** that store data in their own Odoo models (`lugal.crm.omnichannel.message`, `lugal.crm.call`). They work in isolation from Odoo's native communication tools (`mail.channel`, `discuss`, `mail.message`, `voip`). 

This plan covers three layers:
1. **Immediate fixes** — bugs and missing features in the current system
2. **Odoo deep integration** — linking custom models to Odoo's native discuss/mail/voip
3. **Advanced features** — real-time push, AI, telephony, and omnichannel webhook bridge

---

## 1. Current System Gaps

### 1.1 Chat System Gaps

| Gap | Impact |
|-----|--------|
| No real-time push — frontend must poll every N seconds | High server load, delayed messages |
| No unread count per conversation | Agents can't see what needs attention at a glance |
| No read receipt — `read_at` field exists but never populated | Customer always sees unread badge |
| No message search (text search inside conversations) | Agents cannot find past conversations |
| No file/image attachment in the API (only `media_url` as a URL string) | Cannot send images or documents |
| SLA cron runs every 5 min — breach can be delayed up to 5 minutes | Inaccurate SLA reporting |
| No "typing indicator" support | Poor UX for agent-customer real-time interaction |
| No automatic conversation ID generation | Frontend must generate `conversation_id` — can create duplicates |
| No customer lookup before create — webhook can create duplicate customers | Dirty data |

### 1.2 Calling System Gaps

| Gap | Impact |
|-----|--------|
| No real integration with any telephony/VoIP provider | Recording URL must be manually set |
| `duration_seconds` must be calculated by frontend | Inaccurate if browser tab is closed |
| No call scripts displayed during active call | Agents miss key talking points |
| No callback scheduling — `outcome: "callback"` exists but no follow-up creation | Callbacks are forgotten |
| No CTI (Computer Telephony Integration) — no dial-out from the UI | Agents must use physical phones |
| No queue wait time estimate | Customers and agents don't know expected wait |
| Active context doesn't include open interactions | Agent misses current sales context |

### 1.3 Odoo Integration Gaps

| Gap | Impact |
|-----|--------|
| `lugal.crm.omnichannel.message` not linked to `mail.channel` | Messages invisible in Odoo Discuss |
| `lugal.crm.call` inherits `mail.thread` but call history not visible in customer chatter | Agents lose context |
| No WhatsApp/Instagram webhook bridge to Odoo | All inbound messages must be manually created via API |
| Odoo's built-in `voip` module not used | Duplicate infrastructure |
| No link between CRM interactions and Odoo activities | Follow-ups not tracked in calendar |

---

## 2. Phase 1 — Immediate Fixes (Week 1–2)

### 2.1 Auto-generate `conversation_id`

**Problem:** Frontend must supply `conversation_id` on message create — can cause duplicates.

**Fix:** In `message_create` controller, auto-generate if not provided:
```python
if not conversation_id:
    import uuid
    conversation_id = f"conv_{channel}_{customer_id}_{uuid.uuid4().hex[:8]}"
```

**File:** `addons/lugal_crm/controllers/channel_controller.py`

---

### 2.2 Populate `read_at` on Conversation Fetch

**Problem:** `read_at` is never set — the model has the field but no code writes it.

**Fix:** When `conversation()` is called, mark all messages as read for the current agent:
```python
# After fetching messages
messages.filtered(
    lambda m: m.direction == 'inbound' and not m.read_at
).write({'read_at': Datetime.now()})
```

**File:** `addons/lugal_crm/controllers/channel_controller.py`

---

### 2.3 Unread Count Endpoint

**New endpoint:** `POST /api/crm/channels/messages/unread_counts`

Returns unread count per channel so the sidebar badge updates correctly.

```json
Response:
{
  "data": {
    "total": 12,
    "by_channel": {
      "whatsapp":  7,
      "instagram": 3,
      "telegram":  2
    },
    "sla_breached": 5
  }
}
```

---

### 2.4 Callback Follow-Up Auto-Creation

**Problem:** When a call ends with `outcome: "callback"`, no follow-up task is created.

**Fix:** In `end_call` controller, automatically create a `lugal.crm.task`:
```python
if outcome == 'callback':
    request.env['lugal.crm.task'].sudo().create({
        'title': f'Callback: {call.customer_id.name}',
        'customer_id': call.customer_id.id,
        'assigned_to_id': call.agent_id.id,
        'due_date': Datetime.now() + timedelta(hours=2),
        'priority': 'high',
        'description': f'Callback requested during call {call.id}. Notes: {notes}',
    })
```

**File:** `addons/lugal_crm/controllers/call_controller.py`

---

### 2.5 Message Search Endpoint

**New endpoint:** `POST /api/crm/channels/messages/search`

```json
Request: { "query": "طلب جديد", "channel": "whatsapp", "limit": 20 }
Response: { "items": [ /* matching messages */ ], "total": 5 }
```

Uses Odoo domain `('content', 'ilike', query)`.

---

### 2.6 SLA Real-Time Check on Reply

**Problem:** SLA breach is only detected by a cron job every 5 minutes — inaccurate for reporting.

**Fix:** In `message_reply`, compute FRT immediately and store it:
```python
if original.sent_at:
    frt_seconds = (now - original.sent_at).total_seconds()
    # Store on employee KPI if available
```

Also: add a method `check_and_flag_sla(msg)` called inline on message create and assign, not just in the cron.

---

## 3. Phase 2 — Real-Time Push via Odoo Bus (Week 3–4)

### 3.1 Architecture

Odoo has a built-in longpolling bus (`bus.bus`) on port **8072**. The frontend subscribes to a channel and receives push events within < 1 second.

```
Backend                            Frontend
   │                                  │
   │  message arrives / call event    │
   │                                  │
   ├─ bus.bus.sendone(channel, msg) ──►│ /longpolling/poll
   │                                  │
   │                                  │ onmessage → update store
```

### 3.2 Backend Changes

**Add to `crm_omnichannel_message.py`** — send bus event on create:
```python
@api.model_create_multi
def create(self, vals_list):
    records = super().create(vals_list)
    for rec in records:
        channel_key = f'crm_inbox_branch_{rec.branch_id.id or 0}'
        self.env['bus.bus']._sendone(channel_key, 'new_message', {
            'id':              rec.id,
            'customer_name':   rec.customer_id.name if rec.customer_id else '',
            'channel':         rec.channel,
            'content':         (rec.content or '')[:120],
            'conversation_id': rec.conversation_id,
            'status':          rec.status,
            'sent_at':         rec.sent_at.isoformat() if rec.sent_at else None,
            'sla_breached':    rec.sla_breached,
        })
    return records
```

**Add to `crm_call.py`** — send bus event on create and end:
```python
def _notify_bus(self, event_type):
    channel_key = f'crm_calls_branch_{self.branch_id.id or 0}'
    self.env['bus.bus']._sendone(channel_key, event_type, {
        'id':            self.id,
        'customer_name': self.customer_id.name if self.customer_id else '',
        'call_type':     self.call_type,
        'caller_number': self.caller_number or '',
        'started_at':    self.started_at.isoformat() if self.started_at else None,
    })
```

### 3.3 Frontend Subscription

```typescript
// src/services/realtimeService.ts

const BUS_URL = `${import.meta.env.VITE_API_BASE_URL}:8072`;

class RealtimeService {
  private lastId = 0;
  private polling = false;

  subscribe(branchId: number, handlers: {
    onNewMessage?: (msg: OmnichannelMessage) => void;
    onCallEvent?: (call: CrmCall) => void;
    onSlaBreached?: (msg: OmnichannelMessage) => void;
  }) {
    const channels = [
      { model: 'bus.bus', id: `crm_inbox_branch_${branchId}` },
      { model: 'bus.bus', id: `crm_calls_branch_${branchId}` },
    ];

    const poll = async () => {
      if (!this.polling) return;
      try {
        const res = await fetch(`${BUS_URL}/longpolling/poll`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            jsonrpc: '2.0', method: 'call',
            params: { channels, last: this.lastId },
          }),
        }).then(r => r.json());

        const events = res.result ?? [];
        for (const event of events) {
          this.lastId = Math.max(this.lastId, event.id);
          if (event.message?.type === 'new_message') handlers.onNewMessage?.(event.message.payload);
          if (event.message?.type === 'call_started') handlers.onCallEvent?.(event.message.payload);
          if (event.message?.type === 'sla_breached')  handlers.onSlaBreached?.(event.message.payload);
        }
      } catch (e) {
        await new Promise(r => setTimeout(r, 3000)); // backoff on error
      }
      if (this.polling) poll();
    };

    this.polling = true;
    poll();
  }

  unsubscribe() { this.polling = false; }
}

export const realtimeService = new RealtimeService();
```

**Usage in React:**
```typescript
useEffect(() => {
  realtimeService.subscribe(currentBranchId, {
    onNewMessage: (msg) => {
      queryClient.invalidateQueries(['inbox']);
      showNotification(`رسالة جديدة من ${msg.customer_name}`);
    },
    onSlaBreached: (msg) => {
      showUrgentAlert(`تجاوز SLA: ${msg.customer_name} - ${msg.channel}`);
    },
  });
  return () => realtimeService.unsubscribe();
}, [currentBranchId]);
```

---

## 4. Phase 3 — Odoo Native Discuss Integration (Week 5–6)

### 4.1 Link OmnichannelMessage → mail.channel

Every customer should have a dedicated `mail.channel` in Odoo Discuss. When a new conversation starts, create or find the channel:

```python
def _get_or_create_odoo_channel(self, customer):
    """Find or create an Odoo mail.channel for this customer."""
    channel_name = f'CRM: {customer.name}'
    channel = self.env['mail.channel'].search(
        [('name', '=', channel_name)], limit=1
    )
    if not channel:
        channel = self.env['mail.channel'].create({
            'name': channel_name,
            'description': f'Omnichannel conversations for {customer.name}',
            'channel_type': 'channel',
        })
        # Add CRM team as members
        channel.add_members(partner_ids=customer.partner_id.ids)
    return channel
```

When an inbound message arrives, **mirror it to the Odoo channel**:
```python
channel.message_post(
    body=f'[{rec.channel.upper()}] {rec.content}',
    author_id=customer.partner_id.id,
    message_type='comment',
    subtype_xmlid='mail.mt_comment',
)
```

**Result:** CRM agents see customer messages in Odoo Discuss AND in the custom CRM inbox simultaneously.

### 4.2 Link Call → Customer Chatter

After a call ends, post a summary to the customer's chatter:

```python
# In end_call or in CrmCall.write() override
if 'ended_at' in vals or 'outcome' in vals:
    customer = self.customer_id
    if customer and customer.partner_id:
        body = f"""
        📞 Call {self.call_type} — {self.outcome or 'in progress'}<br/>
        Duration: {self.duration_seconds}s<br/>
        Notes: {self.notes or '—'}<br/>
        Agent: {self.agent_id.name}
        """
        customer.partner_id.message_post(
            body=body,
            subtype_xmlid='mail.mt_note',
        )
```

**Result:** Every call appears in the customer's `res.partner` chatter — visible everywhere in Odoo (Sales, POS, Accounting).

### 4.3 Link Call → Odoo Activities

When `outcome = "callback"`, create an Odoo `mail.activity` instead of (or in addition to) the CRM task:

```python
customer.partner_id.activity_schedule(
    'mail.mail_activity_data_call',
    date_deadline=fields.Date.today() + timedelta(days=1),
    summary=f'Callback: {customer.name}',
    note=notes,
    user_id=call.agent_id.id,
)
```

**Result:** Callback appears in the agent's Odoo activity feed, calendar, and "My Activities" view.

---

## 5. Phase 4 — WhatsApp/Instagram Webhook Bridge (Week 7–8)

### 5.1 Architecture

```
WhatsApp Business API
        │
        │ (webhook POST)
        ▼
  Odoo Webhook Endpoint
  /api/crm/webhook/whatsapp
        │
        ├─ Look up customer by phone
        │  (create if not found)
        │
        ├─ Create OmnichannelMessage
        │
        ├─ Notify bus.bus
        │
        └─ (optional) Auto-reply via WA API
```

### 5.2 New Webhook Endpoints

```
POST /api/crm/webhook/whatsapp    — WhatsApp Business API webhook
POST /api/crm/webhook/instagram   — Instagram Graph API webhook
POST /api/crm/webhook/telegram    — Telegram Bot API webhook
GET  /api/crm/webhook/<channel>/verify — Webhook verification (GET challenge)
```

### 5.3 Example WhatsApp Webhook Handler

```python
@http.route('/api/crm/webhook/whatsapp', type='http', auth='none', csrf=False, methods=['POST'])
def whatsapp_webhook(self, **kwargs):
    import json
    payload = json.loads(request.httprequest.data)
    
    # Verify webhook signature (HMAC-SHA256)
    if not self._verify_wa_signature(request.httprequest):
        return Response('Forbidden', status=403)
    
    for entry in payload.get('entry', []):
        for change in entry.get('changes', []):
            for message in change.get('value', {}).get('messages', []):
                phone = message.get('from', '')
                text = message.get('text', {}).get('body', '')
                wa_msg_id = message.get('id', '')
                
                # Find or create customer
                customer = self._find_or_create_customer_by_phone(phone)
                
                # Create message
                request.env['lugal.crm.omnichannel.message'].sudo().create({
                    'customer_id': customer.id,
                    'channel': 'whatsapp',
                    'direction': 'inbound',
                    'content': text,
                    'conversation_id': f'wa_{customer.id}',
                    'sent_at': Datetime.now(),
                    'status': 'pending',
                })
    
    return Response('OK', status=200)
```

### 5.4 Outbound Message Delivery

When agent sends a reply via `message_reply`, the system must **actually send it** to the platform:

```python
# In message_reply controller, after creating the outbound message:
if original.channel == 'whatsapp':
    self._send_via_whatsapp(
        phone=original.customer_id.phone_1,
        text=content,
    )
elif original.channel == 'telegram':
    self._send_via_telegram(
        chat_id=original.conversation_id,
        text=content,
    )
```

**Supported outbound:** WhatsApp (via WA Business API), Telegram (via Bot API), Email (via lugal_email).  
**Not yet supported:** Instagram DMs (requires Meta approval), TikTok, Snapchat.

---

## 6. Phase 5 — VoIP Integration (Week 9–10)

### 6.1 Option A — Odoo Native VoIP Module

Odoo 17 includes a built-in `voip` module that supports:
- Click-to-dial from customer records
- Automatic call logging to `mail.thread`
- SIP.js softphone in the browser

**Integration steps:**
1. Install `voip` module
2. Configure SIP server (Asterisk/FreeSWITCH/3CX)
3. Link `lugal.crm.call` to `voip.call` via Many2one
4. When a voip call ends, sync data to CRM call record

### 6.2 Option B — Custom SIP.js Integration

For full control, integrate SIP.js directly in the frontend:

```typescript
// src/services/sipService.ts
import { UserAgent, Inviter, SessionState } from 'sip.js';

export class SipService {
  private ua: UserAgent;

  connect(sipUri: string, wsServer: string, token: string) {
    this.ua = new UserAgent({
      uri: UserAgent.makeURI(sipUri),
      transportOptions: { server: wsServer },
      authorizationUsername: sipUri,
      authorizationPassword: token,
    });

    this.ua.delegate = {
      onInvite: async (invitation) => {
        const callerNumber = invitation.remoteIdentity.uri.user ?? '';
        
        // Screen pop: fetch customer context immediately
        const context = await crmPost('/api/crm/calls/active_context',
          { phone_number: callerNumber }, authToken);
        
        // Show incoming call UI
        showIncomingCallDialog({ callerNumber, context });
        
        invitation.accept().then(() => {
          // Create call record in CRM
          crmPost('/api/crm/calls/create', {
            customer_id: context.data.customer?.id,
            call_type: 'inbound',
            caller_number: callerNumber,
          }, authToken).then(call => { activeCallId = call.data.id; });
        });
      },
    };

    this.ua.start();
  }

  dialOut(phoneNumber: string) {
    const target = UserAgent.makeURI(`sip:${phoneNumber}@${sipDomain}`);
    const inviter = new Inviter(this.ua, target);
    inviter.invite();
  }
}
```

### 6.3 Call Recording (Automatic)

Configure Asterisk/FreeSWITCH to record calls and POST the file URL to Odoo:
```
POST /api/crm/calls/<id>/attach_recording
Body: { "recording_url": "https://pbx.company.com/recordings/20260330-501.mp3" }
```

---

## 7. Phase 6 — AI Features (Week 11–12)

### 7.1 AI Call Summary

After call ends, send transcript to an AI service and save the summary:

```python
# In end_call, after writing outcome/notes
if duration_seconds and duration_seconds > 30:
    try:
        summary = self._generate_ai_summary(
            notes=notes,
            outcome=outcome,
            customer_name=call.customer_id.name,
        )
        call.write({'ai_summary': summary})
    except Exception:
        pass  # Non-blocking
```

### 7.2 AI Auto-Reply Suggestions

When a new inbound message arrives, suggest 3 reply templates based on the message content:

**New endpoint:** `POST /api/crm/channels/messages/<id>/suggest_replies`

```json
Response:
{
  "data": {
    "suggestions": [
      "شكراً لتواصلك! سأساعدك في أقرب وقت.",
      "أهلاً! يمكنني مساعدتك في طلبك.",
      "مرحباً، سيتم تحويلك لأحد متخصصينا."
    ]
  }
}
```

### 7.3 Sentiment Analysis

Compute customer sentiment on message create and store it:
```python
sentiment = self._analyze_sentiment(content)  # 'positive'/'neutral'/'negative'
vals['sentiment'] = sentiment
```

Use on the dashboard to flag frustrated customers.

---

## 8. Implementation Roadmap Summary

| Phase | Features | Effort | Priority |
|-------|----------|--------|----------|
| **Phase 1** | Auto conversation_id, read receipts, unread counts, callback tasks, message search, SLA fix | 5 days | **P0** |
| **Phase 2** | Odoo Bus real-time push + frontend subscription | 4 days | **P0** |
| **Phase 3** | Odoo Discuss mirror, call chatter, activities | 5 days | **P1** |
| **Phase 4** | WhatsApp webhook bridge (inbound + outbound) | 6 days | **P1** |
| **Phase 5** | VoIP / SIP.js integration | 8 days | **P2** |
| **Phase 6** | AI summary + reply suggestions | 5 days | **P2** |
| **Instagram webhook** | Meta Graph API integration | 4 days | **P3** |
| **Telegram webhook** | Telegram Bot API | 3 days | **P3** |

**Total: ~40 days (8 weeks, 1 full-stack engineer)**

---

## 9. Recommended First Sprint (P0 — 9 days)

### Day 1-2
- [ ] Fix `conversation_id` auto-generation in `message_create`
- [ ] Fix `read_at` population in `conversation` endpoint
- [ ] Add `unread_counts` endpoint

### Day 3
- [ ] Add callback follow-up task auto-creation in `end_call`
- [ ] Add message search endpoint

### Day 4-5
- [ ] Add `bus.bus` notifications to `CrmOmnichannelMessage.create()`
- [ ] Add `bus.bus` notifications to `CrmCall` on create and end

### Day 6-7
- [ ] Frontend: implement `RealtimeService` with longpolling
- [ ] Frontend: connect inbox and calls list to real-time updates
- [ ] Frontend: show browser notifications on new message

### Day 8-9
- [ ] Link `lugal.crm.call` end to customer partner chatter
- [ ] Test all flows end-to-end
- [ ] Deploy and monitor

**Result after sprint:** Near-real-time inbox, call chatter visible in Odoo, callbacks tracked as tasks.
