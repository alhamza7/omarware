# Lugal CRM — Developer Onboarding

**Stack:** Odoo 19 (Python backend) + React 18 (TypeScript frontend)  
**Protocol:** JSON-RPC 2.0 over HTTPS  
**Auth:** JWT Bearer token  
**Base URL (dev):** `http://localhost:8070`  
**Frontend dev server:** `http://localhost:5173` (Vite proxy → Odoo)

---

## 1. What is Lugal CRM?

A custom 360° customer relationship platform built on top of Odoo.  
It is **not** standard Odoo CRM — it lives in the `lugal_crm` addon and uses its own data models.

The system handles:
- **Customer management** — full profile card, pipeline stages, branches
- **Call centre** — log calls, AI summaries, QA scoring
- **Omnichannel messaging** — WhatsApp, Instagram, Telegram, etc.
- **Ticketing** — complaints, SLA deadlines, escalation
- **Tasks & follow-ups** — agent task board
- **Orders & invoices** — via POS bridge to `pos_perfume_custom`
- **Analytics** — KPIs, agent performance, pipeline reports
- **Knowledge base** — internal articles for agents
- **Workforce** — shifts and attendance

---

## 2. Authentication

### Login
```http
POST /lugal/auth/login
```
```json
{
  "jsonrpc": "2.0", "method": "call", "id": 1,
  "params": {
    "db": "lugal_local",
    "username": "admin",
    "password": "admin"
  }
}
```
Returns `access_token` (short-lived JWT) and `refresh_token`.

### Use token
All subsequent calls need the header:
```
Authorization: Bearer <access_token>
```

### Refresh
```http
POST /lugal/auth/refresh
params: { "refresh_token": "..." }
```

### Token expired?
Frontend (`apiClient.ts`) automatically retries once with a refreshed token on `401 Unauthorized`.

---

## 3. Request Format

Every endpoint is **JSON-RPC 2.0 POST**:

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "db": "lugal_local",
    "field_one": "value",
    "field_two": 42
  }
}
```

Every response wraps data in `result`:
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

On error:
```json
{ "result": { "success": false, "error": "Customer not found" } }
```

---

## 4. Data Model (core entities)

```
lugal.crm.customer          ← 360° customer card
    ├── lugal.crm.branch            (M2M) branches
    ├── lugal.crm.tag               (M2M) tags
    ├── lugal.crm.customer.stage    (M2O) pipeline stage
    ├── lugal.crm.channel.identity  (O2M) social handles
    ├── lugal.crm.call              (O2M) call log
    ├── lugal.crm.interaction       (O2M) activity timeline entries
    ├── lugal.crm.omnichannel.msg   (O2M) chat messages
    ├── lugal.crm.ticket            (O2M) support tickets
    ├── lugal.crm.task              (O2M) follow-ups / tasks
    └── res.partner (Odoo)          (M2O) linked Odoo contact
```

### Customer pipeline stages
`lead → interested → active → vip → dormant`

### Interaction types
`call | message | email | visit | note`

### Ticket status
`open → in_progress → resolved → closed`  
(also: `stale` for SLA breach)

### Task status
`open → in_progress → done | overdue`

---

## 5. Key API Endpoints

### Customers
| Method | Endpoint | What it does |
|---|---|---|
| POST | `/api/crm/customers/list` | Paginated customer list |
| POST | `/api/crm/customers/<id>` | Full customer detail (all arrays populated) |
| POST | `/api/crm/customers/create` | Create customer |
| POST | `/api/crm/customers/<id>/update` | Partial update |
| POST | `/api/crm/customers/<id>/delete` | Soft delete |
| POST | `/api/crm/customers/<id>/kanban_move` | Move to another stage |
| POST | `/api/crm/customers/search` | Quick search (name / phone / email) |

### Calls
| Method | Endpoint | What it does |
|---|---|---|
| POST | `/api/crm/customers/<id>/calls` | List calls for customer |
| POST | `/api/crm/calls/create` | Log a new call |
| POST | `/api/crm/calls/<id>/update` | Update call record |

### Tickets
| Method | Endpoint | What it does |
|---|---|---|
| POST | `/api/crm/customers/<id>/tickets` | List tickets |
| POST | `/api/crm/tickets/create` | Open a ticket |
| POST | `/api/crm/tickets/<id>/update` | Update ticket |

### Tasks (Follow-ups)
| Method | Endpoint | What it does |
|---|---|---|
| POST | `/api/crm/tasks/list` | Task board (filter by agent/branch) |
| POST | `/api/crm/tasks/create` | Create follow-up |
| POST | `/api/crm/tasks/<id>/update` | Update status / due date |

### Activity & Notes
| Method | Endpoint | What it does |
|---|---|---|
| POST | `/api/crm/customers/<id>/activity` | Merged timeline (calls + interactions + tickets) |
| POST | `/api/crm/customers/<id>/interactions` | Interaction list (filterable by type) |
| POST | `/api/crm/interactions/create` | Add an interaction / note |
| POST | `/api/crm/customers/<id>/note/add` | Quick sticky note |

### Orders / POS Bridge
| Method | Endpoint | What it does |
|---|---|---|
| POST | `/api/crm/pos/create_invoice` | Create POS order from CRM call dialog |

### Analytics
| Method | Endpoint | What it does |
|---|---|---|
| POST | `/api/crm/analytics/dashboard` | Summary KPIs |
| POST | `/api/crm/analytics/agent_performance` | Per-agent stats |
| POST | `/api/crm/analytics/pipeline` | Stage distribution |

### Config (Tags, Stages, Branches)
| Method | Endpoint | What it does |
|---|---|---|
| POST | `/api/crm/config/tags` | List / create tags |
| POST | `/api/crm/config/stages` | List stages |
| POST | `/api/crm/branches/list` | List branches |

---

## 6. Customer Detail Response (what the modal gets)

When you call `POST /api/crm/customers/<id>` you receive **one object** with everything:

```
customer
├── identity        name, phones, email
├── address         city, state, district, building, postal_code, country
├── billing         billing_address, shipping_address, billing_method
├── classification  stage, tags, vip, enterprise, rating
├── account_manager id, name, phone
├── branches[]      id, name, location, manager, phone  (full objects)
├── commerce        credit_limit, lifetime_value, total_orders
├── preferences     favorite_fragrance, preferred_contact_time/channel
├── social          instagram/tiktok/whatsapp/snapchat/twitter/telegram handles
├── channel_identities[]  full list with is_primary flag
├── attachments[]   id, name, mimetype, url, uploaded_by
├── samples[]       id, name, version, dateSent, image
├── activity_timeline[]   merged sorted: calls + interactions + tickets
├── call_log[]      date, time, duration, agent, type, notes, aiSummary
├── tickets[]       subject, status, priority, date, assignedTo
├── follow_ups[]    title, dueDate, assignedTo, assignedBy, priority, status
├── internal_notes[]      body, date, note_author
├── top_products[]  name, quantity, totalSpent, lastPurchase
└── payments[]      date, amount, method, invoiceId, status
```

> Arrays are **only populated on the detail endpoint**.  
> The list endpoint returns `[]` for all arrays (for speed).

---

## 7. Frontend Architecture

```
src/
├── shared/
│   └── services/
│       └── apiClient.ts     ← central HTTP client (JWT, refresh, rpc helper)
└── features/
    ├── auth/                ← login, token storage
    ├── customers/           ← kanban board, customer card, detail modal
    ├── calls/               ← call dialog, call log
    ├── tickets/             ← ticket list & form
    ├── tasks/               ← follow-up board
    ├── pos-invoice/         ← invoice creation from CRM
    └── analytics/           ← dashboard charts
```

**Rule:** No API calls inside `.tsx` files. All API calls live in `containers/` or `services/` files.

---

## 8. Backend Architecture

```
addons/lugal_crm/
├── models/              ← Odoo ORM models (one file per entity)
├── controllers/         ← HTTP/JSON-RPC route handlers
│   ├── _auth.py         ← JWT validation helper
│   ├── _error.py        ← uniform error response
│   ├── _audit.py        ← audit log writer
│   └── *.py             ← one controller per domain
├── security/
│   ├── groups.xml        ← role definitions
│   └── ir.model.access.csv
└── data/
    ├── crm_sequences.xml ← ticket number sequence
    └── crm_cron.xml      ← scheduled jobs
```

---

## 9. Roles & Permissions

| Role | Key | Can do |
|---|---|---|
| Agent | `group_lugal_crm_agent` | Manage own customers, log calls, create tickets |
| Supervisor | `group_lugal_crm_qa_supervisor` | All agent actions + QA reviews + team reports |
| General Manager | `group_lugal_crm_general_manager` | Full access to all CRM data |
| Admin | Odoo admin | Full access to everything |

All roles are checked server-side via `ensure_jwt_user_id()` + `_check_permission()` helpers.

---

## 10. Local Dev Setup

```bash
# Start Odoo
./venv/bin/python odoo-bin -c odoo_local.conf

# Odoo runs on port 8070
# Vite dev server proxies /api/* and /lugal/* → localhost:8070

# After changing Python files, Odoo reloads automatically (--dev=all in conf)
# After changing frontend files, Vite hot-reloads automatically

# Upgrade a specific module (e.g. after adding a new model field)
./venv/bin/python odoo-bin -c odoo_local.conf -u lugal_crm
```

**DB name:** `lugal_local`  
**Default login:** `admin / admin`  
**JWT login endpoint:** `POST /lugal/auth/login` (use `username` not `login`)

---

## 11. Common Patterns

### Soft delete
Every entity has `is_deleted = Boolean` and `active = Boolean`.  
Never use `unlink()` — always `write({'is_deleted': True, 'active': False})`.

### Audit log
Every create/update/delete writes to `lugal.crm.audit.log` automatically via `crm_audit()`.

### Customer ID resolution
The detail endpoint accepts **either** a CRM `id` or a `res.partner` `id`.  
This lets POS screens (which store `partner_id`) open the correct CRM card.

### API key in array fields
When an array field is missing from the API response, the UI shows `notInApi: [key]`.  
Always return `[]` (never `null` or omit the key) for array fields.
