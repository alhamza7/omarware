# Lugal CRM — Architecture & Module Connections

> **Odoo Version:** 19.0
> **Modules:** `lugal_auth` + `lugal_crm` + `lugal_supply`
> **Last Updated:** 2026-02-26

---

## 0. Architectural Principles (مبادئ معمارية)

### مبدأ ١ — JWT مركزي ومستقل

JWT يعيش في **`lugal_auth`** — موديول مخصص لا يحتوي أي business logic.
لا يأخذ أي موديول الـ JWT من موديول business آخر مثل `nbs_archive`.

```
lugal_auth  ←  the ONLY jwt issuer / verifier 
    ↑
lugal_crm   ←  depends on lugal_auth for auth (not nbs_archive)
```

### مبدأ ٢ — استقلالية الموديولات

كل موديول يعمل **بمفرده** بعد تثبيته. الاعتمادية الوحيدة الإلزامية هي `lugal_auth`
لأنها متخصصة في المصادقة فقط (لا تعتمد إلا على `base`).

### مبدأ ٣ — الربط يكون فقط في الجزء المتخصص

| الاحتياج | الموديول الصحيح | السبب |
|----------|----------------|-------|
| JWT / Auth | `lugal_auth` | متخصص في المصادقة |
| Containers / Vendors | `lugal_supply` | متخصص في سلسلة التوريد |
| POS Invoice | `pos_perfume_custom` (optional) | متخصص في نقاط البيع |
| Documents / Archive | `nbs_archive` | **لا يُربط** من CRM — غير ذي صلة |

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         NBS Odoo 19 Instance (:8070)                            │
│                                                                                 │
│  ┌──────────────────┐                                                           │
│  │   lugal_auth     │  ← centralized JWT (lugal.jwt.service)                   │
│  │  depends: base   │    /lugal/auth/login  /lugal/auth/refresh                 │
│  └──────────────────┘                                                           │
│           ↑ depends on                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        lugal_crm (Core CRM Module)                      │   │
│  │  15 Controllers  •  24 Models  •  2 Sequences  •  3 Cron Jobs           │   │
│  │  6 Security Groups  •  25 Access Rules                                   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│            │                │               │                                    │
│     depends on        depends on      depends on                                 │
│            ↓                ↓               ↓                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │lugal_supply  │  │   product    │  │    stock     │  │    mail      │       │
│  │ (Vendors +   │  │ (Pricelist + │  │ (Warehouse + │  │ (Chatter +   │       │
│  │  Containers) │  │  Products)   │  │  Stock Qty)  │  │  Tracking)   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                                                 │
│     OPTIONAL link (guarded by _pos_available())                                 │
│            ↓                                                                    │
│  ┌──────────────────────────────────┐                                          │
│  │      pos_perfume_custom          │                                          │
│  │  (POS Orders / Invoices / SAP)   │                                          │
│  │  Linked via pos_bridge_controller│                                          │
│  └──────────────────────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Module Dependency Tree

```
lugal_auth                  ← NEW standalone auth module
└── base                    (res.users, ir.config_parameter)

lugal_crm
├── base                    (res.users, res.partner, res.country, ir.sequence, ir.cron)
├── web                     (HTTP routing, JSON-RPC)
├── mail                    (mail.thread, mail.activity.mixin — tracking & chatter)
├── contacts                (res.partner extensions)
├── lugal_auth              ← JWT authentication (lugal.jwt.service) — NOT nbs_archive
│   └── provides:           verify_access_token(), user_id from token
│   └── provides:           POST /lugal/auth/login + /lugal/auth/refresh
├── product                 ← product.product, product.pricelist, uom.uom
│   └── used by:            price_list_controller, pos_bridge_controller
├── stock                   ← stock.warehouse, stock.quant, stock.location
│   └── used by:            pos_bridge_controller (live stock qty per warehouse)
└── lugal_supply            ← Sister module (always installed together)
    ├── lugal.supply.vendor     (Custom vendor cards with WhatsApp/WeChat)
    └── lugal.supply.container  (Shipping container tracking + clearance)

lugal_supply
├── base
└── mail                    (mail.thread for container tracking)

OPTIONAL (not in depends — runtime guard only):
└── pos_perfume_custom      ← POS Bridge — checked with _pos_available() guard
    ├── pos.perfume.order       (Create invoice from CRM call dialog)
    └── pos.perfume.order.line  (Invoice lines)
```

---

## 3. Data Model Map

### 3.1 Core CRM Models (lugal_crm)

```
lugal.crm.branch ──────────────────────────────────────────┐
│ id, name, name_ar, code, city, address                    │
│ phone, email, manager_id→res.users                        │
│ active, is_deleted                                        │
└── Referenced by: customer, call, ticket, task,            │
    message, PO, kpi, shift, attendance, tag, script        │
                                                            │
lugal.crm.customer.stage                                    │
│ id, name, name_ar, sequence, stage_type                   │
└── Referenced by: lugal.crm.customer.stage_id              │
                                                            │
lugal.crm.tag                                               │
│ id, name, name_ar, tag_type, color, sequence              │
└── M2M with: lugal.crm.customer                            │
                                                            │
lugal.crm.customer ◄────── Central 360° Card ──────────────┘
│ Identity: name, name_ar, phone_1/2/3, email, photo
│ Address: address, city, country_id→res.country
│ Partner: partner_id→res.partner (Odoo ERP link)
│ Pipeline: stage_id→stage, tag_ids→tags, vip_status
│ Finance: lifetime_value, credit_debt, credit_limit
│ Dates: member_since, last_call_date, last_purchase_date
│ Commerce: open_invoice_status, delivery_status
│ Products: most_purchased_item_ids→product.product
│ Location: shop_location, favorite_shipping_address, billing_address
│ Sample: sample_version, sample_date, sample_image
│ Docs: attachment_ids→ir.attachment
│ Branches: branch_ids→lugal.crm.branch
│ Staff: account_manager_id→res.users
│ Loyalty: referral_source, loyalty_points, preferences
│
├──┤ ONE-TO-MANY (via customer_id):
│  ├── lugal.crm.channel.identity  (social handles)
│  ├── lugal.crm.interaction       (activity log)
│  ├── lugal.crm.call              (call records)
│  ├── lugal.crm.ticket            (complaints/issues)
│  ├── lugal.crm.task              (follow-ups)
│  ├── lugal.crm.omnichannel.message (inbox messages)
│  ├── lugal.crm.requested.item    (out-of-catalog requests)
│  └── lugal.crm.qa.review         (QA review reference)
```

---

### 3.2 Communication Models

```
lugal.crm.channel.identity
│ customer_id→customer, channel (whatsapp/instagram/...), handle
│ is_primary, active, is_deleted
│ PURPOSE: Unified identity — same customer across channels

lugal.crm.call
│ customer_id→customer, agent_id→res.users, branch_id→branch
│ call_type (inbound/outbound), caller_number, channel
│ started_at, ended_at, duration_seconds, outcome
│ notes, ai_summary, qa_score, issues_found
│ recording_url, catalogue_sent, catalogue_sent_via
│ Financial snapshot: balance_at_call, outstanding_at_call, credit_limit_at_call
│ POS link: pos_order_id (int), pos_order_name, pos_order_total, pos_order_state
│ Ticket link: ticket_created_id→lugal.crm.ticket
│ active, is_deleted
│
├── LINKED TO: lugal.crm.qa.review (via call_id)
└── LINKED FROM: pos_bridge_controller writes pos_order_* fields

lugal.crm.call.queue
│ customer_id, caller_number, channel, status
│ Branch queue for multiple simultaneous incoming calls

lugal.crm.omnichannel.message
│ customer_id→customer, channel, direction (inbound/outbound)
│ channel_identity_id→channel.identity, content, media_url
│ sent_at, read_at, conversation_id (groups messages)
│ assigned_to_id→res.users, owner_id→res.users
│ status (pending/assigned/resolved)
│ replied_by_agent_at, sla_breached, waiting_customer_response
│ branch_id→branch
│
└── SLA CRON: _cron_flag_sla_breaches() every 5 min

lugal.crm.interaction
│ customer_id→customer, interaction_type, subject, body
│ channel, outcome, duration_seconds, interaction_date
│ agent_id→res.users, branch_id→branch
│ PURPOSE: Universal activity log (notes/calls/tasks/ticket comments)
```

---

### 3.3 Issue & Task Management

```
lugal.crm.ticket
│ ticket_number (TKT-NNNNN, auto via ir.sequence)
│ customer_id→customer, branch_id→branch
│ assigned_to_id→res.users, escalated_to_id→res.users
│ title, description, ticket_type, channel
│ status (open/in_progress/resolved/closed/stale)
│ priority (low/medium/high/urgent)
│ sla_deadline, first_response_at, resolved_at
│ active, is_deleted

lugal.crm.task
│ title, description, priority, status (open/in_progress/done/overdue)
│ customer_id→customer, assigned_to_id→res.users, created_by_id→res.users
│ branch_id→branch, due_date, reminder_date
│ active, is_deleted
```

---

### 3.4 Knowledge Base

```
lugal.crm.kb.article
│ title, title_ar, content, content_ar
│ category (document/policy/faq/announcement/training)
│ branch_id→branch, is_published, author_id→res.users

lugal.crm.kb.notification
│ title, title_ar, body, body_ar
│ notification_type (announcement/alert/update)
│ branch_ids (Many2many→branch), pushed_by_id→res.users

lugal.crm.call.script
│ title, title_ar, category (faq/objection/greeting/closing/escalation)
│ question, answer, branch_id→branch, sequence
│ is_active, active
```

---

### 3.5 Employee Management

```
lugal.crm.shift
│ name, name_ar, branch_id→branch
│ shift_type (morning/evening/night/split)
│ start_time (float), end_time (float)
│ user_ids (Many2many→res.users)

lugal.crm.attendance
│ employee_id→res.users, branch_id→branch, shift_id→shift
│ check_in, check_out, work_type (office/remote/field)
│ ip_address, device_type, location_lat/lng/label
│ duration_hours (computed)

lugal.crm.employee.kpi
│ employee_id→res.users, branch_id→branch
│ period_start, period_end
│ total_calls, answered_calls, total_messages, answered_messages
│ avg_frt_seconds, avg_ttr_seconds
│ late_messages, late_calls, conversions_to_order
│
└── CRON: _cron_daily_kpi_snapshot() every day

lugal.crm.message.template
│ name, channel, body, body_ar, category
│ branch_id→branch, requires_approval
│ PURPOSE: Quick-reply templates for agents
```

---

### 3.6 QA Review System

```
lugal.crm.qa.review
│ review_number (QA-NNNNN, auto via ir.sequence)
│ review_type (call/message)
│ call_id→lugal.crm.call (for call reviews)
│ conversation_id (for message thread reviews)
│ customer_id→customer, agent_id→res.users (reviewed)
│ reviewer_id→res.users (QA auditor), branch_id→branch
│ reviewed_at, listen_duration_seconds
│ Scores: score, greeting_score, product_knowledge_score,
│         problem_solving_score, professionalism_score, compliance_score
│ issues_found, qa_notes, feedback_to_agent
│ status (draft/submitted/acknowledged)
```

---

### 3.7 Audit Log (Immutable)

```
lugal.crm.audit.log
│ timestamp, user_id→res.users (readonly)
│ action (Selection: 45 CRM-specific actions)
│ customer_id→customer, branch_id→branch (readonly)
│ record_model, record_id, ip_address
│ details (JSON Text)
│
│ RULES:
│ - Cannot be deleted (SQL constraint + unlink override)
│ - Created via non-blocking log_action() helper
│ - Written from all 15 controllers via _audit.py helper
│
└── 45 logged actions:
    Customer: created/updated/deleted/stage_moved
    Call: created/ended/deleted/recording_attached
    Ticket: created/status_changed/assigned/escalated/deleted
    Task: created/status_changed/assigned/deleted
    Message: created/replied/resolved/transferred
    KB: article_created/deleted/notification_pushed
    Supply: po_created/deleted/vendor_created/deleted/container_created
    Config: tag/stage/script CRUD
    Branch: created/updated/deleted
    QA: review_created/submitted
```

---

### 3.8 Supply Chain (lugal_crm + lugal_supply)

```
lugal.supply.vendor  (in lugal_supply module)
│ name, name_ar, division (europe/china/other)
│ contact_name, phone, email, website
│ whatsapp, wechat, telegram  ← Vendor communication channels
│ payment_terms, currency_id→res.currency, lead_time_days
│ country_id→res.country, city, address
│ partner_id→res.partner (optional ERP link)

lugal.supply.container  (in lugal_supply module)
│ name, container_number, bl_number
│ clearance_company, origin_location
│ departure_date, eta, arrived_at
│ status (waiting/active/at_port/completed)
│ division (europe/china)
│ tracking_url (Searates or similar)
│ assigned_user_id→res.users, po_uploaded_by_id→res.users
│ clearance_info_delivered (Boolean — highlighted flag in UI)
│ clearance_info_delivered_at, clearance_info_delivered_by_id→res.users
│ attachment_ids (Many2many→ir.attachment)

lugal.crm.supply.po  (in lugal_crm module)
│ name, vendor_id→lugal.supply.vendor ← Cross-module FK
│ division (europe/china)
│ currency_id→res.currency
│ container_id→lugal.supply.container ← Cross-module FK
│ branch_id→lugal.crm.branch
│ status (draft/confirmed/shipped/received/cancelled)
│ total_amount (computed: sum of line_ids.total_price)
│ is_suggested (flag for suggested POs)
│
└── line_ids → lugal.crm.supply.po.line

lugal.crm.supply.po.line
│ po_id→lugal.crm.supply.po (required)
│ sequence, product_name, item_code, uom
│ quantity, unit_price, currency_id→res.currency
│ last_purchase_price, last_purchase_date ← Historical price reference
│ total_price (computed: quantity × unit_price)
│ min_qty, max_qty ← Inventory thresholds

lugal.crm.requested.item
│ customer_id→customer, product_name, notes
│ status (pending/notified/fulfilled/cancelled)
│ requested_at, notified_at
│
└── CRON: _cron_notify_requested_items() every hour
    (auto-notifies customers when item becomes available)
```

---

## 4. Controller → Model Mapping

```
┌───────────────────────────────┬────────────────────────────────────────────────────┐
│ Controller                    │ Models Accessed                                    │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ customer_controller           │ lugal.crm.customer                                 │
│                               │ lugal.crm.channel.identity                         │
│                               │ lugal.crm.interaction                              │
│                               │ lugal.crm.call (read)                              │
│                               │ lugal.crm.ticket (read)                            │
│                               │ lugal.crm.omnichannel.message (read)               │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ call_controller               │ lugal.crm.call                                     │
│                               │ lugal.crm.call.queue                               │
│                               │ lugal.crm.customer (update last_call_date)         │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ ticket_controller             │ lugal.crm.ticket                                   │
│                               │ lugal.crm.interaction (ticket notes)               │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ task_controller               │ lugal.crm.task                                     │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ channel_controller            │ lugal.crm.omnichannel.message                      │
│                               │ lugal.crm.channel.config                           │
│                               │ lugal.crm.channel.identity (read)                  │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ analytics_controller          │ lugal.crm.employee.kpi                             │
│                               │ lugal.crm.call (aggregate)                         │
│                               │ lugal.crm.ticket (aggregate)                       │
│                               │ lugal.crm.omnichannel.message (aggregate)          │
│                               │ lugal.crm.customer (aggregate)                     │
│                               │ lugal.crm.task (aggregate)                         │
│                               │ lugal.crm.audit.log                                │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ knowledge_controller          │ lugal.crm.kb.article                               │
│                               │ lugal.crm.kb.notification                          │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ config_controller             │ lugal.crm.tag                                      │
│                               │ lugal.crm.customer.stage                           │
│                               │ lugal.crm.call.script                              │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ branch_controller             │ lugal.crm.branch                                   │
│                               │ res.users (user assignment)                        │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ supply_controller             │ lugal.crm.supply.po                                │
│                               │ lugal.crm.supply.po.line                           │
│                               │ lugal.supply.vendor           ← lugal_supply       │
│                               │ lugal.supply.container        ← lugal_supply       │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ workforce_controller          │ lugal.crm.shift                                    │
│                               │ lugal.crm.attendance                               │
│                               │ lugal.crm.message.template                         │
│                               │ lugal.crm.customer (template render)               │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ price_list_controller         │ product.product              ← product module      │
│                               │ product.pricelist            ← product module      │
│                               │ product.category             ← product module      │
│                               │ uom.uom                      ← uom module          │
│                               │ lugal.crm.requested.item                           │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ pos_bridge_controller         │ pos.perfume.order            ← pos_perfume_custom  │
│                               │ pos.perfume.order.line       ← pos_perfume_custom  │
│                               │ product.product              ← product module      │
│                               │ product.pricelist            ← product module      │
│                               │ stock.warehouse              ← stock module        │
│                               │ stock.quant                  ← stock module        │
│                               │ res.partner                  ← base               │
│                               │ lugal.crm.call (write pos_order_*)                 │
│                               │ lugal.crm.customer (resolve partner_id)            │
│                               │ ir.config_parameter (exchange rate)                │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ delivery_controller           │ pos.perfume.order            ← pos_perfume_custom  │
│                               │ lugal.crm.customer (resolve to partner)            │
├───────────────────────────────┼────────────────────────────────────────────────────┤
│ qa_controller                 │ lugal.crm.qa.review                                │
│                               │ lugal.crm.call (read for review)                   │
└───────────────────────────────┴────────────────────────────────────────────────────┘
```

---

## 5. Authentication Flow

```
Frontend App
    │
    │  POST /lugal/auth/login  {username, password}
    │
    ▼
lugal_auth  →  LugalAuthController.login()
    │
    │  lugal.jwt.service.authenticate_user(username, password)
    │  → returns { access_token, refresh_token, token_type, user }
    │
    ▼
Frontend stores tokens, then calls CRM endpoints:

Frontend App
    │
    │  POST /api/crm/<any_endpoint>
    │  Headers: { Authorization: "Bearer <access_token>" }
    │
    ▼
lugal_crm Controller
    │
    │  uid = ensure_jwt_user_id()
    │        ← lugal_crm/controllers/_auth.py
    │          (thin re-export of lugal_auth/controllers/_auth.py)
    │  │
    │  │  1. Extract token from "Authorization: Bearer" header
    │  │  2. jwt_service = env['lugal.jwt.service'].sudo()  ← lugal_auth
    │  │  3. payload = jwt_service.verify_access_token(token)
    │  │  4. request.update_env(user=payload['user_id'])
    │  │
    │  if uid is None:
    │      return {'success': False, 'error': 'Unauthorized'}
    │
    ▼
Business Logic + ORM
    │
    ▼
crm_audit(action, ...)   ← controllers/_audit.py
    │
    │  env['lugal.crm.audit.log'].sudo().log_action(...)
    │
    ▼
Response {'success': True, 'data': {...}}
```

### Auth Endpoints (owned by lugal_auth)

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/lugal/auth/login` | Get access + refresh tokens |
| POST | `/lugal/auth/refresh` | Renew access token |

### JWT Config (ir.config_parameter)

| Key | Default | Description |
|-----|---------|-------------|
| `lugal_auth.jwt_secret_key` | `lugal-secret-…` | Access token signing key |
| `lugal_auth.jwt_refresh_secret_key` | `lugal-refresh-…` | Refresh token signing key |
| `lugal_auth.jwt_access_token_expire_minutes` | `480` (8 h) | Access token TTL |
| `lugal_auth.jwt_refresh_token_expire_days` | `7` | Refresh token TTL |

---

## 6. Cross-Module Integration Details

### 6.1 lugal_auth Integration (JWT — Centralized)

```
Module: lugal_auth
File:   addons/lugal_auth/models/lugal_jwt_service.py
        addons/lugal_auth/controllers/_auth.py   ← shared helper

lugal_auth provides:
  • Model: lugal.jwt.service (AbstractModel)
  • Methods: generate_access_token(), generate_refresh_token()
             verify_access_token(), verify_refresh_token()
             authenticate_user(), refresh_access_token()
  • Routes: POST /lugal/auth/login  +  POST /lugal/auth/refresh
  • Helper: ensure_jwt_user_id()  — imported by ALL Lugal modules

lugal_crm uses:
  • controllers/_auth.py  re-exports ensure_jwt_user_id from lugal_auth
  • All 15 controllers call ensure_jwt_user_id() as the first line
  • Token config stored in ir.config_parameter (not nbs_archive)

Why NOT nbs_archive:
  • nbs_archive is a DOCUMENT MANAGEMENT module — coupling auth to it
    would break lugal_crm whenever nbs_archive is not installed
  • Principle: cross-module coupling only for the specialised part
```

---

### 6.2 pos_perfume_custom Integration (POS Bridge)

```
Files:
  • addons/lugal_crm/controllers/pos_bridge_controller.py
  • addons/lugal_crm/controllers/delivery_controller.py

Integration pattern:
  def _pos_available():
      return 'pos.perfume.order' in request.env
  # All POS endpoints check this before proceeding

Models READ from pos_perfume_custom:
  • pos.perfume.order        — order list, last order, create order
  • pos.perfume.order.line   — order line items
  
  Accessed fields:
    order: id, name, state, date, amount_total, amount_total_iqd,
           partner_id, pricelist_id, invoice_type, exchange_rate,
           sale_order_id, sap_synced, order_line_ids
    line: product_id, product_uom_id, quantity, unit_price,
          discount_percent, warehouse_id, location_id

Models READ (shared with POS):
  • product.product          — product catalog, stock qty
  • product.pricelist        — pricing (USD/IQD)
  • stock.warehouse          — warehouse list + stock location
  • stock.quant              — live stock quantities
  • uom.uom                  — units of measure
  • res.partner              — customer ERP partner for order
  • ir.config_parameter      — exchange rate (pos_perfume.default_exchange_rate_usd_iqd)

Models WRITTEN in lugal_crm after POS order creation:
  • lugal.crm.call fields written:
      pos_order_id, pos_order_name, pos_order_total,
      pos_order_total_iqd, pos_order_state,
      pos_sale_order_name, pos_sap_synced

CRM Call Dialog Flow:
  1. Agent opens call → GET /api/crm/calls/create
  2. Agent wants to create invoice → GET /api/crm/pos/invoice_context
     → Returns: pricelists, warehouses, exchange rate, last order, partner_id
  3. Agent selects products → POST /api/crm/pos/product_detail
  4. Agent confirms → POST /api/crm/pos/orders/create
     → Creates pos.perfume.order + confirms it
     → Writes back pos_order_* fields to lugal.crm.call
  5. Agent ends call → POST /api/crm/calls/end
```

---

### 6.3 lugal_supply Integration (Supply Chain)

```
Module: lugal_supply (separate installable module)
Depends: base, mail

Models in lugal_supply:
  • lugal.supply.vendor
  • lugal.supply.container

Models in lugal_crm that reference lugal_supply:
  • lugal.crm.supply.po
      vendor_id → lugal.supply.vendor  (Many2one, required)
      container_id → lugal.supply.container (Many2one, optional)

Controller (in lugal_crm):
  • supply_controller.py manages ALL supply operations including
    both lugal_crm models AND lugal_supply models
  • This is intentional: single API surface for the frontend

Cross-module data flow:
  Vendor (lugal_supply) ←── PO (lugal_crm) ──→ Container (lugal_supply)
                              │
                              └── PO Lines (lugal_crm)
                                  last_purchase_price / last_purchase_date
                                  min_qty / max_qty (inventory thresholds)
```

---

### 6.4 product / stock Integration (Catalog)

```
Module dependencies: product, stock (in __manifest__.py depends)

product.product accessed by:
  • price_list_controller.py    — product catalog browsing
  • pos_bridge_controller.py    — product search + pricing
  • crm_customer.py             — most_purchased_item_ids (M2M)

product.pricelist accessed by:
  • price_list_controller.py    — pricelist selection
  • pos_bridge_controller.py    — price calculation per UoM

product.category accessed by:
  • price_list_controller.py    — brand/category filter

uom.uom accessed by:
  • pos_bridge_controller.py    — UoM-based pricing

stock.warehouse accessed by:
  • pos_bridge_controller.py    — warehouse list + stock location
  
stock.quant accessed by:
  • pos_bridge_controller.py    — live available qty per warehouse

No CRM models store product/stock data directly.
All product/stock data is fetched live via ORM at request time.
```

---

### 6.5 base (res.partner) Integration

```
res.partner is used in:
  • lugal.crm.customer.partner_id (Many2one, optional)
    → Links CRM customer to Odoo ERP partner
    → Used by pos_bridge_controller to find partner for invoices
    → Identity resolution: if no partner_id, search by phone

  • lugal.supply.vendor.partner_id (Many2one, optional)
    → Links supply vendor to Odoo ERP partner

  • pos_bridge_controller.py
    → request.env['res.partner'].search([phone/mobile conditions])
    → Identity resolution for invoice creation
```

---

## 7. Automated Processes (Cron Jobs)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Scheduled Jobs (ir.cron)                            │
├──────────────────────────────────────────────────────────────────────────────┤
│ 1. Auto-notify Requested Items           Every 1 HOUR                        │
│    Model: lugal.crm.requested.item                                           │
│    Method: _cron_notify_requested_items()                                    │
│    Logic: Checks pending requested items against current stock;              │
│           marks as 'notified' when item becomes available                    │
├──────────────────────────────────────────────────────────────────────────────┤
│ 2. Flag SLA-breached Messages             Every 5 MINUTES                    │
│    Model: lugal.crm.omnichannel.message                                      │
│    Method: _cron_flag_sla_breaches()                                         │
│    Logic: Finds pending/assigned messages older than channel SLA threshold;  │
│           sets sla_breached=True for supervisor alerts                       │
├──────────────────────────────────────────────────────────────────────────────┤
│ 3. Daily KPI Snapshot                     Every 1 DAY                        │
│    Model: lugal.crm.employee.kpi                                             │
│    Method: _cron_daily_kpi_snapshot()                                        │
│    Logic: Aggregates calls, messages, FRT, TTR per employee per day;         │
│           stores snapshot in lugal.crm.employee.kpi for reporting            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Security Architecture

### 8.1 Groups Hierarchy

```
                    ┌──────────────────────────┐
                    │  CRM General Manager     │ ← Full access, delete, export
                    │  (GM)                    │
                    └──────────────┬───────────┘
                                   │ implies
                    ┌──────────────▼───────────┐
                    │  CRM Manager             │ ← Settings, branches, supply chain
                    └──────────────┬───────────┘
                                   │ implies
                    ┌──────────────▼───────────┐
                    │  CRM Supervisor          │ ← View all agents, assign, manage
                    └──────────────┬───────────┘
                                   │ implies
                    ┌──────────────▼───────────┐
                    │  CRM Agent               │ ← Handle calls, messages, tickets
                    └──────────────────────────┘

    QA Track (separate):
                    ┌──────────────────────────┐
                    │  CRM QA Supervisor       │ ← View all QA, manage assignments
                    └──────────────┬───────────┘
                                   │ implies
                    ┌──────────────▼───────────┐
                    │  CRM QA Auditor          │ ← Listen, review, score
                    └──────────────────────────┘
```

### 8.2 Access Rules (ir.model.access.csv)

All 24 models grant `base.group_user` full CRUD by default. The security groups defined in `groups.xml` are used at the controller/business-logic level for permission checks.

| Model | Read | Write | Create | Delete |
|-------|------|-------|--------|--------|
| lugal.crm.branch | ✅ | ✅ | ✅ | ❌ (admin only) |
| lugal.crm.tag | ✅ | ✅ | ✅ | ❌ |
| lugal.crm.customer.stage | ✅ | ✅ | ✅ | ❌ |
| lugal.crm.customer | ✅ | ✅ | ✅ | ✅ (soft) |
| lugal.crm.call | ✅ | ✅ | ✅ | ✅ (soft) |
| lugal.crm.ticket | ✅ | ✅ | ✅ | ✅ (soft) |
| lugal.crm.task | ✅ | ✅ | ✅ | ✅ (soft) |
| lugal.crm.omnichannel.message | ✅ | ✅ | ✅ | ✅ (soft) |
| lugal.crm.audit.log | ✅ | ✅ | ✅ | ❌ (immutable) |
| lugal.crm.qa.review | ✅ | ✅ | ✅ | ✅ |
| lugal.supply.vendor | ✅ | ✅ | ✅ | ✅ (soft) |
| lugal.supply.container | ✅ | ✅ | ✅ | ✅ (soft) |

---

## 9. Soft-Delete Pattern

All operational models implement consistent soft-delete:

```python
# Every delete endpoint:
record.write({'is_deleted': True, 'active': False})

# Every list query domain includes:
[('is_deleted', '=', False)]

# Odoo's active field automatically filters in search:
active = False → excluded from default searches
```

**Exceptions:**
- `lugal.crm.audit.log` — **cannot be deleted** (SQL constraint)
- `lugal.crm.supply.po.line` — **hard delete** (lines are expendable)

---

## 10. File Structure

```
lugal_crm/
├── __init__.py
├── __manifest__.py
│     depends: [base, web, mail, contacts, nbs_archive, product, stock, lugal_supply]
│     data: [security/groups.xml, security/ir.model.access.csv,
│            data/crm_sequences.xml, data/crm_cron.xml]
│
├── models/
│   ├── __init__.py
│   ├── crm_branch.py                → lugal.crm.branch
│   ├── crm_tag.py                   → lugal.crm.tag
│   ├── crm_customer_stage.py        → lugal.crm.customer.stage
│   ├── crm_customer.py              → lugal.crm.customer  [mail.thread]
│   ├── crm_channel_identity.py      → lugal.crm.channel.identity  [mail.thread]
│   ├── crm_interaction.py           → lugal.crm.interaction  [mail.thread]
│   ├── crm_task.py                  → lugal.crm.task  [mail.thread]
│   ├── crm_ticket.py                → lugal.crm.ticket  [mail.thread] + ir.sequence
│   ├── crm_call.py                  → lugal.crm.call  [mail.thread]
│   ├── crm_call_script.py           → lugal.crm.call.script  [mail.thread]
│   ├── crm_call_queue.py            → lugal.crm.call.queue  [mail.thread]
│   ├── crm_omnichannel_message.py   → lugal.crm.omnichannel.message  [mail.thread] + cron
│   ├── crm_channel_config.py        → lugal.crm.channel.config  [mail.thread]
│   ├── crm_employee_kpi.py          → lugal.crm.employee.kpi  [mail.thread] + cron
│   ├── crm_kb_article.py            → lugal.crm.kb.article  [mail.thread]
│   ├── crm_kb_notification.py       → lugal.crm.kb.notification  [mail.thread]
│   ├── crm_supply_po.py             → lugal.crm.supply.po  [mail.thread]
│   ├── crm_supply_po_line.py        → lugal.crm.supply.po.line  [mail.thread]
│   ├── crm_requested_item.py        → lugal.crm.requested.item  [mail.thread] + cron
│   ├── crm_shift.py                 → lugal.crm.shift  [mail.thread]
│   ├── crm_attendance.py            → lugal.crm.attendance  [mail.thread]
│   ├── crm_message_template.py      → lugal.crm.message.template  [mail.thread]
│   ├── crm_audit_log.py             → lugal.crm.audit.log  (immutable)
│   └── crm_qa_review.py             → lugal.crm.qa.review  [mail.thread] + ir.sequence
│
├── controllers/
│   ├── __init__.py
│   ├── _auth.py                     ← JWT validation helper (uses nbs_archive)
│   ├── _audit.py                    ← Audit log helper
│   ├── customer_controller.py       ← /api/crm/customers/*  (16 endpoints)
│   ├── call_controller.py           ← /api/crm/calls/*       (10 endpoints)
│   ├── ticket_controller.py         ← /api/crm/tickets/*     (11 endpoints)
│   ├── task_controller.py           ← /api/crm/tasks/*       (8 endpoints)
│   ├── channel_controller.py        ← /api/crm/channels/*    (11 endpoints)
│   ├── analytics_controller.py      ← /api/crm/analytics/*   (9 endpoints)
│   ├── knowledge_controller.py      ← /api/crm/kb/*          (8 endpoints)
│   ├── config_controller.py         ← /api/crm/config/*      (13 endpoints)
│   ├── branch_controller.py         ← /api/crm/branches/*    (6 endpoints)
│   ├── supply_controller.py         ← /api/crm/supply/*      (21 endpoints)
│   ├── workforce_controller.py      ← /api/crm/shifts|attendance|templates/* (13 endpoints)
│   ├── price_list_controller.py     ← /api/crm/pricelist/*   (8 endpoints)
│   ├── pos_bridge_controller.py     ← /api/crm/pos/*         (7 endpoints)
│   ├── delivery_controller.py       ← /api/crm/delivery/*    (3 endpoints)
│   └── qa_controller.py             ← /api/crm/qa/*          (6 endpoints)
│
├── security/
│   ├── groups.xml                   ← 6 CRM Security Groups
│   └── ir.model.access.csv          ← 25 access rules
│
├── data/
│   ├── crm_sequences.xml            ← TKT-NNNNN + QA-NNNNN sequences
│   └── crm_cron.xml                 ← 3 scheduled jobs
│
├── CRM_API_COMPLETE.md              ← Full API documentation
└── CRM_ARCHITECTURE.md              ← This file

lugal_supply/
├── __init__.py
├── __manifest__.py
│     depends: [base, mail]
├── models/
│   ├── __init__.py
│   ├── lugal_supply_vendor.py       → lugal.supply.vendor  [mail.thread]
│   └── lugal_supply_container.py   → lugal.supply.container  [mail.thread]
└── security/
    └── ir.model.access.csv          ← 2 access rules
```

---

## 11. API Surface Summary

| Group | Base Path | Endpoints | Module |
|-------|-----------|-----------|--------|
| Customers | `/api/crm/customers/*` | 16 | lugal_crm |
| Calls | `/api/crm/calls/*` | 10 | lugal_crm |
| Tickets | `/api/crm/tickets/*` | 11 | lugal_crm |
| Tasks | `/api/crm/tasks/*` | 8 | lugal_crm |
| Omnichannel | `/api/crm/channels/*` | 11 | lugal_crm |
| Analytics | `/api/crm/analytics/*` | 9 | lugal_crm |
| Knowledge Base | `/api/crm/kb/*` | 8 | lugal_crm |
| Config | `/api/crm/config/*` | 13 | lugal_crm |
| Branches | `/api/crm/branches/*` | 6 | lugal_crm |
| Supply Chain | `/api/crm/supply/*` | 21 | lugal_crm |
| Workforce | `/api/crm/shifts|attendance|templates/*` | 13 | lugal_crm |
| Price List | `/api/crm/pricelist/*` | 8 | lugal_crm |
| POS Bridge | `/api/crm/pos/*` | 7 | lugal_crm |
| Delivery | `/api/crm/delivery/*` | 3 | lugal_crm |
| QA Reviews | `/api/crm/qa/*` | 6 | lugal_crm |
| **Total** | | **150 endpoints** | |
