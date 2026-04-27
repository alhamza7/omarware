# CRM Communication System — Full Architecture Reference

> **Module:** `lugal_crm` (Odoo 19, Python 3.12)  
> **Base path (all APIs):** JSON-RPC via POST  
> **Auth:** JWT token in `Authorization: Bearer <token>` header (via `lugal_auth`)  
> **Last updated:** 2026-03-31

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Module File Structure](#2-module-file-structure)
3. [Calling System](#3-calling-system)
4. [Chat / Omnichannel System](#4-chat--omnichannel-system)
5. [Email System](#5-email-system)
6. [Cross-cutting: Agent Status](#6-cross-cutting-agent-status)
7. [Cross-cutting: Interaction Timeline](#7-cross-cutting-interaction-timeline)
8. [Data Flow Diagrams](#8-data-flow-diagrams)
9. [API Quick Reference](#9-api-quick-reference)
10. [Integration Points](#10-integration-points)

---

## 1. System Overview

The CRM communication layer is composed of **three sub-systems** that share a common:
- JWT authentication (`lugal_auth`)
- Audit log (`lugal.crm.audit.log`)
- Customer record (`lugal.crm.customer`)
- Interaction timeline (`lugal.crm.interaction`)

```
┌─────────────────────────────────────────────────────────────────┐
│                       lugal_crm module                          │
│                                                                 │
│  ┌──────────────┐  ┌─────────────────────┐  ┌───────────────┐  │
│  │   CALLING    │  │  CHAT / OMNICHANNEL  │  │     EMAIL     │  │
│  │  Sub-system  │  │     Sub-system       │  │  Sub-system   │  │
│  └──────┬───────┘  └──────────┬──────────┘  └───────┬───────┘  │
│         │                     │                      │          │
│         └─────────────────────┴──────────────────────┘          │
│                               │                                 │
│                 ┌─────────────▼──────────────┐                  │
│                 │  lugal.crm.interaction     │                  │
│                 │  (unified activity log)    │                  │
│                 └─────────────┬──────────────┘                  │
│                               │                                 │
│                 ┌─────────────▼──────────────┐                  │
│                 │  lugal.crm.customer        │                  │
│                 │  (360° customer card)      │                  │
│                 └────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
         ↑                      ↑                     ↑
    lugal_auth             SLA cron             lugal_email
    (JWT)                  (5 min)              (IMAP/SMTP)
```

---

## 2. Module File Structure

```
addons/lugal_crm/
│
├── __manifest__.py          # depends: base, mail, lugal_auth, lugal_email, lugal_supply
├── __init__.py
│
├── models/
│   ├── __init__.py
│   │
│   │── CALLING SYSTEM ────────────────────────────────────────────
│   ├── crm_call.py              # lugal.crm.call          – call record
│   ├── crm_call_queue.py        # lugal.crm.call.queue    – incoming call queue
│   ├── crm_call_script.py       # lugal.crm.call.script   – FAQ/scripts for agents
│   │
│   │── CHAT SYSTEM ───────────────────────────────────────────────
│   ├── crm_omnichannel_message.py  # lugal.crm.omnichannel.message – individual message
│   ├── crm_channel_config.py       # lugal.crm.channel.config      – channel settings + SLA
│   ├── crm_channel_identity.py     # lugal.crm.channel.identity    – per-account identities
│   ├── crm_message_template.py     # lugal.crm.message.template    – quick-reply templates
│   ├── crm_chat_session.py      ★  # lugal.crm.chat.session        – conversation container
│   │                               # also extends omnichannel.message with session_id
│   │
│   │── EMAIL SYSTEM ──────────────────────────────────────────────
│   ├── crm_email_extension.py   # extends lugal.email.message with CRM typed links
│   │                            # linked_customer_id, linked_ticket_id
│   │
│   │── CROSS-CUTTING ─────────────────────────────────────────────
│   ├── crm_agent_status.py      ★  # lugal.crm.agent.status  – agent availability
│   ├── crm_interaction.py          # lugal.crm.interaction   – unified activity log
│   ├── crm_customer.py             # lugal.crm.customer      – customer 360° card
│   ├── crm_ticket.py               # lugal.crm.ticket
│   ├── crm_task.py                 # lugal.crm.task
│   ├── crm_audit_log.py            # lugal.crm.audit.log
│   ├── crm_qa_review.py            # lugal.crm.qa.review
│   ├── crm_employee_kpi.py         # lugal.crm.employee.kpi
│   └── ... (branch, tag, stage, supply, kb, shift, etc.)
│
├── controllers/
│   ├── __init__.py
│   │
│   │── CALLING SYSTEM ────────────────────────────────────────────
│   ├── call_controller.py       # /api/crm/calls/*  +  /api/crm/calls/queue/*
│   │                            # /api/crm/calls/active_context
│   │
│   │── CHAT SYSTEM ───────────────────────────────────────────────
│   ├── channel_controller.py    # /api/crm/channels/config_*
│   │                            # /api/crm/channels/messages/*
│   │
│   │── EMAIL + AGENT + SESSION ────────────────────────────────────
│   ├── crm_email_crm_controller.py ★  # /api/crm/email/*
│   │                                  # /api/crm/agent/*
│   │                                  # /api/crm/chat/sessions/*
│   │
│   │── SUPPORT ───────────────────────────────────────────────────
│   ├── customer_controller.py   # /api/crm/customers/*
│   ├── ticket_controller.py     # /api/crm/tickets/*
│   ├── analytics_controller.py  # /api/crm/analytics/*
│   ├── knowledge_controller.py  # /api/crm/kb/*
│   └── ... (branch, supply, pos_bridge, price_list, qa, etc.)
│
├── data/
│   ├── crm_sequences.xml        # TKT-, QA-, SESS- sequences
│   └── crm_cron.xml             # SLA breach, KPI snapshot, stale agent status
│
└── security/
    ├── groups.xml
    └── ir.model.access.csv      # ACL for all models
```

> ★ = files added/created in this session

---

## 3. Calling System

### 3.1 Models

#### `lugal.crm.call`
Core call record. Created when an agent starts a call. Closed via `end` endpoint.

| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | Many2one | CRM customer |
| `agent_id` | Many2one | res.users |
| `call_type` | Selection | `inbound` / `outbound` |
| `caller_number` | Char | CLI / caller phone |
| `started_at` | Datetime | Call start |
| `ended_at` | Datetime | Call end |
| `duration_seconds` | Integer | Auto-set on end |
| `outcome` | Selection | resolved / callback / escalated / no_answer |
| `notes` | Text | Agent notes |
| `ai_summary` | Text | AI-generated summary |
| `qa_score` | Float | Quality assurance score |
| `recording_url` | Char | External URL / path |
| `catalogue_sent` | Boolean | Was catalogue sent? |
| `catalogue_sent_via` | Selection | whatsapp / email / telegram |
| `ticket_created_id` | Many2one | Ticket opened during call |
| `invoice_created_id` | Integer | POS invoice ID |
| `balance_at_call` | Float | Customer balance snapshot |

#### `lugal.crm.call.queue`
Incoming calls waiting for an available agent.

| Field | Type | Description |
|-------|------|-------------|
| `caller_number` | Char | |
| `customer_id` | Many2one | May be null (unknown caller) |
| `queue_position` | Integer | Auto-incremented |
| `status` | Selection | waiting / assigned / answered / abandoned |
| `assigned_to_id` | Many2one | Agent who accepted |
| `queued_at` | Datetime | Time entered queue |

#### `lugal.crm.call.script`
FAQ/guided workflow cards shown in the agent's call dialog.

| Field | Type | Description |
|-------|------|-------------|
| `title` | Char | |
| `category` | Selection | faq / guided_workflow / objection_handling |
| `question` | Char | |
| `answer` | Text | |
| `branch_id` | Many2one | Branch-specific or company-wide |
| `sequence` | Integer | Display order |

### 3.2 Call API Endpoints

All routes: `type='jsonrpc'`, `auth='none'`, JWT required.

```
POST /api/crm/calls/list
  → page, per_page, customer_id, branch_id, agent_id, date_from, date_to, outcome
  ← { items[], total, page, per_page }

POST /api/crm/calls/<id>
  ← { call_dict }

POST /api/crm/calls/create
  → customer_id*, call_type, channel, caller_number, branch_id
  ← { call_dict }
    Side effects: snapshots customer financials, writes last_call_date

POST /api/crm/calls/<id>/end
  → duration_seconds, outcome, notes, catalogue_sent, catalogue_sent_via, recording_url
  ← { call_dict }

POST /api/crm/calls/<id>/update
  → notes, ai_summary, qa_score, issues_found, outcome, recording_url,
    catalogue_sent, catalogue_sent_via, pos_order_id, pos_order_name, ...
  ← { call_dict }

POST /api/crm/calls/<id>/delete
  ← { success: true }  (soft-delete)

POST /api/crm/calls/<id>/attach_recording
  → recording_url*
  ← { id, recording_url }

─── Queue ─────────────────────────────────────────────

POST /api/crm/calls/queue/list
  → status (default: 'waiting')
  ← { items[] }

POST /api/crm/calls/queue/add
  → customer_id, channel, caller_number
  ← { id, queue_position }

POST /api/crm/calls/queue/<id>/assign
  ← { success: true }
    Side effects: agent status → busy

─── Active Call Context ────────────────────────────────

POST /api/crm/calls/active_context
  → call_id  OR  phone_number
  ← { customer: {...}, recent_tickets: [], recent_orders: [] }
```

### 3.3 Call Lifecycle

```
[Inbound]                           [Outbound]
  PSTN/VoIP                          Agent dials
       │                                │
  queue/add ──► waiting                 │
       │                          calls/create
  queue/assign                          │
       │                         (customer lookup)
  calls/create  ◄──────────────────────┘
       │
  (active_context in call dialog)
       │
  calls/end  →  outcome, notes, recording_url
       │
  [Optional] ticket_controller/create
  [Optional] pos_bridge/create_invoice
       │
  crm.interaction logged
```

---

## 4. Chat / Omnichannel System

### 4.1 Models

#### `lugal.crm.omnichannel.message`
Individual inbound or outbound message from any channel.

| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | Many2one | |
| `channel` | Selection | whatsapp / instagram / telegram / tiktok / x / snapchat / email / website |
| `direction` | Selection | inbound / outbound |
| `content` | Text | Message text |
| `media_url` | Char | Media attachment URL |
| `sent_at` | Datetime | |
| `conversation_id` | Char | Groups messages into threads |
| `session_id` ★ | Many2one | Links to `lugal.crm.chat.session` |
| `status` | Selection | pending / assigned / resolved |
| `assigned_to_id` | Many2one | Agent |
| `owner_id` | Many2one | First-reply owner |
| `replied_by_agent_at` | Datetime | First Response Time anchor |
| `sla_breached` | Boolean | Set by 5-min cron |
| `waiting_customer_response` | Boolean | |

#### `lugal.crm.chat.session` ★ (NEW)
Conversation container — one per `conversation_id`.

| Field | Type | Description |
|-------|------|-------------|
| `session_ref` | Char | Auto-seq: SESS-00001 |
| `conversation_id` | Char | Matches omnichannel_message.conversation_id |
| `customer_id` | Many2one | |
| `channel` | Selection | |
| `status` | Selection | open / pending / resolved / closed |
| `opened_at` | Datetime | |
| `resolved_at` | Datetime | Auto-set on status=resolved |
| `closed_at` | Datetime | Auto-set on status=closed |
| `last_message_at` | Datetime | Updated on touch() |
| `first_response_seconds` | Integer | FRT metric |
| `handle_time_seconds` | Integer | Computed from open→resolved |
| `sla_breached` | Boolean | |
| `message_count` | Integer | Computed from message_ids |
| `unread_count` | Integer | Incremented on inbound messages |
| `reopen_count` | Integer | Counts re-opens |
| `assigned_to_id` | Many2one | |
| `owner_id` | Many2one | |

#### `lugal.crm.channel.config`
Per-branch channel settings, SLA, work hours.

| Field | Type | Description |
|-------|------|-------------|
| `channel` | Selection | |
| `branch_id` | Many2one | |
| `sla_threshold_seconds` | Integer | Default 300 (5 min) |
| `work_hours_start` | Float | e.g. 8.0 = 08:00 |
| `work_hours_end` | Float | e.g. 18.0 = 18:00 |
| `assigned_user_ids` | Many2many | |
| `is_free_for_all` | Boolean | All agents can take chats |

#### `lugal.crm.message.template`
Quick-reply templates with placeholder support.

Placeholders: `{customer_name}`, `{agent_name}`, `{branch_name}`

### 4.2 Chat API Endpoints

```
─── Channel Config ─────────────────────────────────────

POST /api/crm/channels/config_list
  → branch_id
  ← { items[] }

POST /api/crm/channels/config/create
  → channel*, branch_id, display_name, color_hex, is_free_for_all,
    sla_threshold_seconds, work_hours_start, work_hours_end
  ← { config_dict }

POST /api/crm/channels/config/<id>/update
  → any config field
  ← { config_dict }

POST /api/crm/channels/config/<id>/delete
  ← { success: true }

─── Messages (individual) ──────────────────────────────

POST /api/crm/channels/messages/list
  → page, per_page, customer_id, channel, status, branch_id,
    assigned_to_id, sla_breached
  ← { items[], total, page, per_page }

POST /api/crm/channels/messages/conversation
  → conversation_id*
  ← { items[] }  (chronological order)

POST /api/crm/channels/messages/create
  → customer_id*, channel*, content*, direction, conversation_id,
    branch_id, media_url
  ← { message_dict }
    Side effects (outbound): sets owner_id, replied_by_agent_at,
                             waiting_customer_response

POST /api/crm/channels/messages/<id>/assign
  → assigned_to_id (default: current user)
  ← { message_dict }

POST /api/crm/channels/messages/<id>/reply
  → content*, media_url
  ← { message_dict }  (new outbound message)
    Side effects: sets FRT on original, owner_id, marks waiting

POST /api/crm/channels/messages/<id>/resolve
  ← { success: true }
    Side effects: resolves all messages in conversation

POST /api/crm/channels/messages/<id>/transfer
  → new_owner_id*
  ← { success: true }
    Side effects: reassigns all messages in conversation

─── Sessions (conversation-level) ──────────────────────

POST /api/crm/chat/sessions/list
  → page, per_page, customer_id, channel, status, branch_id,
    assigned_to_id, sla_breached
  ← { items[], total, page, per_page }

POST /api/crm/chat/sessions/<id>
  ← { session_dict + messages[] }
    Side effects: resets unread_count

POST /api/crm/chat/sessions/<id>/resolve
  ← { session_dict }

POST /api/crm/chat/sessions/<id>/reopen
  ← { session_dict }

POST /api/crm/chat/sessions/unread_counts
  → branch_id
  ← { by_channel: {whatsapp: N, ...}, total: N }
```

### 4.3 SLA Cron Architecture

```
Every 5 min (ir.cron → lugal.crm.omnichannel.message._cron_flag_sla_breaches):
  1. Find all pending inbound messages with sla_breached=False
  2. Lookup channel.config for their channel+branch
  3. If elapsed > sla_threshold_seconds → set sla_breached=True

Every 30 min (ir.cron → lugal.crm.agent.status._cron_reset_stale_statuses):
  1. Find online/busy agents with last_status_change > 2 hours ago
  2. Auto-set to offline (crashed session protection)
```

---

## 5. Email System

### 5.1 Architecture — Two-layer design

```
┌─────────────────────────────────────────────────┐
│              lugal_crm module                    │
│                                                  │
│  crm_email_extension.py                          │
│  ├── _inherit 'lugal.email.message'              │
│  ├── +linked_customer_id (Many2one)              │
│  ├── +linked_ticket_id   (Many2one)              │
│  ├── override _to_list_dict()  → crm_links{}     │
│  └── override action_link_to_record()            │
│                                                  │
│  crm_email_crm_controller.py ★                  │
│  └── /api/crm/email/*  (CRM-scoped endpoints)   │
└──────────────────────┬──────────────────────────┘
                       │ depends on / delegates to
┌──────────────────────▼──────────────────────────┐
│              lugal_email module                  │
│                                                  │
│  lugal.email.account   (IMAP + SMTP per user)    │
│  lugal.email.message   (stored email records)    │
│  /api/lugal/email/*    (raw email REST API)      │
└─────────────────────────────────────────────────┘
```

### 5.2 Models

#### `lugal.email.message` (in `lugal_email`)
Base email storage. Extended by `lugal_crm`.

| Field | Type | Description |
|-------|------|-------------|
| `account_id` | Many2one | lugal.email.account |
| `subject` | Char | |
| `from_address` | Char | |
| `to_addresses` | Text | JSON: [{name, email}] |
| `cc_addresses` | Text | JSON: [{name, email}] |
| `date` | Datetime | |
| `body_html` | Html | |
| `body_text` | Text | |
| `folder` | Selection | inbox/sent/drafts/trash/spam/archive |
| `is_read` | Boolean | |
| `is_starred` | Boolean | |
| `attachment_ids` | Many2many | ir.attachment |
| `linked_record_model` | Char | Generic link model name |
| `linked_record_id` | Integer | Generic link record ID |
| `preview` | Char | Computed 160-char preview |

CRM extension fields (`crm_email_extension.py`):

| Field | Type | Description |
|-------|------|-------------|
| `linked_customer_id` | Many2one | lugal.crm.customer |
| `linked_ticket_id` | Many2one | lugal.crm.ticket |

### 5.3 CRM Email API Endpoints

All routes: `type='jsonrpc'`, JWT required.

```
─── Customer-scoped inbox ──────────────────────────────

POST /api/crm/email/customer/<id>/messages
  → folder, page, per_page
  ← { customer_id, customer_name, total, items[] }
    Covers: linked_customer_id  OR  linked_record_model+id

POST /api/crm/email/customer/<id>/thread
  → subject_contains
  ← { threads: [{subject, messages[]}] }
    Grouped by normalised subject (strips Re:/Fwd:)

─── Paginated list with CRM filters ────────────────────

POST /api/crm/email/messages/list
  → page, per_page, folder, customer_id, ticket_id, is_read
  ← { total, items[] }  (current user's account)

POST /api/crm/email/messages/<id>
  ← { detail_dict }  (marks as read)

─── Send ────────────────────────────────────────────────

POST /api/crm/email/send
  → account_id*, to_addresses*, subject*, body_html, body_text,
    cc_addresses, customer_id, ticket_id, in_reply_to, attachment_ids
  ← { message_id }
    Side effects:
      1. Sends via SMTP (delegates to lugal.email.account.send_email)
      2. Stores sent message with CRM links
      3. Creates lugal.crm.interaction (type=email)

─── Linking ─────────────────────────────────────────────

POST /api/crm/email/messages/<id>/link
  → model*, record_id*, record_name
  ← { message_dict }
    model must be in ALLOWED_LINK_MODELS

POST /api/crm/email/messages/<id>/unlink
  ← { message_dict }

─── Quick actions ───────────────────────────────────────

POST /api/crm/email/messages/<id>/read
POST /api/crm/email/messages/<id>/trash
POST /api/crm/email/messages/<id>/archive
```

### 5.4 Auto-Link Incoming Emails to Customers

Add this hook to `lugal_crm/models/crm_email_extension.py` (or a separate mixin):

```python
class LugalEmailAccountCrmAutoLink(models.Model):
    _inherit = 'lugal.email.account'

    def _post_store_message(self, message_rec):
        super()._post_store_message(message_rec)
        if message_rec.from_address:
            customer = self.env['lugal.crm.customer'].search(
                [('email', '=', message_rec.from_address)], limit=1
            )
            if customer:
                message_rec.action_link_to_record(
                    'lugal.crm.customer', customer.id, customer.name
                )
```

### 5.5 Base Email API (lugal_email module)

The standalone `lugal_email` module provides the raw infrastructure:

```
GET  /api/lugal/email/accounts           — list accounts
POST /api/lugal/email/accounts/connect   — add IMAP/SMTP account
POST /api/lugal/email/accounts/<id>/sync — trigger IMAP sync
GET  /api/lugal/email/messages           — list with filters
GET  /api/lugal/email/messages/<id>      — detail
POST /api/lugal/email/send               — low-level send
POST /api/lugal/email/messages/<id>/link — generic link
```

CRM controllers (`/api/crm/email/*`) sit **on top** of this and add customer/ticket context.

---

## 6. Cross-cutting: Agent Status

### 6.1 Model: `lugal.crm.agent.status` ★

One record per `res.users` agent. Upserted via `set_status()` classmethod.

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | Many2one | UNIQUE — one record per user |
| `status` | Selection | offline / online / busy / break |
| `is_available` | Boolean | Computed: online + no active call + <5 chats |
| `active_call_id` | Many2one | Set when agent accepts a call |
| `open_chat_count` | Integer | Managed by channel controller |
| `branch_id` | Many2one | |
| `active_channels` | Char | JSON list of channels agent is monitoring |
| `last_status_change` | Datetime | For stale-session detection |

### 6.2 Valid Status Transitions

```
offline  ──► online
online   ──► busy | break | offline
busy     ──► online | break | offline
break    ──► online | offline
```

Attempting an invalid transition returns a `ValueError`.

### 6.3 Agent Status API Endpoints

```
POST /api/crm/agent/status
  → agent_id  (default: current user)
  ← { id, agent_id, agent_name, status, is_available,
       open_chat_count, active_call_id, branch_id, last_status_change }

POST /api/crm/agent/set_status
  → status*, branch_id
  ← { status, is_available }
```

### 6.4 Routing Helper

```python
# Find next available agent for a channel/branch
agents = request.env['lugal.crm.agent.status'].get_available_agents(
    branch_id=3, channel='whatsapp'
)
# Returns: records ordered by open_chat_count asc (least loaded first)
```

---

## 7. Cross-cutting: Interaction Timeline

Every call, chat reply, and email send writes to `lugal.crm.interaction` — the unified customer activity log.

### Model: `lugal.crm.interaction`

| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | Many2one | Required |
| `user_id` | Many2one | Agent |
| `interaction_type` | Selection | call / message / email / visit / note |
| `channel` | Char | whatsapp, email, phone, etc. |
| `subject` | Char | Email subject or call summary |
| `body` | Text | Message content or notes |
| `outcome` | Char | call outcome or email recipient |
| `duration_seconds` | Integer | For calls |
| `interaction_date` | Datetime | |

### When it is written

| Event | Type logged |
|-------|-------------|
| `calls/create` (start) | `call` |
| `channels/messages/<id>/reply` | `message` |
| `email/send` | `email` |
| Manual note in customer card | `note` |

---

## 8. Data Flow Diagrams

### 8.1 Inbound Call Flow

```
Phone/SIP ──► Telephony Gateway
                     │
              POST /api/crm/calls/queue/add
                     │
                [ Queue entry: waiting ]
                     │
              Agent sees queue → POST /api/crm/calls/queue/<id>/assign
                     │
              POST /api/crm/calls/create  (customer_id from phone lookup)
                     │
              [ Active call dialog ]
                │            │
     active_context      call_scripts
     (customer card)     (FAQ panel)
                │
         Agent fills outcome/notes
                │
         POST /api/crm/calls/<id>/end
                │
         ┌──────┴──────────┐
    ticket/create      catalogue/send
                │
         crm.interaction logged
```

### 8.2 Inbound Chat Message Flow

```
WhatsApp/Telegram Webhook
         │
POST /api/crm/channels/messages/create
  (direction='inbound', conversation_id='WA-12345')
         │
  Session: get_or_create_for_conversation()
         │
  SLA cron (every 5 min) checks if replied
         │
  Agent sees unread_counts badge
         │
POST /api/crm/channels/messages/<id>/reply
  (creates outbound message, sets FRT, owner_id)
         │
POST /api/crm/chat/sessions/<id>/resolve
  (closes conversation, logs to interaction)
```

### 8.3 Inbound Email Flow

```
IMAP Sync (lugal.email.account._sync_imap)
         │
lugal.email.message created
         │
_post_store_message() hook
         │
lugal.crm.customer matched by from_address
         │
action_link_to_record('lugal.crm.customer', ...)
  → sets linked_customer_id (typed Many2one)
  → sets linked_record_model + linked_record_id (generic)
         │
Appears in: /api/crm/email/customer/<id>/messages
```

---

## 9. API Quick Reference

### Authentication

All endpoints require:
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": { ...endpoint params... }
}
```

### Response shape (standard)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": { ... }
  }
}
```

Error response:
```json
{
  "result": {
    "success": false,
    "error": "Human-readable message"
  }
}
```

### Full endpoint table

| Category | Endpoint | Description |
|----------|----------|-------------|
| **Calls** | `POST /api/crm/calls/list` | List calls |
| | `POST /api/crm/calls/create` | Start call |
| | `POST /api/crm/calls/<id>` | Get call |
| | `POST /api/crm/calls/<id>/end` | End call |
| | `POST /api/crm/calls/<id>/update` | Update call |
| | `POST /api/crm/calls/<id>/delete` | Soft-delete |
| | `POST /api/crm/calls/<id>/attach_recording` | Add recording URL |
| | `POST /api/crm/calls/active_context` | Caller lookup + context |
| **Queue** | `POST /api/crm/calls/queue/list` | List queue |
| | `POST /api/crm/calls/queue/add` | Add to queue |
| | `POST /api/crm/calls/queue/<id>/assign` | Agent takes call |
| **Chat Config** | `POST /api/crm/channels/config_list` | List channel configs |
| | `POST /api/crm/channels/config/create` | Create config |
| | `POST /api/crm/channels/config/<id>/update` | Update config |
| | `POST /api/crm/channels/config/<id>/delete` | Delete config |
| **Messages** | `POST /api/crm/channels/messages/list` | List messages |
| | `POST /api/crm/channels/messages/conversation` | Get thread |
| | `POST /api/crm/channels/messages/create` | New message |
| | `POST /api/crm/channels/messages/<id>/assign` | Assign |
| | `POST /api/crm/channels/messages/<id>/reply` | Reply |
| | `POST /api/crm/channels/messages/<id>/resolve` | Resolve |
| | `POST /api/crm/channels/messages/<id>/transfer` | Transfer |
| **Sessions** ★ | `POST /api/crm/chat/sessions/list` | List sessions |
| | `POST /api/crm/chat/sessions/<id>` | Session detail + messages |
| | `POST /api/crm/chat/sessions/<id>/resolve` | Resolve |
| | `POST /api/crm/chat/sessions/<id>/reopen` | Re-open |
| | `POST /api/crm/chat/sessions/unread_counts` | Badge counts |
| **Email** ★ | `POST /api/crm/email/customer/<id>/messages` | Customer inbox |
| | `POST /api/crm/email/customer/<id>/thread` | Threaded view |
| | `POST /api/crm/email/messages/list` | Paginated list |
| | `POST /api/crm/email/messages/<id>` | Message detail |
| | `POST /api/crm/email/send` | Send email |
| | `POST /api/crm/email/messages/<id>/link` | Link to record |
| | `POST /api/crm/email/messages/<id>/unlink` | Unlink |
| | `POST /api/crm/email/messages/<id>/read` | Mark read |
| | `POST /api/crm/email/messages/<id>/trash` | Move to trash |
| | `POST /api/crm/email/messages/<id>/archive` | Archive |
| **Agent** ★ | `POST /api/crm/agent/status` | Get status |
| | `POST /api/crm/agent/set_status` | Set status |

---

## 10. Integration Points

### 10.1 POS Bridge
- `crm_call.invoice_created_id` → `pos.order` ID
- `call_controller.active_context` → fetches recent `pos.order` records
- `pos_bridge_controller.py` → create invoice during active call

### 10.2 Tickets
- `crm_call.ticket_created_id` → ticket opened during call
- `ticket_controller.py` → full ticket CRUD
- `email_controller` → `linked_ticket_id` on email message

### 10.3 Supply Chain
- `supply_controller.py` + `supply_ext_controller.py` → supply POs from CRM context

### 10.4 Analytics
- `analytics_controller.py` → aggregates calls, chats, emails per agent/branch/period
- KPI tracked: FRT, AHT, CSAT, QA score, SLA compliance, catalogue send rate

### 10.5 WhatsApp (UltraMsg integration)
- `addons/ultramsg_integration/` → separate addon for webhook reception
- Inbound messages arrive → POST `/api/crm/channels/messages/create`
- Outbound messages via reply → actual WhatsApp send delegated to UltraMsg API

### 10.6 Knowledge Base
- `knowledge_controller.py` → `/api/crm/kb/*`
- `crm_call_script.py` → scripts panel shown in call dialog (call-specific KB)

---

## Appendix: Cron Jobs Summary

| Cron Name | Interval | Model | Method |
|-----------|----------|-------|--------|
| Auto-notify Requested Items | 1 hour | `lugal.crm.requested.item` | `_cron_notify_requested_items` |
| Flag SLA-breached Messages | 5 min | `lugal.crm.omnichannel.message` | `_cron_flag_sla_breaches` |
| Daily Employee KPI Snapshot | 1 day | `lugal.crm.employee.kpi` | `_cron_daily_kpi_snapshot` |
| Reset Stale Agent Statuses ★ | 30 min | `lugal.crm.agent.status` | `_cron_reset_stale_statuses` |

---

*★ = added/created in this session*
