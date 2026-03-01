# Lugal CRM — Development Plan (Updated)

> **Backend مكتمل — بعد مراجعة Excel CRM (3).xlsx وإصلاح الثغرات المكتشفة.**
> Frontend مستقل — مرحلة 2 منفصلة.

---

## مبادئ معمارية أساسية (Architectural Principles)

### ١. JWT مركزي ومستقل (Centralized, Decoupled JWT)

```
lugal_auth          ← الوحيد الذي يعرّف lugal.jwt.service
    ↑
lugal_crm           ← يعتمد على lugal_auth فقط (ليس nbs_archive)
    ↑
lugal_supply        ← لا controllers → لا حاجة لـ lugal_auth مباشرةً
```

- **`lugal_auth`** هو الموديول الوحيد المسؤول عن JWT — بدون أي business logic.
- **لا يحق لأي موديول business** (مثل `nbs_archive`) أن يكون مصدر الـ JWT لموديول آخر.
- الـ `lugal_crm/_auth.py` هو re-export لـ `lugal_auth/controllers/_auth.py` فقط.

### ٢. استقلالية الموديولات (Module Independence)

كل موديول يعمل بشكل كامل بدون الحاجة لتفعيل موديول آخر — ما عدا:
- **`lugal_auth`**: dependency وحيدة للـ JWT — وهي تعتمد على `base` فقط.
- **`lugal_supply`**: موديول بيانات فقط — لا controllers — يعمل وحده.
- **`pos_perfume_custom`** (اختياري): ربط POS محمي بـ guard `_pos_available()`.

### ٣. الربط بين الموديولات (Cross-Module Coupling)

الربط يكون **فقط في الجزء المتخصص** للموديول الآخر:

| الاستخدام | المقبول | الممنوع |
|-----------|---------|---------|
| JWT       | `lugal_auth` (متخصص في Auth) | `nbs_archive` (متخصص في Documents) |
| Containers | `lugal_supply` (متخصص في Supply) | داخل `lugal_crm` models |
| POS Invoice | `pos_perfume_custom` (متخصص في POS) | إعادة بناء منطق الفاتورة في CRM |

---

---

## نتائج مراجعة الـ Excel (CRM (3).xlsx) — تقرير المطابقة الشامل

### ✅ مُطابَق ومنفَّذ بالكامل

| الشيت | المتطلب | الموقع |
|-------|---------|--------|
| Customer Card | الهوية، الهاتف (1/2/3)، العنوان، Tags/VIP، LTV، الذمم | `crm_customer.py` |
| Customer Card | نسخة العينة + صورة + تاريخ | `crm_customer.py` |
| Customer Card | سجل المكالمات، التذاكر، Timeline | `crm_call`, `crm_ticket`, `crm_interaction` |
| Customer Card | مدير الحساب، الإحالة، نقاط الولاء، التفضيلات | `crm_customer.py` |
| Customer Card | **وثائق الهوية (attachment_ids)** ✅ مُضاف | `crm_customer.py` |
| Customer Card | عنوان الشحن المفضل + موقع المحل | `crm_customer.py` |
| Call Dialog | Inbound/Outbound، مدة المكالمة، الرصيد، السكريبت | `crm_call.py` + `call_controller` |
| Call Dialog | إنشاء فاتورة (POS Bridge)، فتح تذكرة، إرسال كتالوج | `pos_bridge_controller`, `ticket_controller` |
| Call Dialog | QA Score، Issues، AI Summary، تسجيل المكالمة | `crm_call.py` |
| Call Dialog | One-Click Wrap-Up (حقول post_call_notes) | `crm_call.py` |
| Omnichannel | رسائل متعددة القنوات، SLA، تعيين موظف، التحويل | `crm_omnichannel_message.py` + `channel_controller` |
| Omnichannel | نماذج الرسائل، queue المكالمات، ورديتان | `crm_message_template`, `crm_call_queue`, `crm_shift` |
| Employee KPI | المكالمات، الرسائل، FRT، TTR، المتأخرات، التحويلات | `crm_employee_kpi.py` |
| Knowledge Base | مقالات، إشعارات، سكريبت الأسئلة | `crm_kb_article`, `crm_kb_notification`, `crm_call_script` |
| Supply Chain | أوامر الشراء + بنودها (آخر سعر، min/max) | `crm_supply_po`, `crm_supply_po_line` |
| Supply Chain | بطاقة المورد (WhatsApp/WeChat/Telegram) | `lugal_supply_vendor.py` |
| Supply Chain | بطاقة الحاوية (B/L، clearance، Searates URL) | `lugal_supply_container.py` |
| Supply Chain | **علَم تسليم المعلومات للمخلص** ✅ مُضاف | `lugal_supply_container.py` |
| Supply Chain | **مرفقات الحاوية (attachment_ids)** ✅ مُضاف | `lugal_supply_container.py` |
| Admin Dashboard | Audit Log شامل (43 إجراء) | `crm_audit_log.py` |
| Admin Dashboard | **Security Groups (Agent/Supervisor/QA/GM)** ✅ مُضاف | `security/groups.xml` |
| Reports | Analytics: مكالمات، رسائل، FRT، تذاكر، فروع | `analytics_controller.py` |
| Tickets | Open/In Progress/Resolved/Closed | `crm_ticket.py` |
| Tickets | **نظام الترقيم التلقائي (TKT-00001)** ✅ مُضاف | `crm_sequences.xml` + `crm_ticket.py` |
| QA System | **QA Review Model كامل** ✅ مُضاف | `crm_qa_review.py` + `qa_controller.py` |

---

### ⚠️ متطلبات مرحلة مستقبلية (لا تمنع الإطلاق)

| الشيت | المتطلب | ملاحظة |
|-------|---------|--------|
| Supply Chain | Suggested PO (تحليل min/max تلقائي) | يحتاج خوارزمية تحليل + بيانات مخزون ERP |
| Supply Chain | Import from Excel to PO | مستوى Frontend + backend parsing |
| Supply Chain | Move PO to AP (ربط بالمحاسبة) | يحتاج Odoo `account` module integration |
| Supply Chain | Searates API فعلي (بدل URL يدوي) | يحتاج API key + webhook |
| Main Sheet | Broadcast & Campaigns | ميزة مستقلة — تحتاج sprint منفصل |
| Main Sheet | Skill-based routing | تحتاج بيانات مهارات الموظفين |
| Call Dialog | Debt Aging Breakdown (30/60/90 يوم) | يحتاج ربط مع نظام المحاسبة |
| Call Dialog | Customer discounts per brand/item | يحتاج discount model |
| Admin Dashboard | AI vs Human reports | مرتبط بميزة AI Bots (مستقبلية) |
| Reports | Export / Pivot-ready | مستوى Frontend |
| AI Bots Sheet | كل المتطلبات | مرحلة مستقبلية منفصلة |

---

## Module Location
- `addons/lugal_auth/` — **مركز المصادقة** JWT فقط — لا business logic (depends: `base`)
- `addons/lugal_crm/` — CRM core (**24 نموذج**، **15 controller**، 3 cron jobs، 2 sequences) (depends: `lugal_auth`, NOT `nbs_archive`)
- `addons/lugal_supply/` — Containers + Vendors (موردين وحاويات) — 2 نماذج (no controllers)

---

## Directory Structure (الوضع الحالي الكامل)

```
lugal_auth/                                 ← NEW: standalone JWT module
├── __init__.py
├── __manifest__.py                         depends: base ONLY
├── models/
│   ├── __init__.py
│   └── lugal_jwt_service.py                lugal.jwt.service (AbstractModel)
├── controllers/
│   ├── __init__.py
│   ├── _auth.py                            ensure_jwt_user_id() — reused by all Lugal modules
│   └── auth_controller.py                  POST /lugal/auth/login  +  POST /lugal/auth/refresh
└── security/
    └── ir.model.access.csv

lugal_crm/
├── __init__.py
├── __manifest__.py                         depends: base, web, mail, contacts, lugal_auth, product, stock, lugal_supply
├── models/
│   ├── __init__.py
│   ├── crm_branch.py                       lugal.crm.branch
│   ├── crm_tag.py                          lugal.crm.tag
│   ├── crm_customer_stage.py               lugal.crm.customer.stage
│   ├── crm_customer.py                     lugal.crm.customer  [+attachment_ids, +shop_location, +billing_address]
│   ├── crm_channel_identity.py             lugal.crm.channel.identity
│   ├── crm_interaction.py                  lugal.crm.interaction
│   ├── crm_task.py                         lugal.crm.task
│   ├── crm_ticket.py                       lugal.crm.ticket    [+ticket_number auto-sequence TKT-XXXXX]
│   ├── crm_call.py                         lugal.crm.call (+ recording_url, catalogue_sent_via, pos_order linkage)
│   ├── crm_call_script.py                  lugal.crm.call.script
│   ├── crm_call_queue.py                   lugal.crm.call.queue
│   ├── crm_omnichannel_message.py          lugal.crm.omnichannel.message (+ SLA, owner, waiting_customer_response)
│   ├── crm_channel_config.py               lugal.crm.channel.config (+ sla_threshold, work_hours)
│   ├── crm_employee_kpi.py                 lugal.crm.employee.kpi (+ _cron_daily_kpi_snapshot)
│   ├── crm_kb_article.py                   lugal.crm.kb.article (+ title_ar, content_ar)
│   ├── crm_kb_notification.py              lugal.crm.kb.notification
│   ├── crm_supply_po.py                    lugal.crm.supply.po (vendor_id → lugal.supply.vendor, total_amount computed)
│   ├── crm_supply_po_line.py               lugal.crm.supply.po.line (total_price computed)
│   ├── crm_requested_item.py               lugal.crm.requested.item (+ _cron_notify_requested_items)
│   ├── crm_shift.py                        lugal.crm.shift
│   ├── crm_attendance.py                   lugal.crm.attendance
│   ├── crm_message_template.py             lugal.crm.message.template
│   ├── crm_audit_log.py                    lugal.crm.audit.log (immutable, 45 actions)
│   └── crm_qa_review.py                    lugal.crm.qa.review  [NEW] QA scoring model
├── controllers/
│   ├── __init__.py
│   ├── _auth.py                            JWT helper (ensure_jwt_user_id)
│   ├── _audit.py                           audit log helper (crm_audit)
│   ├── customer_controller.py              16 endpoints — customer CRUD + 360° + channel identity + interactions
│   ├── task_controller.py                  8 endpoints  — task CRUD + assign + my tasks
│   ├── ticket_controller.py                11 endpoints — ticket CRUD + assign + escalate + notes
│   ├── call_controller.py                  10 endpoints — call CRUD + end + recording + queue
│   ├── channel_controller.py               11 endpoints — channel config CRUD + message inbox + conversation
│   ├── analytics_controller.py             8 endpoints  — dashboard + KPI + supervisor + CSV export
│   ├── knowledge_controller.py             8 endpoints  — articles + notifications
│   ├── config_controller.py                13 endpoints — tags CRUD + stages CRUD + scripts CRUD
│   ├── branch_controller.py                6 endpoints  — branch CRUD + user assign
│   ├── supply_controller.py                21 endpoints — PO CRUD + lines + vendors + containers + clearance flag
│   ├── workforce_controller.py             13 endpoints — shifts + attendance + message templates
│   ├── price_list_controller.py            8 endpoints  — product catalog + requested items
│   ├── pos_bridge_controller.py            7 endpoints  — POS invoice/products/orders
│   ├── delivery_controller.py              3 endpoints  — POS order tracking per customer
│   └── qa_controller.py                    6 endpoints  — QA review CRUD + submit + stats  [NEW]
├── security/
│   ├── groups.xml                          6 Security Groups (Agent/Supervisor/Manager/GM/QA/QA-Supervisor)  [NEW]
│   └── ir.model.access.csv                 25 access rules (all 24 models + QA covered)
├── data/
│   ├── crm_sequences.xml                   ir.sequence for TKT-XXXXX + QA-XXXXX  [NEW]
│   └── crm_cron.xml                        3 cron jobs
└── requirements/
    └── PLAN.md

lugal_supply/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── lugal_supply_container.py           lugal.supply.container
│   └── lugal_supply_vendor.py              lugal.supply.vendor
└── security/
    └── ir.model.access.csv                 2 access rules
```

---

## Backend Status — مكتمل بالكامل ✅

| # | Area | Files | Endpoints | Status |
|---|------|-------|-----------|--------|
| 1 | Core Models (branch, tag, stage, customer, channel identity) | 5 models | — | ✅ |
| 2 | Activity Models (interaction, task, ticket) | 3 models | — | ✅ |
| 3 | Call Centre (call + queue + script) | 3 models | — | ✅ |
| 4 | Omnichannel (message + channel config + SLA) | 2 models | — | ✅ |
| 5 | KPIs + Knowledge Base | 3 models | — | ✅ |
| 6 | Supply Chain (PO + lines in CRM; containers + vendors in lugal_supply) | 4 models | — | ✅ |
| 7 | Workforce (shifts + attendance + templates) | 3 models | — | ✅ |
| 8 | Customer 360° API | customer_controller | 16 | ✅ |
| 9 | Tasks API | task_controller | 8 | ✅ |
| 10 | Tickets API | ticket_controller | 11 | ✅ |
| 11 | Calls API + Queue | call_controller | 10 | ✅ |
| 12 | Omnichannel API | channel_controller | 11 | ✅ |
| 13 | Analytics + KPI + CSV Export + Audit Log | analytics_controller | 9 | ✅ |
| 14 | Knowledge Base API | knowledge_controller | 8 | ✅ |
| 15 | Config Lookups (Tags + Stages + Scripts) | config_controller | 13 | ✅ |
| 16 | Branch API | branch_controller | 6 | ✅ |
| 17 | Supply Chain API (PO + lines + vendors + containers) | supply_controller | 20 | ✅ |
| 18 | Workforce API (shifts + attendance + templates) | workforce_controller | 13 | ✅ |
| 19 | Price List + Requested Items API | price_list_controller | 8 | ✅ |
| 20 | POS Bridge API | pos_bridge_controller | 7 | ✅ |
| 21 | Delivery Tracking API | delivery_controller | 3 | ✅ |
| 22 | Security (ir.model.access) | ir.model.access.csv | 24 models covered | ✅ |
| 23 | Cron Jobs (3) | crm_cron.xml | — | ✅ |
| 24 | Audit Logging | crm_audit_log.py + _audit.py | 31 audit calls | ✅ |
| 25 | Audit Log API | analytics_controller | +1 endpoint | ✅ |
| 26 | API Documentation | CRM_API_GUIDE.md | 15 sections | ✅ |
| 27 | Frontend (React app) | — | — | 🔜 Phase 2 |

**Total: 25 Models · 14 Controllers · 143 API Endpoints · 31 Audit Calls · 3 Cron Jobs**

---

## Conventions (matching nbs_archive)

- API routes: `type='json'`, `auth='none'`, `csrf=False`, `methods=['POST']`
- JWT auth: `ensure_jwt_user_id()` from `_auth.py` — token sent in **HTTP header**: `Authorization: Bearer <token>`
- Soft-delete: `is_deleted` field on all models; `active=False` on archive
- Response format: `{'success': True/False, 'data': ..., 'error': '...'}`
- Arabic + English bilingual field labels on all models
- All API functions use `try/except` with `_logger.exception()`

---

## API Routes Summary (142 endpoints)

### Customer — `/api/crm/customers/*` (16)
| Route | Description |
|-------|-------------|
| `POST /api/crm/customers/list` | List with filters (stage, branch, VIP, search) |
| `POST /api/crm/customers/search` | Quick search by name/phone/email |
| `POST /api/crm/customers/create` | Create customer |
| `POST /api/crm/customers/<id>` | Get customer |
| `POST /api/crm/customers/<id>/update` | Update customer |
| `POST /api/crm/customers/<id>/delete` | Soft delete |
| `POST /api/crm/customers/<id>/kanban_move` | Move to pipeline stage |
| `POST /api/crm/customers/<id>/activity` | Full 360° activity timeline |
| `POST /api/crm/customers/<id>/calls` | Call history |
| `POST /api/crm/customers/<id>/tickets` | Ticket history |
| `POST /api/crm/customers/<id>/note/add` | Add quick note |
| `POST /api/crm/customers/<id>/interactions` | Full interaction log |
| `POST /api/crm/interactions/create` | Create standalone interaction |
| `POST /api/crm/customers/<id>/channel_identity/add` | Add social handle |
| `POST /api/crm/customers/<id>/channel_identity/<ci_id>/update` | Update handle |
| `POST /api/crm/customers/<id>/channel_identity/<ci_id>/delete` | Delete handle |

### Tasks — `/api/crm/tasks/*` (8)
| Route | Description |
|-------|-------------|
| `POST /api/crm/tasks/list` | List all tasks (filters: customer, branch, assignee, status, priority, overdue) |
| `POST /api/crm/tasks/<id>` | Get single task |
| `POST /api/crm/tasks/create` | Create task |
| `POST /api/crm/tasks/<id>/update` | Update task fields |
| `POST /api/crm/tasks/<id>/update_status` | Set status (open/in_progress/done/overdue) |
| `POST /api/crm/tasks/<id>/assign` | Reassign task |
| `POST /api/crm/tasks/<id>/delete` | Soft delete |
| `POST /api/crm/tasks/my` | Tasks assigned to current user |

### Tickets — `/api/crm/tickets/*` (11)
| Route | Description |
|-------|-------------|
| `POST /api/crm/tickets/list` | List with filters |
| `POST /api/crm/tickets/search` | Search tickets |
| `POST /api/crm/tickets/<id>` | Get ticket |
| `POST /api/crm/tickets/create` | Create ticket |
| `POST /api/crm/tickets/<id>/update` | Update ticket |
| `POST /api/crm/tickets/<id>/update_status` | Change status |
| `POST /api/crm/tickets/<id>/assign` | Assign to agent |
| `POST /api/crm/tickets/<id>/escalate` | Escalate ticket |
| `POST /api/crm/tickets/<id>/delete` | Soft delete |
| `POST /api/crm/tickets/<id>/note/add` | Add internal note |
| `POST /api/crm/tickets/<id>/notes` | List notes |

### Calls — `/api/crm/calls/*` (10)
| Route | Description |
|-------|-------------|
| `POST /api/crm/calls/list` | List calls |
| `POST /api/crm/calls/<id>` | Get call |
| `POST /api/crm/calls/create` | Log new call |
| `POST /api/crm/calls/<id>/end` | End call (duration, outcome) |
| `POST /api/crm/calls/<id>/update` | Update call |
| `POST /api/crm/calls/<id>/delete` | Soft delete |
| `POST /api/crm/calls/<id>/attach_recording` | Attach recording URL |
| `POST /api/crm/calls/queue/list` | List call queue |
| `POST /api/crm/calls/queue/add` | Add incoming call to queue |
| `POST /api/crm/calls/queue/<id>/assign` | Assign queue item to agent |

### Omnichannel — `/api/crm/channels/*` (11)
| Route | Description |
|-------|-------------|
| `POST /api/crm/channels/config_list` | List channel configs |
| `POST /api/crm/channels/config/create` | Create channel config |
| `POST /api/crm/channels/config/<id>/update` | Update config (SLA, work hours) |
| `POST /api/crm/channels/config/<id>/delete` | Delete config |
| `POST /api/crm/channels/messages/list` | Inbox with filters (channel, status, SLA, branch) |
| `POST /api/crm/channels/messages/create` | Create incoming message |
| `POST /api/crm/channels/messages/<id>/assign` | Assign message to agent |
| `POST /api/crm/channels/messages/<id>/reply` | Agent reply (sets FRT + waiting_customer_response) |
| `POST /api/crm/channels/messages/<id>/resolve` | Resolve conversation |
| `POST /api/crm/channels/messages/<id>/transfer` | Transfer to another agent |
| `POST /api/crm/channels/conversation/<conversation_id>` | Full thread view |

### Analytics — `/api/crm/analytics/*` (8)
| Route | Description |
|-------|-------------|
| `POST /api/crm/analytics/dashboard_stats` | Main dashboard KPIs |
| `POST /api/crm/analytics/channel_report` | Per-channel message + call stats |
| `POST /api/crm/analytics/branch_report` | Per-branch stats |
| `POST /api/crm/analytics/employee_kpi` | KPI for one employee (snapshot or live) |
| `POST /api/crm/analytics/all_employees_kpi` | All employees KPI table |
| `POST /api/crm/analytics/supervisor_dashboard` | Supervisor real-time panel |
| `POST /api/crm/analytics/ai_vs_human` | AI vs human interaction report |
| `POST /api/crm/analytics/export_kpi` | Export KPI as CSV file (HTTP) |

### Knowledge Base — `/api/crm/kb/*` (8)
| Route | Description |
|-------|-------------|
| `POST /api/crm/kb/articles/list` | List articles |
| `POST /api/crm/kb/articles/search` | Search articles |
| `POST /api/crm/kb/articles/<id>` | Get article |
| `POST /api/crm/kb/articles/create` | Create article (title_ar + content_ar) |
| `POST /api/crm/kb/articles/<id>/update` | Update article |
| `POST /api/crm/kb/articles/<id>/delete` | Delete article |
| `POST /api/crm/kb/notifications/list` | List notifications |
| `POST /api/crm/kb/notifications/push` | Push notification to users |

### Config / Lookups — `/api/crm/config/*` (13)
| Route | Description |
|-------|-------------|
| `POST /api/crm/config/tags/list` | List tags (filter by tag_type) |
| `POST /api/crm/config/tags/create` | Create tag |
| `POST /api/crm/config/tags/<id>/update` | Update tag |
| `POST /api/crm/config/tags/<id>/delete` | Delete tag |
| `POST /api/crm/config/stages/list` | List pipeline stages |
| `POST /api/crm/config/stages/create` | Create stage |
| `POST /api/crm/config/stages/<id>/update` | Update stage |
| `POST /api/crm/config/stages/<id>/delete` | Delete stage |
| `POST /api/crm/config/scripts/list` | List call scripts/FAQ |
| `POST /api/crm/config/scripts/<id>` | Get script |
| `POST /api/crm/config/scripts/create` | Create script |
| `POST /api/crm/config/scripts/<id>/update` | Update script |
| `POST /api/crm/config/scripts/<id>/delete` | Delete script |

### Branches — `/api/crm/branches/*` (6)
`POST /api/crm/branches/list` · `create` · `<id>` · `<id>/update` · `<id>/user_assign` · `<id>/delete`

### Supply Chain — `/api/crm/supply/*` (20)
| Route | Description |
|-------|-------------|
| `POST /api/crm/supply/containers/list` | List containers |
| `POST /api/crm/supply/containers/<id>` | Get container |
| `POST /api/crm/supply/containers/create` | Create container |
| `POST /api/crm/supply/containers/<id>/update` | Update container |
| `POST /api/crm/supply/containers/<id>/delete` | Delete container |
| `POST /api/crm/supply/po/list` | List POs |
| `POST /api/crm/supply/po/<id>` | Get PO with lines |
| `POST /api/crm/supply/po/create` | Create PO |
| `POST /api/crm/supply/po/<id>/update` | Update PO |
| `POST /api/crm/supply/po/<id>/delete` | Soft delete PO |
| `POST /api/crm/supply/po/<id>/lines` | List PO lines |
| `POST /api/crm/supply/po/<id>/lines/add` | Add line to PO |
| `POST /api/crm/supply/po/<id>/lines/<lid>/update` | Update line |
| `POST /api/crm/supply/po/<id>/lines/<lid>/delete` | Delete line |
| `POST /api/crm/supply/po/suggested` | Suggested POs based on history |
| `POST /api/crm/supply/vendors/list` | List vendors |
| `POST /api/crm/supply/vendors/<id>` | Get vendor |
| `POST /api/crm/supply/vendors/create` | Create vendor |
| `POST /api/crm/supply/vendors/<id>/update` | Update vendor |
| `POST /api/crm/supply/vendors/<id>/delete` | Delete vendor |

### Workforce — `/api/crm/shifts|attendance|templates/*` (13)
| Route | Description |
|-------|-------------|
| `POST /api/crm/shifts/list` | List shifts |
| `POST /api/crm/shifts/create` | Create shift |
| `POST /api/crm/shifts/<id>/update` | Update shift |
| `POST /api/crm/shifts/<id>/delete` | Delete shift |
| `POST /api/crm/attendance/check_in` | Employee check-in |
| `POST /api/crm/attendance/check_out` | Employee check-out |
| `POST /api/crm/attendance/list` | List attendance records |
| `POST /api/crm/attendance/live_status` | Who is currently online |
| `POST /api/crm/templates/list` | List message templates |
| `POST /api/crm/templates/create` | Create template |
| `POST /api/crm/templates/<id>/update` | Update template |
| `POST /api/crm/templates/<id>/delete` | Delete template |
| `POST /api/crm/templates/<id>/render` | Render template with customer variables |

### Price List — `/api/crm/pricelist/*` (8)
| Route | Description |
|-------|-------------|
| `POST /api/crm/pricelist/categories` | Product categories / brands |
| `POST /api/crm/pricelist/pricelists` | Available pricelists |
| `POST /api/crm/pricelist/products` | Products list (brand/UoM/pricelist/search/discount/new) |
| `POST /api/crm/pricelist/products/<id>` | Product detail + UoM prices + stock |
| `POST /api/crm/pricelist/requested_items` | List out-of-catalog requests |
| `POST /api/crm/pricelist/requested_items/create` | Create catalog request |
| `POST /api/crm/pricelist/requested_items/<id>/update_status` | Update status (pending/notified/fulfilled/cancelled) |
| `POST /api/crm/pricelist/requested_items/<id>/delete` | Delete request |

### POS Bridge — `/api/crm/pos/*` (7)
| Route | Description |
|-------|-------------|
| `POST /api/crm/pos/invoice_context` | Setup data (warehouses, pricelists, UoMs) |
| `POST /api/crm/pos/products` | POS product list with pricelist pricing |
| `POST /api/crm/pos/product_detail` | Single product detail |
| `POST /api/crm/pos/uom_price` | Price for specific UoM |
| `POST /api/crm/pos/orders/create` | Create POS order from CRM call |
| `POST /api/crm/pos/orders/<id>` | Get POS order |
| `POST /api/crm/pos/customer_orders` | Customer's POS order history |

### Delivery Tracking — `/api/crm/delivery/*` (3)
| Route | Description |
|-------|-------------|
| `POST /api/crm/delivery/customer_orders` | POS orders for customer |
| `POST /api/crm/delivery/order/<id>` | Order detail + delivery status |
| `POST /api/crm/delivery/orders/search` | Search orders |

---

## Cron Jobs
| Job | Interval | Method |
|-----|----------|--------|
| Auto-notify requested items | كل ساعة | `lugal.crm.requested.item._cron_notify_requested_items()` |
| Flag SLA breaches | كل 5 دقائق | `lugal.crm.omnichannel.message._cron_flag_sla_breaches()` |
| Daily KPI snapshot | يومياً | `lugal.crm.employee.kpi._cron_daily_kpi_snapshot()` |

---

---

## Audit Logging Coverage
| Controller | Audited Actions |
|-----------|----------------|
| customer_controller | created, updated, deleted, stage_moved |
| call_controller | created, ended, deleted, recording_attached |
| ticket_controller | created, status_changed, assigned, escalated, deleted |
| task_controller | created, status_changed, assigned, deleted |
| channel_controller | message_created, replied, resolved, transferred |
| supply_controller | po_created, po_deleted, vendor_created, vendor_deleted, container_created |
| knowledge_controller | article_created, article_deleted, notification_pushed |

**Supervisor audit trail:** `POST /api/crm/analytics/audit_log`
Params: `page, per_page, action, user_id, customer_id, branch_id, date_from, date_to`

---

## Pending — Phase 2 (Frontend)
- [ ] React frontend application (feature-based architecture)
- [ ] Authentication screens (login/JWT)
- [ ] Customer 360° card page
- [ ] Call centre interface
- [ ] Omnichannel inbox
- [ ] Analytics dashboard
- [ ] Supply chain management screens
