# User Roles & Permissions API — Frontend Integration Guide

> **Base URL:** `http://<server>:8069`  
> **Protocol:** JSON-RPC 2.0  
> **Auth:** `Authorization: Bearer <jwt_token>` header on every request  
> **Content-Type:** `application/json`

---

## Overview — How Permissions Work (3-Layer System)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERMISSION RESOLUTION                         │
│                                                                 │
│  Layer 1 (lowest)  CRM System Role / Odoo Group                 │
│    ↓ overridden by                                               │
│  Layer 2           Job-Title Template                            │
│    ↓ overridden by                                               │
│  Layer 3 (highest) Individual User Override                      │
│                                                                 │
│  Result = deep_merge(layer1, layer2, layer3)                     │
└─────────────────────────────────────────────────────────────────┘
```

| Layer | Source | Who controls |
|-------|--------|--------------|
| 1 | CRM role (agent / supervisor / manager / general_manager / qa_*) | Admin via `assign_role` |
| 2 | Job-title template linked to `user.job_title` | Admin via `job_titles/upsert` |
| 3 | Per-user override stored for just this employee | Admin via `permissions/set` |

**Key rule:** Higher layers always win. An individual override `create: true` beats a job-title template `create: false`.

---

## Quick Start for the FE

### 1 — On Login: fetch current user's permissions

```http
POST /api/crm/me/permissions
Authorization: Bearer <token>
Content-Type: application/json

{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

Store the `data.permissions` object in your Redux / context store. Every UI control checks against it.

```typescript
// pseudocode
const { data } = await api.post('/api/crm/me/permissions');
store.dispatch(setPermissions(data.permissions));
store.dispatch(setUserRole(data.role));
store.dispatch(setJobTitle(data.job_title));
```

### 2 — Guard UI elements

```typescript
// Check a single action
const canCreate = permissions?.supply_chain?.containers?.create ?? false;

// Helper
function can(path: string): boolean {
  return path.split('.').reduce((obj, key) => obj?.[key], permissions) === true;
}

can('supply_chain.containers.create')   // → true / false
can('supply_chain.po.confirm')           // → true / false
can('admin.users.assign_role')           // → true / false
```

---

## Full Permission Tree

Every leaf is a `boolean`. The FE receives the entire tree in every permissions response.  
The system covers **10 modules**: supply_chain, crm, qa, pos, hr, inventory, finance, analytics, settings, admin.

```jsonc
{
  // ── SUPPLY CHAIN ──────────────────────────────────────────────────────────
  "supply_chain": {
    "containers": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool,
      "assign_driver": bool, "mark_arrived": bool, "clearance_delivered": bool,
      "set_reminder": bool, "upload_attachment": bool, "delete_attachment": bool,
      "add_comment": bool, "delete_comment": bool, "add_penalty": bool, "delete_penalty": bool
    },
    "vendors":  { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool },
    "po": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool,
      "submit": bool, "confirm": bool, "ship": bool, "receive": bool,
      "cancel": bool, "reopen": bool,
      "add_line": bool, "edit_line": bool, "delete_line": bool,
      "upload_attachment": bool, "delete_attachment": bool,
      "add_comment": bool, "delete_comment": bool, "export_pdf": bool
    },
    "negotiations": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool,
      "add_comment": bool, "delete_comment": bool
    },
    "item_requests": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool,
      "approve": bool, "reject": bool, "fulfill": bool
    },
    "clearance_companies": { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool },
    "tracking":      { "view": bool, "update": bool },
    "minmax":        { "list": bool, "edit": bool, "delete": bool },
    "penalties":     { "list": bool, "add": bool, "delete": bool },
    "notifications": { "list": bool, "mark_read": bool, "delete": bool },
    "chat":          { "view": bool, "send": bool, "delete_message": bool },
    "stories":       { "list": bool, "view": bool, "create": bool, "delete": bool }
  },

  // ── CRM ───────────────────────────────────────────────────────────────────
  "crm": {
    "customers": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool,
      "export": bool, "import": bool, "merge": bool
    },
    "calls":   { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "listen_recording": bool },
    "tickets": { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "assign": bool, "escalate": bool, "close": bool },
    "tasks":   { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "assign": bool, "close": bool },
    "analytics":   { "view": bool, "export": bool, "view_team_data": bool },
    "config":      { "view": bool, "edit": bool },
    "branches":    { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool },
    "knowledge":   { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool },
    "omnichannel": { "view": bool, "reply": bool, "assign": bool },
    "shifts":      { "view": bool, "manage": bool }
  },

  // ── QA ────────────────────────────────────────────────────────────────────
  "qa": {
    "reviews":    { "list": bool, "view": bool, "create": bool, "score": bool, "delete": bool, "export": bool },
    "management": { "view": bool, "manage": bool, "assign_reviewer": bool },
    "reports":    { "view": bool, "export": bool }
  },

  // ── POINT OF SALE ─────────────────────────────────────────────────────────
  "pos": {
    "sessions":  { "list": bool, "view": bool, "open": bool, "close": bool },
    "orders":    { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "refund": bool, "export_pdf": bool },
    "products":  { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "set_price": bool, "set_discount": bool },
    "customers": { "list": bool, "view": bool, "create": bool, "edit": bool },
    "payments":  { "view": bool, "process": bool, "refund": bool },
    "reports":   { "view": bool, "export": bool, "z_report": bool },
    "config":    { "view": bool, "edit": bool }
  },

  // ── HUMAN RESOURCES ───────────────────────────────────────────────────────
  "hr": {
    "employees":   { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "view_salary": bool, "view_private": bool, "export": bool },
    "attendance":  { "view_own": bool, "view_all": bool, "edit": bool, "export": bool },
    "leaves":      { "view_own": bool, "view_all": bool, "request": bool, "approve": bool, "refuse": bool, "manage_allocation": bool },
    "payroll":     { "view_own": bool, "view_all": bool, "compute": bool, "validate": bool, "export": bool },
    "recruitment": { "view": bool, "create": bool, "manage": bool, "delete": bool },
    "kpi":         { "view_own": bool, "view_all": bool, "set": bool, "export": bool },
    "shifts":      { "view_own": bool, "view_all": bool, "manage": bool },
    "org_chart":   { "view": bool },
    "config":      { "view": bool, "edit": bool }
  },

  // ── INVENTORY / STOCK ─────────────────────────────────────────────────────
  "inventory": {
    "products":    { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "set_price": bool, "import": bool, "export": bool },
    "stock":       { "view": bool, "adjust": bool, "transfer": bool, "scrap": bool, "view_valuation": bool },
    "transfers":   { "list": bool, "view": bool, "create": bool, "validate": bool, "cancel": bool, "delete": bool },
    "warehouses":  { "view": bool, "create": bool, "edit": bool, "delete": bool },
    "locations":   { "view": bool, "create": bool, "edit": bool, "delete": bool },
    "lots_serials":{ "view": bool, "create": bool, "edit": bool },
    "reports":     { "view": bool, "export": bool },
    "config":      { "view": bool, "edit": bool }
  },

  // ── FINANCE / ACCOUNTING ──────────────────────────────────────────────────
  "finance": {
    "invoices":       { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "confirm": bool, "cancel": bool, "register_payment": bool, "export_pdf": bool },
    "bills":          { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "confirm": bool, "cancel": bool, "register_payment": bool },
    "payments":       { "list": bool, "view": bool, "create": bool, "validate": bool, "cancel": bool },
    "journals":       { "view": bool, "create": bool, "edit": bool, "delete": bool },
    "accounts":       { "view": bool, "create": bool, "edit": bool },
    "reports":        { "profit_loss": bool, "balance_sheet": bool, "cash_flow": bool, "tax_report": bool, "export": bool },
    "bank_statements":{ "view": bool, "import": bool, "reconcile": bool },
    "config":         { "view": bool, "edit": bool }
  },

  // ── ANALYTICS / DASHBOARDS ────────────────────────────────────────────────
  "analytics": {
    "dashboards":   { "view": bool, "create": bool, "edit": bool, "delete": bool, "share": bool },
    "reports":      { "view": bool, "create": bool, "export": bool },
    "kpi":          { "view": bool, "manage": bool },
    "spreadsheets": { "view": bool, "create": bool, "edit": bool, "delete": bool }
  },

  // ── SYSTEM SETTINGS ───────────────────────────────────────────────────────
  "settings": {
    "general":         { "view": bool, "edit": bool },
    "users_companies": { "view": bool, "manage": bool },
    "integrations":    { "view": bool, "manage": bool },
    "email":           { "view": bool, "configure": bool },
    "sap_integration": { "view": bool, "sync": bool, "configure": bool }
  },

  // ── ADMIN PANEL ───────────────────────────────────────────────────────────
  "admin": {
    "users":       { "list": bool, "view": bool, "create": bool, "assign_role": bool, "deactivate": bool, "activate": bool },
    "permissions": { "view": bool, "set_job_title_defaults": bool, "set_user_overrides": bool },
    "audit_logs":  { "view": bool, "export": bool, "delete": bool },
    "modules":     { "view": bool, "install": bool, "upgrade": bool }
  }
}
```

---

## API Reference

### Current User

#### `POST /api/crm/me/permissions`

Returns the authenticated user's resolved permission map.  
Call on login, cache globally, refetch after any admin-role/permission change.

**Request**
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

**Response**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "data": {
      "id": 5,
      "name": "Ahmad Karimi",
      "email": "ahmad@company.com",
      "login": "ahmad@company.com",
      "job_title": "Sales Supervisor",
      "active": true,
      "role": "supervisor",
      "role_label": "Supervisor",
      "has_individual_overrides": false,
      "override_notes": "",
      "avatar_url": "/web/image/res.users/5/avatar_128",
      "permissions": {
        "supply_chain": {
          "containers": { "list": true, "view": true, "create": true, "edit": true, "delete": false, "..." : "..." }
        }
      }
    }
  }
}
```

---

### Admin — Permission Schema

#### `POST /api/crm/admin/permissions/schema`

Returns the complete permission tree (all false as base) plus role baselines.  
Use this to **render the admin permission-editor form dynamically** — you don't need to hardcode the tree in the FE.

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "tree": { "...full PERMISSION_TREE with all false..." },
      "roles": ["none", "agent", "supervisor", "manager", "general_manager", "qa_auditor", "qa_supervisor"],
      "role_baselines": {
        "agent":    { "supply_chain": { "containers": { "list": true, "view": true, "create": false, "..." : "..." } } },
        "manager":  { "..." : "..." }
      }
    }
  }
}
```

---

### Admin — Job-Title Templates

#### `POST /api/crm/admin/permissions/job_titles/list`

**Request**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "search": "Sales",
    "active": true
  }
}
```

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "items": [
        {
          "job_title":   "Sales Agent",
          "label":       "Sales Agent",
          "crm_role":    "agent",
          "notes":       "",
          "is_active":   true,
          "user_count":  3,
          "permissions": { "supply_chain": { "containers": { "list": true, "create": false, "..." : "..." } } }
        }
      ],
      "total": 1
    }
  }
}
```

---

#### `POST /api/crm/admin/permissions/job_titles/upsert`

Create or update the default permissions for a job title.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `job_title` | string | ✅ | Exact job title text, e.g. `"Sales Agent"` |
| `permissions` | object | ✅ | Full or partial permission tree |
| `crm_role` | string | — | `agent` / `supervisor` / `manager` / `general_manager` / `qa_auditor` / `qa_supervisor` / `none` |
| `apply_to_all_users` | bool | — | If `true`, removes ALL individual overrides for users with this job title (clean slate). Default `false` |
| `label` | string | — | Human-friendly label |
| `notes` | string | — | Admin memo |

**Request — Create "Sales Supervisor" template**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "job_title":    "Sales Supervisor",
    "crm_role":     "supervisor",
    "label":        "Sales Supervisor",
    "notes":        "Can approve POs and manage containers but cannot delete",
    "apply_to_all_users": false,
    "permissions": {
      "supply_chain": {
        "containers": {
          "list": true, "view": true, "create": true, "edit": true, "delete": false,
          "assign_driver": true, "mark_arrived": true, "clearance_delivered": true,
          "set_reminder": true, "upload_attachment": true, "delete_attachment": true,
          "add_comment": true, "delete_comment": true, "add_penalty": false, "delete_penalty": false
        },
        "po": {
          "list": true, "view": true, "create": true, "edit": true, "submit": true,
          "confirm": true, "ship": false, "receive": false, "cancel": false, "reopen": false,
          "add_line": true, "edit_line": true, "delete_line": true,
          "upload_attachment": true, "delete_attachment": true,
          "add_comment": true, "delete_comment": true, "export_pdf": true, "delete": false
        },
        "vendors":       { "list": true, "view": true, "create": false, "edit": false, "delete": false },
        "negotiations":  { "list": true, "view": true, "create": true, "edit": true, "delete": false, "add_comment": true, "delete_comment": true },
        "item_requests": { "list": true, "view": true, "create": true, "edit": true, "delete": false, "approve": true, "reject": true, "fulfill": false },
        "clearance_companies": { "list": true, "view": true, "create": false, "edit": false, "delete": false },
        "tracking":   { "view": true, "update": true },
        "minmax":     { "list": true, "edit": false, "delete": false },
        "notifications": { "list": true, "mark_read": true, "delete": true },
        "chat":       { "view": true, "send": true, "delete_message": true },
        "stories":    { "list": true, "view": true, "create": true, "delete": true }
      },
      "crm": {
        "customers": { "list": true, "view": true, "create": true, "edit": true, "delete": false, "export": false },
        "calls":     { "list": true, "view": true, "create": true, "edit": true, "delete": false },
        "tickets":   { "list": true, "view": true, "create": true, "edit": true, "delete": false, "assign": true },
        "tasks":     { "list": true, "view": true, "create": true, "edit": true, "delete": false, "assign": true },
        "analytics": { "view": true, "export": false },
        "config":    { "view": false, "edit": false },
        "branches":  { "list": true, "view": true, "create": false, "edit": true, "delete": false },
        "knowledge": { "list": true, "view": true, "create": true, "edit": true, "delete": false }
      },
      "admin": {
        "users":       { "list": false, "view": false, "assign_role": false, "deactivate": false, "activate": false },
        "permissions": { "view": false, "set_job_title_defaults": false, "set_user_overrides": false }
      }
    }
  }
}
```

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "job_title": "Sales Supervisor",
      "label":     "Sales Supervisor",
      "crm_role":  "supervisor",
      "user_count": 2,
      "applied_to_all_users": false,
      "permissions": { "..." : "..." }
    }
  }
}
```

---

#### `POST /api/crm/admin/permissions/job_titles/delete`

```json
{ "jsonrpc": "2.0", "method": "call", "params": { "job_title": "Sales Agent" } }
```

---

### Admin — User Management

#### `POST /api/crm/admin/users/list`

| Param | Type | Description |
|-------|------|-------------|
| `search` | string | Filter by name / email |
| `role` | string | Filter by CRM role |
| `job_title` | string | Filter by job title (partial match) |
| `active` | bool | Default `true` |
| `with_perms` | bool | Include full permission map in each item (slower). Default `false` |
| `page`, `per_page` | int | Pagination |

**Request**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "search": "ahmad",
    "role":   "supervisor",
    "with_perms": false,
    "page": 1, "per_page": 20
  }
}
```

---

#### `POST /api/crm/admin/users/<id>/get`

Returns a single user with full effective permissions.

```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

---

#### `POST /api/crm/admin/users/<id>/permissions/get`

Returns the **full permission audit trail** — shows all three layers separately:

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "user_id":   5,
      "name":      "Ahmad Karimi",
      "email":     "ahmad@company.com",
      "job_title": "Sales Supervisor",
      "role":      "supervisor",

      "role_baseline": {
        "supply_chain": { "containers": { "list": true, "create": true, "delete": false, "..." : "..." } }
      },

      "job_title_template": {
        "found":       true,
        "crm_role":    "supervisor",
        "permissions": { "supply_chain": { "containers": { "create": true, "..." : "..." } } }
      },

      "individual_overrides": {
        "found":              true,
        "job_title_override": null,
        "overrides": {
          "supply_chain": { "containers": { "delete": true } }
        },
        "admin_notes":     "Ahmad needs delete for Q2 cleanup",
        "last_modified_by": "Admin User",
        "last_modified_at": "2026-05-02T06:30:00"
      },

      "effective_permissions": {
        "supply_chain": { "containers": { "list": true, "create": true, "delete": true, "..." : "..." } }
      }
    }
  }
}
```

---

#### `POST /api/crm/admin/users/<id>/permissions/set`

**The main endpoint for granting/restricting an individual employee.**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `permissions` | object | ✅ | **Partial or full** permission delta. Only the keys you send are changed. |
| `apply_to_all_same_job_title` | bool | — | If `true`, saves these permissions as the **job-title template** for this user's job title — affects ALL future users with that title. Does NOT clear other users' individual overrides. |
| `job_title_override` | string | — | Treat this user as if they had a different job title for permission lookup. |
| `notes` | string | — | Audit trail memo (e.g. `"Temp access for Q2 inventory count"`) |

##### Scenario A — Grant one extra action to a specific employee

> Ahmad is a Sales Supervisor. His job title template says `containers.delete = false`.
> You want only Ahmad to be able to delete containers temporarily.

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "permissions": {
      "supply_chain": {
        "containers": { "delete": true }
      }
    },
    "apply_to_all_same_job_title": false,
    "notes": "Temp delete access for Q2 cleanup — expires Jun 30"
  }
}
```

##### Scenario B — Restrict an action for one employee

> Sara is a Manager but should NOT be able to export customer data.

```json
{
  "params": {
    "permissions": {
      "crm": {
        "customers": { "export": false }
      }
    },
    "notes": "Export disabled per compliance request #2045"
  }
}
```

##### Scenario C — Give employee a different role's permissions

> Khalid is officially an Agent but needs Supervisor-level supply chain rights.

```json
{
  "params": {
    "job_title_override": "Sales Supervisor",
    "permissions": {},
    "notes": "Acting supervisor while Ali is on leave"
  }
}
```

##### Scenario D — Update permissions and propagate to ALL users with same job title

> You want to update the default for "Warehouse Agent" so that ALL employees with that title get container create rights.

```json
{
  "params": {
    "permissions": {
      "supply_chain": {
        "containers": { "create": true, "edit": true },
        "tracking":   { "update": true }
      }
    },
    "apply_to_all_same_job_title": true,
    "notes": "Warehouse Agents now create containers as of May 2026"
  }
}
```

This will:
1. Upsert the "Warehouse Agent" job-title template with the new permissions.
2. Clear THIS user's individual overrides (they now inherit the template cleanly).
3. Other Warehouse Agents keep their individual overrides layered on top of the new template.

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "id": 5,
      "name": "Ahmad Karimi",
      "role": "supervisor",
      "has_individual_overrides": true,
      "applied_to_all_same_job_title": false,
      "permissions": { "..." : "...merged result..." }
    }
  }
}
```

---

#### `POST /api/crm/admin/users/<id>/permissions/reset`

Remove ALL individual overrides for this user. They revert to their job-title template defaults.

```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

---

#### `POST /api/crm/admin/users/assign_role`

Assigns a system-level CRM Odoo group (role) to a user identified by email.  
This controls Odoo model-level access rules. Combine with `permissions/set` for fine-grained action control.

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "email": "ahmad@company.com",
    "role":  "supervisor"
  }
}
```

Valid roles: `none` | `agent` | `supervisor` | `manager` | `general_manager` | `qa_auditor` | `qa_supervisor`

---

#### `POST /api/crm/admin/users/bulk_assign`

Assign roles to multiple users at once.

```json
{
  "params": {
    "assignments": [
      { "email": "ahmad@company.com",  "role": "supervisor" },
      { "email": "sara@company.com",   "role": "agent" },
      { "email": "khalid@company.com", "role": "manager" }
    ]
  }
}
```

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "updated_count": 3,
      "results": [
        { "email": "ahmad@company.com",  "role": "supervisor", "success": true  },
        { "email": "sara@company.com",   "role": "agent",      "success": true  },
        { "email": "khalid@company.com", "role": "manager",    "success": true  }
      ]
    }
  }
}
```

---

#### `POST /api/crm/admin/users/<id>/deactivate`

#### `POST /api/crm/admin/users/<id>/activate`

---

## Role vs Permission — When to Use Which

| Use case | Endpoint |
|----------|----------|
| Set model-level access (record rules, menu visibility in Odoo backend) | `assign_role` |
| Set what actions the FE shows/hides for ALL users with a job title | `job_titles/upsert` |
| Grant or restrict a **specific employee** beyond their title | `permissions/set` |
| View the full breakdown (why does Ahmad see this button?) | `permissions/get` |
| Remove individual exceptions, return to defaults | `permissions/reset` |

---

## Default Permissions by Role

| Action | `none` | `agent` | `supervisor` | `manager` | `general_manager` |
|--------|:------:|:-------:|:------------:|:---------:|:-----------------:|
| **Containers** |
| list / view | ❌ | ✅ | ✅ | ✅ | ✅ |
| create / edit | ❌ | ❌ | ✅ | ✅ | ✅ |
| delete | ❌ | ❌ | ❌ | ❌ | ✅ |
| assign driver / mark arrived | ❌ | ❌ | ✅ | ✅ | ✅ |
| add penalty | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Purchase Orders** |
| list / view / create | ❌ | ✅ | ✅ | ✅ | ✅ |
| submit for approval | ❌ | ✅ | ✅ | ✅ | ✅ |
| supervisor confirm (1st approval) | ❌ | ❌ | ✅ | ✅ | ✅ |
| ship / receive / cancel | ❌ | ❌ | ❌ | ✅ | ✅ |
| delete | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Vendors** |
| list / view | ❌ | ✅ | ✅ | ✅ | ✅ |
| create / edit | ❌ | ❌ | ❌ | ✅ | ✅ |
| delete | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Item Requests** |
| list / view / create | ❌ | ✅ | ✅ | ✅ | ✅ |
| approve / reject | ❌ | ❌ | ✅ | ✅ | ✅ |
| fulfill | ❌ | ❌ | ❌ | ✅ | ✅ |
| delete | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Clearance Companies** |
| list / view | ❌ | ✅ | ✅ | ✅ | ✅ |
| create / edit | ❌ | ❌ | ❌ | ✅ | ✅ |
| delete | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Min/Max Rules** |
| list | ❌ | ✅ | ✅ | ✅ | ✅ |
| edit / delete | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Admin** |
| manage users / permissions | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Error Responses

All errors follow this format:

```json
{
  "result": {
    "success": false,
    "error":   "Human-readable message",
    "code":    403
  }
}
```

| Code | Meaning |
|------|---------|
| *(missing)* | Bad input or not found |
| `403` | Authenticated but not authorized (wrong role) |

Unauthorized (no / invalid JWT) returns:
```json
{ "result": { "success": false, "error": "Unauthorized" } }
```

---

---

## New Admin Endpoints — Full Control Reference

### `POST /api/crm/admin/users/create`
إنشاء مستخدم جديد وتعيين دوره مباشرة.

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "name":      "Ahmed Al-Farsi",
    "email":     "ahmed@company.com",
    "job_title": "مشرف المبيعات",
    "role":      "supervisor",
    "password":  "Initial@123",
    "lang":      "ar_001"
  }
}
```

**Response**
```json
{
  "result": {
    "success": true,
    "data": { "id": 42, "name": "Ahmed Al-Farsi", "email": "ahmed@company.com", "role": "supervisor" }
  }
}
```

---

### `POST /api/crm/admin/users/<id>/update`
تعديل بيانات مستخدم موجود (أي حقل منهم اختياري).

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "name":      "Ahmed Al-Farsi",
    "job_title": "مدير المبيعات",
    "phone":     "+966501234567",
    "lang":      "ar_001"
  }
}
```

---

### `POST /api/crm/admin/users/<id>/change_password`
تغيير كلمة مرور مستخدم بصلاحية الأدمن.

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "new_password": "NewPass@456" }
}
```

---

### `POST /api/crm/admin/users/<id>/delete`
حذف مستخدم نهائياً (لا رجعة — استخدم `/deactivate` للإيقاف المؤقت).

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "confirm": true }
}
```

---

### `POST /api/crm/admin/users/<id>/remove_role`
إزالة جميع أدوار CRM من مستخدم (يصبح `role: "none"`).
لا يحذف الاستثناءات الفردية.

```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

---

### `POST /api/crm/admin/permissions/job_titles/get`
عرض تفاصيل template مسمى وظيفي واحد مع الصلاحيات الفعلية المدمجة.

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "job_title": "مشرف المبيعات" }
}
```

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "id": 3,
      "job_title": "مشرف المبيعات",
      "crm_role": "supervisor",
      "is_active": true,
      "user_count": 7,
      "permissions": { "...delta overrides only..." },
      "effective_permissions": { "...full resolved tree..." }
    }
  }
}
```

---

### `POST /api/crm/admin/users/bulk_permissions`
تطبيق صلاحيات دفعة واحدة على مجموعة مستخدمين.

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "user_ids": [5, 8, 12, 17],
    "permissions": {
      "inventory": { "stock": { "view": true, "adjust": true } },
      "finance":   { "invoices": { "list": true, "view": true } }
    },
    "mode":  "merge",
    "notes": "تحديث مايو 2026 — صلاحيات جديدة لفريق المبيعات"
  }
}
```

| `mode` | الوصف |
|--------|-------|
| `merge` | دمج فوق الاستثناءات الموجودة (افتراضي) |
| `replace` | استبدال جميع الاستثناءات بالجديدة |
| `reset` | حذف جميع الاستثناءات (تجاهل `permissions`) |

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 4,
      "processed": 4,
      "results": [
        { "user_id": 5,  "status": "merged" },
        { "user_id": 8,  "status": "merged" },
        { "user_id": 12, "status": "merged" },
        { "user_id": 17, "status": "merged" }
      ]
    }
  }
}
```

---

### `POST /api/crm/admin/audit/permissions`
سجل التعديلات على الصلاحيات — من غيّر ماذا ومتى.

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "user_id": 5,
    "limit":   20,
    "offset":  0
  }
}
```

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 3,
      "log": [
        {
          "id": 12,
          "user": { "id": 5, "name": "Ahmed", "email": "ahmed@company.com", "job_title": "مشرف المبيعات" },
          "permissions_delta": { "inventory": { "stock": { "adjust": true } } },
          "notes": "تحديث مايو 2026",
          "modified_by": { "id": 1, "name": "Admin", "email": "admin@company.com" },
          "modified_at": "2026-05-02T11:00:00"
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/admin/stats`
إحصائيات سريعة لداشبورد الأدمن.

```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "users": {
        "total_active": 45,
        "total_inactive": 3,
        "with_individual_overrides": 12,
        "without_crm_role": 2,
        "no_role_list": [{ "id": 9, "name": "New User", "email": "new@company.com" }]
      },
      "roles": {
        "agent": 20, "supervisor": 10, "manager": 8,
        "general_manager": 2, "qa_auditor": 4, "qa_supervisor": 1
      },
      "templates": { "active": 8, "total": 9 }
    }
  }
}
```

---

### `POST /api/crm/admin/export/permissions`
تصدير صلاحيات جميع المستخدمين كـ JSON (للنسخ الاحتياطي أو الـ FE cache).

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "format": "full",
    "role":   "supervisor"
  }
}
```

| `format` | الوصف |
|----------|-------|
| `full` | الصلاحيات الكاملة المحسوبة لكل مستخدم |
| `delta_only` | الاستثناءات الفردية فقط (payload أخف) |

---

### `POST /api/crm/admin/import/permissions`
استيراد صلاحيات من snapshot سابق (مثلاً بعد migrate).

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "dry_run": false,
    "users": [
      {
        "email": "ahmed@company.com",
        "individual_overrides": { "finance": { "invoices": { "view": true } } },
        "job_title_override": ""
      }
    ]
  }
}
```

---

### `POST /api/crm/admin/users/compare_permissions`
مقارنة صلاحيات مستخدمين جنباً إلى جنب.

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "user_id_a": 5, "user_id_b": 8 }
}
```

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "user_a": { "id": 5, "name": "Ahmed", "role": "supervisor" },
      "user_b": { "id": 8, "name": "Sara",  "role": "manager" },
      "total_differences": 14,
      "diff": {
        "supply_chain": {
          "containers": {
            "delete":      { "user_a": false, "user_b": false },
            "add_penalty": { "user_a": false, "user_b": true }
          }
        },
        "finance": {
          "invoices": {
            "list": { "user_a": false, "user_b": true }
          }
        }
      }
    }
  }
}
```

---

## Complete Admin Endpoints Reference

| # | Endpoint | الوصف |
|---|----------|-------|
| 1 | `POST /api/crm/me/permissions` | صلاحيات المستخدم الحالي |
| 2 | `POST /api/crm/admin/permissions/schema` | شجرة الصلاحيات + baselines لكل role |
| 3 | `POST /api/crm/admin/permissions/job_titles/list` | قائمة templates المسميات الوظيفية |
| 4 | `POST /api/crm/admin/permissions/job_titles/get` | تفاصيل template واحد |
| 5 | `POST /api/crm/admin/permissions/job_titles/upsert` | إنشاء/تعديل template |
| 6 | `POST /api/crm/admin/permissions/job_titles/delete` | حذف template |
| 7 | `POST /api/crm/admin/users/list` | قائمة المستخدمين مع الأدوار |
| 8 | `POST /api/crm/admin/users/create` | **جديد** — إنشاء مستخدم |
| 9 | `POST /api/crm/admin/users/<id>/get` | تفاصيل مستخدم |
| 10 | `POST /api/crm/admin/users/<id>/update` | **جديد** — تعديل بيانات مستخدم |
| 11 | `POST /api/crm/admin/users/<id>/change_password` | **جديد** — تغيير كلمة المرور |
| 12 | `POST /api/crm/admin/users/<id>/delete` | **جديد** — حذف مستخدم نهائياً |
| 13 | `POST /api/crm/admin/users/<id>/deactivate` | إيقاف مستخدم مؤقتاً |
| 14 | `POST /api/crm/admin/users/<id>/activate` | تفعيل مستخدم |
| 15 | `POST /api/crm/admin/users/<id>/remove_role` | **جديد** — إزالة دور CRM |
| 16 | `POST /api/crm/admin/users/<id>/permissions/get` | صلاحيات مستخدم (3 طبقات منفصلة) |
| 17 | `POST /api/crm/admin/users/<id>/permissions/set` | تعيين/تعديل صلاحيات مستخدم |
| 18 | `POST /api/crm/admin/users/<id>/permissions/reset` | حذف الاستثناءات الفردية |
| 19 | `POST /api/crm/admin/users/assign_role` | تعيين دور بالـ email |
| 20 | `POST /api/crm/admin/users/bulk_assign` | تعيين أدوار لمجموعة |
| 21 | `POST /api/crm/admin/users/bulk_permissions` | **جديد** — صلاحيات لمجموعة دفعة واحدة |
| 22 | `POST /api/crm/admin/users/compare_permissions` | **جديد** — مقارنة مستخدمين |
| 23 | `POST /api/crm/admin/audit/permissions` | **جديد** — سجل التعديلات |
| 24 | `POST /api/crm/admin/stats` | **جديد** — إحصائيات الداشبورد |
| 25 | `POST /api/crm/admin/export/permissions` | **جديد** — تصدير الصلاحيات |
| 26 | `POST /api/crm/admin/import/permissions` | **جديد** — استيراد الصلاحيات |

---

## Implementation Notes

1. **Always call `/api/crm/me/permissions` on app load** and store the result. Do not call it on every page navigation.
2. **Refetch permissions after** `assign_role`, `permissions/set`, or `permissions/reset` so the cache stays fresh.
3. `has_individual_overrides: true` in the user object means the user has exceptions beyond their job title — useful to show a visual indicator in the admin UI.
4. The `permissions` object in every response is **fully resolved** — you never need to merge layers yourself.
5. The `admin.permissions.view` flag controls whether to show the admin permissions management UI in the FE.
6. When `apply_to_all_same_job_title` is passed as `true`, the backend writes a job-title template. Other users are NOT reset — they keep their own individual overrides, but from now on those overrides sit on top of the updated template.
7. Use `bulk_permissions` with `mode: "reset"` to clear all overrides for a group of users at once.
8. `compare_permissions` is ideal for FE "Access Inspector" tooling where admins compare two employees side-by-side.
