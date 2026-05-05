# Lugal ERP — Frontend Integration Guide
## Permission System & Admin API — Complete Reference

> **Version:** 2.0 — May 2026  
> **Base URL:** `http://<server>:8069`  
> **Protocol:** JSON-RPC 2.0  
> **Auth Header:** `Authorization: Bearer <jwt_token>` — required on **every** request  
> **Content-Type:** `application/json`

---

## Table of Contents

1. [How the Permission System Works](#1-how-the-permission-system-works)
2. [Role Hierarchy](#2-role-hierarchy)
3. [Quick Start — On Login](#3-quick-start--on-login)
4. [How to Guard UI Elements](#4-how-to-guard-ui-elements)
5. [Full Permission Tree](#5-full-permission-tree)
6. [Current User Endpoints](#6-current-user-endpoints)
7. [Admin — User Management](#7-admin--user-management)
8. [Admin — Permission Management](#8-admin--permission-management)
9. [Admin — Job-Title Templates](#9-admin--job-title-templates)
10. [Admin — Bulk & Batch Operations](#10-admin--bulk--batch-operations)
11. [Admin — Audit & Analytics](#11-admin--audit--analytics)
12. [Admin — Export & Import](#12-admin--export--import)
13. [All Endpoints — Quick Reference](#13-all-endpoints--quick-reference)
14. [Error Handling](#14-error-handling)
15. [Frontend Integration Checklist](#15-frontend-integration-checklist)

---

## 1. How the Permission System Works

The system uses **3 layers** to compute every user's final permissions.  
Higher layers always win over lower ones.

```
┌───────────────────────────────────────────────────────────────────────┐
│                     PERMISSION RESOLUTION ENGINE                       │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 3 — Individual Override          ← HIGHEST PRIORITY      │ │
│  │  Set by: Admin via /permissions/set                              │ │
│  │  Scope:  Only this specific employee                             │ │
│  └──────────────────────────┬──────────────────────────────────────┘ │
│                              │  overrides                             │
│  ┌───────────────────────────▼──────────────────────────────────────┐ │
│  │  LAYER 2 — Job-Title Template                                    │ │
│  │  Set by: Admin via /job_titles/upsert                            │ │
│  │  Scope:  All users with the same job title (res.partner.function)│ │
│  └──────────────────────────┬──────────────────────────────────────┘ │
│                              │  overrides                             │
│  ┌───────────────────────────▼──────────────────────────────────────┐ │
│  │  LAYER 1 — CRM Role Baseline            ← LOWEST PRIORITY       │ │
│  │  Set by: Admin via /assign_role                                  │ │
│  │  Scope:  All users with the same Odoo role group                 │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│   final = deep_merge( layer1, layer2, layer3 )                        │
└───────────────────────────────────────────────────────────────────────┘
```

| Layer | What it is | How admin sets it |
|-------|-----------|------------------|
| 1 — Role Baseline | Default permissions for an Odoo CRM role (agent/supervisor/...) | `POST /api/crm/admin/users/assign_role` |
| 2 — Job-Title Template | Custom defaults for a job title e.g. "مشرف المبيعات" | `POST /api/crm/admin/permissions/job_titles/upsert` |
| 3 — Individual Override | Exceptions for one specific user | `POST /api/crm/admin/users/<id>/permissions/set` |

> **FE rule:** You never merge layers yourself. The backend always returns the final resolved `permissions` object ready to use.

---

## 2. Role Hierarchy

```
                    ┌──────────────────────────────┐
                    │       GENERAL MANAGER         │
                    │  Full access to everything    │
                    └──────────┬──────────┬─────────┘
                               │          │
               ┌───────────────┘          └───────────────┐
               ▼                                           ▼
      ┌─────────────────┐                     ┌────────────────────┐
      │    MANAGER       │                     │   QA SUPERVISOR    │
      │  مدير CRM        │                     │  مشرف مدققي الجودة │
      └────────┬─────────┘                     └─────────┬──────────┘
               │                                         │
               ▼                                         ▼
      ┌─────────────────┐                     ┌────────────────────┐
      │   SUPERVISOR     │                     │   QA AUDITOR       │
      │  مشرف CRM        │                     │  مدقق الجودة       │
      └────────┬─────────┘                     └────────────────────┘
               │
               ▼
      ┌─────────────────┐
      │     AGENT        │
      │   موظف CRM       │
      └─────────────────┘
```

| Role Key | Arabic | Implied Roles |
|----------|--------|---------------|
| `agent` | موظف | — |
| `supervisor` | مشرف | agent |
| `manager` | مدير | supervisor → agent |
| `general_manager` | مدير عام | manager → supervisor → agent + qa_supervisor |
| `qa_auditor` | مدقق الجودة | — |
| `qa_supervisor` | مشرف مدققي الجودة | qa_auditor |
| `none` | بدون دور | no CRM permissions |

---

## 3. Quick Start — On Login

### Step 1: Fetch permissions right after login

```typescript
// Call once after JWT is obtained
const response = await api.post('/api/crm/me/permissions', {
  jsonrpc: '2.0',
  method: 'call',
  params: {}
});

const { data } = response.result;

// Store in Redux / Zustand / Context
store.dispatch(setCurrentUser({
  id:          data.id,
  name:        data.name,
  email:       data.email,
  jobTitle:    data.job_title,
  role:        data.role,           // "agent" | "supervisor" | "manager" | "general_manager" | "qa_auditor" | "qa_supervisor" | "none"
  hasOverrides:data.has_individual_overrides,
  permissions: data.permissions,    // ← the full resolved tree, ready to use
}));
```

### Step 2: Create a `can()` helper

```typescript
// permissions.ts
import { store } from '@/app/store';

/**
 * Check a dot-notation permission path.
 * e.g.  can('supply_chain.containers.create')
 *        can('admin.users.assign_role')
 *        can('finance.invoices.view')
 */
export function can(path: string): boolean {
  const permissions = store.getState().auth.permissions;
  if (!permissions) return false;
  return path.split('.').reduce((obj: any, key) => obj?.[key], permissions) === true;
}

/**
 * Check multiple permissions — returns true only if ALL pass.
 */
export function canAll(...paths: string[]): boolean {
  return paths.every(can);
}

/**
 * Check multiple permissions — returns true if ANY pass.
 */
export function canAny(...paths: string[]): boolean {
  return paths.some(can);
}
```

### Step 3: Use in components

```tsx
// React example
import { can } from '@/shared/utils/permissions';

function ContainerActions({ container }) {
  return (
    <div>
      {can('supply_chain.containers.view')   && <ViewButton />}
      {can('supply_chain.containers.edit')   && <EditButton />}
      {can('supply_chain.containers.create') && <NewContainerButton />}
      {can('supply_chain.containers.delete') && <DeleteButton />}
      {can('admin.users.assign_role')        && <AdminPanel />}
    </div>
  );
}
```

---

## 4. How to Guard UI Elements

### Navigation / Sidebar

```typescript
const navItems = [
  { label: 'Supply Chain',  path: '/supply',   show: can('supply_chain.containers.list') },
  { label: 'CRM',           path: '/crm',      show: can('crm.customers.list') },
  { label: 'Point of Sale', path: '/pos',      show: can('pos.orders.list') },
  { label: 'HR',            path: '/hr',       show: canAny('hr.employees.list', 'hr.attendance.view_own') },
  { label: 'Inventory',     path: '/inventory',show: can('inventory.products.list') },
  { label: 'Finance',       path: '/finance',  show: canAny('finance.invoices.list', 'finance.bills.list') },
  { label: 'Analytics',     path: '/analytics',show: can('analytics.dashboards.view') },
  { label: 'QA',            path: '/qa',       show: can('qa.reviews.list') },
  { label: 'Admin',         path: '/admin',    show: can('admin.users.list') },
  { label: 'Settings',      path: '/settings', show: can('settings.general.view') },
];
```

### Route Guards

```typescript
// React Router v6
function ProtectedRoute({ permissionPath, children }) {
  if (!can(permissionPath)) {
    return <Navigate to="/unauthorized" replace />;
  }
  return children;
}

// Usage
<ProtectedRoute permissionPath="admin.users.list">
  <AdminUsersPage />
</ProtectedRoute>
```

### Button-level Guards

```tsx
// Disable vs hide — choose based on UX
<button
  disabled={!can('supply_chain.po.confirm')}
  onClick={confirmPO}
>
  Confirm PO
</button>

// Or hide completely
{can('supply_chain.containers.delete') && (
  <DeleteContainerButton />
)}
```

---

## 5. Full Permission Tree

All values are `boolean`. The backend returns the complete tree on every permissions call.  
Covers **10 modules** — 80+ sections — 200+ actions.

```jsonc
{
  // ── SUPPLY CHAIN ──────────────────────────────────────────────────────────
  "supply_chain": {
    "containers": {
      "list": bool,               // Show containers list/tab
      "view": bool,               // Open container detail
      "create": bool,             // "New Container" button — ADMIN+ only
      "edit": bool,               // Save changes to container
      "delete": bool,             // Delete container — GM only
      "assign_driver": bool,      // Driver assignment action
      "mark_arrived": bool,       // "Mark Arrived at Port"
      "clearance_delivered": bool,// "Clearance Documents Delivered"
      "set_reminder": bool,       // Set/clear reminder date
      "upload_attachment": bool,  // Attach files
      "delete_attachment": bool,  // Remove attachments
      "add_comment": bool,        // Post comment/note
      "delete_comment": bool,     // Delete comment
      "add_penalty": bool,        // Add penalty — Manager+
      "delete_penalty": bool      // Delete penalty — Manager+
    },
    "vendors": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool
    },
    "po": {
      "list": bool, "view": bool,
      "create": bool,             // Create draft PO
      "edit": bool,               // Edit PO header
      "delete": bool,             // Hard delete — GM only
      "submit": bool,             // Submit for approval
      "confirm": bool,            // Supervisor 1st approval
      "ship": bool,               // Mark as shipped — Manager
      "receive": bool,            // Mark as received — Manager
      "cancel": bool,             // Cancel PO
      "reopen": bool,             // Reopen cancelled PO
      "add_line": bool,           // Add PO line items
      "edit_line": bool,          // Edit existing line
      "delete_line": bool,        // Remove a line
      "upload_attachment": bool,
      "delete_attachment": bool,
      "add_comment": bool,
      "delete_comment": bool,
      "export_pdf": bool          // Download PO as PDF
    },
    "negotiations": {
      "list": bool, "view": bool,
      "create": bool, "edit": bool, "delete": bool,
      "add_comment": bool, "delete_comment": bool
    },
    "item_requests": {
      "list": bool, "view": bool,
      "create": bool,             // Submit new request
      "edit": bool,               // Edit pending request
      "delete": bool,
      "approve": bool,            // Supervisor approves
      "reject": bool,             // Supervisor rejects
      "fulfill": bool             // Manager marks fulfilled
    },
    "clearance_companies": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool
    },
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
      "export": bool,             // CSV/Excel export
      "import": bool,             // Bulk import
      "merge": bool               // Merge duplicate records — GM only
    },
    "calls": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool,
      "listen_recording": bool    // Play call recording — Manager+/QA
    },
    "tickets": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool,
      "assign": bool,             // Assign to agent
      "escalate": bool,           // Escalate to manager
      "close": bool               // Close ticket
    },
    "tasks": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool,
      "assign": bool, "close": bool
    },
    "analytics": {
      "view": bool,
      "export": bool,
      "view_team_data": bool      // See all agents' data, not just own
    },
    "config":      { "view": bool, "edit": bool },
    "branches":    { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool },
    "knowledge":   { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool },
    "omnichannel": { "view": bool, "reply": bool, "assign": bool },
    "shifts":      { "view": bool, "manage": bool }
  },

  // ── QA ────────────────────────────────────────────────────────────────────
  "qa": {
    "reviews": {
      "list": bool, "view": bool, "create": bool,
      "score": bool,              // Submit quality score
      "delete": bool, "export": bool
    },
    "management": { "view": bool, "manage": bool, "assign_reviewer": bool },
    "reports":    { "view": bool, "export": bool }
  },

  // ── POINT OF SALE ─────────────────────────────────────────────────────────
  "pos": {
    "sessions":  { "list": bool, "view": bool, "open": bool, "close": bool },
    "orders": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool,
      "refund": bool, "export_pdf": bool
    },
    "products": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool,
      "set_price": bool,          // Override product price
      "set_discount": bool        // Apply discount
    },
    "customers": { "list": bool, "view": bool, "create": bool, "edit": bool },
    "payments":  { "view": bool, "process": bool, "refund": bool },
    "reports":   { "view": bool, "export": bool, "z_report": bool },
    "config":    { "view": bool, "edit": bool }
  },

  // ── HUMAN RESOURCES ───────────────────────────────────────────────────────
  "hr": {
    "employees": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool,
      "view_salary": bool,        // See salary fields — GM only
      "view_private": bool,       // See private/sensitive fields — GM only
      "export": bool
    },
    "attendance": {
      "view_own": bool,           // See own attendance — all users
      "view_all": bool,           // See all team — Supervisor+
      "edit": bool, "export": bool
    },
    "leaves": {
      "view_own": bool, "view_all": bool,
      "request": bool,            // Submit leave request
      "approve": bool, "refuse": bool,
      "manage_allocation": bool   // Manage leave allocations
    },
    "payroll": {
      "view_own": bool,           // See own payslip
      "view_all": bool,           // See all payslips — Manager+
      "compute": bool, "validate": bool, "export": bool
    },
    "recruitment": { "view": bool, "create": bool, "manage": bool, "delete": bool },
    "kpi":  { "view_own": bool, "view_all": bool, "set": bool, "export": bool },
    "shifts":{ "view_own": bool, "view_all": bool, "manage": bool },
    "org_chart": { "view": bool },
    "config": { "view": bool, "edit": bool }
  },

  // ── INVENTORY / STOCK ─────────────────────────────────────────────────────
  "inventory": {
    "products": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool,
      "set_price": bool, "import": bool, "export": bool
    },
    "stock": {
      "view": bool,
      "adjust": bool,             // Manual stock adjustment
      "transfer": bool,           // Create internal transfer
      "scrap": bool,              // Scrap products — GM only
      "view_valuation": bool      // See stock valuation amounts — GM only
    },
    "transfers": {
      "list": bool, "view": bool, "create": bool,
      "validate": bool, "cancel": bool, "delete": bool
    },
    "warehouses":   { "view": bool, "create": bool, "edit": bool, "delete": bool },
    "locations":    { "view": bool, "create": bool, "edit": bool, "delete": bool },
    "lots_serials": { "view": bool, "create": bool, "edit": bool },
    "reports":      { "view": bool, "export": bool },
    "config":       { "view": bool, "edit": bool }
  },

  // ── FINANCE / ACCOUNTING ──────────────────────────────────────────────────
  "finance": {
    "invoices": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool,
      "confirm": bool,            // Post/confirm invoice
      "cancel": bool,             // Cancel posted invoice
      "register_payment": bool,   // Register payment against invoice
      "export_pdf": bool
    },
    "bills": {
      "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool,
      "confirm": bool, "cancel": bool, "register_payment": bool
    },
    "payments":       { "list": bool, "view": bool, "create": bool, "validate": bool, "cancel": bool },
    "journals":       { "view": bool, "create": bool, "edit": bool, "delete": bool },
    "accounts":       { "view": bool, "create": bool, "edit": bool },
    "reports": {
      "profit_loss": bool,        // P&L report
      "balance_sheet": bool,
      "cash_flow": bool,
      "tax_report": bool,
      "export": bool
    },
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

## 6. Current User Endpoints

### `POST /api/crm/me/permissions`

Returns the fully resolved permission map of the logged-in user.  
Call **once on login** and cache. Refetch whenever admin changes the user's role/permissions.

**Request**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {}
}
```

**Response**
```json
{
  "jsonrpc": "2.0",
  "id": null,
  "result": {
    "success": true,
    "data": {
      "id": 5,
      "name": "Ahmed Al-Farsi",
      "email": "ahmed@company.com",
      "login": "ahmed@company.com",
      "job_title": "مشرف المبيعات",
      "active": true,
      "role": "supervisor",
      "role_label": "CRM Supervisor / مشرف CRM",
      "has_individual_overrides": false,
      "override_notes": "",
      "avatar_url": "/web/image/res.users/5/avatar_128",
      "permissions": {
        "supply_chain": {
          "containers": {
            "list": true, "view": true, "create": true, "edit": true, "delete": false,
            "assign_driver": true, "mark_arrived": true, "clearance_delivered": true,
            "set_reminder": true, "upload_attachment": true, "delete_attachment": true,
            "add_comment": true, "delete_comment": true, "add_penalty": false, "delete_penalty": false
          }
        },
        "crm": { "..." : "..." },
        "hr":  { "attendance": { "view_own": true, "view_all": true, "edit": false, "export": false } }
      }
    }
  }
}
```

---

## 7. Admin — User Management

> All `/api/crm/admin/*` endpoints require `Authorization: Bearer <token>` for a **General Manager** or Odoo system admin.  
> Any other role receives `{ "success": false, "error": "Forbidden", "code": 403 }`.

---

### `POST /api/crm/admin/users/list`

List all internal CRM users with their roles and override status.

**Request**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "search":    "ahmed",
    "role":      "supervisor",
    "job_title": "مشرف المبيعات",
    "active":    true,
    "limit":     50,
    "offset":    0
  }
}
```

All params are **optional**. Omit to get all users.

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 45,
      "limit": 50,
      "offset": 0,
      "users": [
        {
          "id": 5,
          "name": "Ahmed Al-Farsi",
          "email": "ahmed@company.com",
          "job_title": "مشرف المبيعات",
          "active": true,
          "role": "supervisor",
          "role_label": "CRM Supervisor / مشرف CRM",
          "has_individual_overrides": false,
          "override_notes": "",
          "avatar_url": "/web/image/res.users/5/avatar_128"
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/admin/users/create`

Create a new user and optionally assign their CRM role in one call.

**Request**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "name":      "Sara Al-Rashidi",
    "email":     "sara@company.com",
    "job_title": "مدير المبيعات",
    "role":      "manager",
    "password":  "Initial@123",
    "lang":      "ar_001"
  }
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | ✅ | Display name |
| `email` | string | ✅ | Used as login |
| `job_title` | string | ❌ | Sets `res.partner.function` |
| `role` | string | ❌ | `agent\|supervisor\|manager\|general_manager\|qa_auditor\|qa_supervisor` |
| `password` | string | ❌ | If omitted, Odoo sends reset link |
| `lang` | string | ❌ | `ar_001` / `en_US` (default: `en_US`) |

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "id": 42,
      "name": "Sara Al-Rashidi",
      "email": "sara@company.com",
      "job_title": "مدير المبيعات",
      "role": "manager",
      "active": true
    }
  }
}
```

---

### `POST /api/crm/admin/users/<id>/get`

Get full details of a specific user including their effective permissions.

**Request**
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

**Response** — same shape as `/me/permissions` but for any user.

---

### `POST /api/crm/admin/users/<id>/update`

Update any profile field of an existing user.

**Request**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "name":      "Sara Al-Rashidi",
    "email":     "sara.new@company.com",
    "job_title": "مدير العمليات",
    "phone":     "+966501234567",
    "mobile":    "+966509876543",
    "lang":      "ar_001",
    "notes":     "Senior manager — promoted May 2026"
  }
}
```

All fields are **optional** — only send what you want to change.

---

### `POST /api/crm/admin/users/<id>/change_password`

Force-change a user's password as admin (no old password needed).

**Request**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "new_password": "NewSecure@789" }
}
```

Minimum 6 characters required.

---

### `POST /api/crm/admin/users/<id>/deactivate`

Soft-disable a user (they cannot log in, data preserved).

```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

---

### `POST /api/crm/admin/users/<id>/activate`

Re-enable a previously deactivated user.

```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

---

### `POST /api/crm/admin/users/<id>/delete`

**Permanently** delete a user. Irreversible — prefer `/deactivate`.

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "confirm": true }
}
```

`confirm: true` is required as a safety gate.

---

### `POST /api/crm/admin/users/assign_role`

Assign a CRM role to a user by email.

**Request**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "email": "ahmed@company.com",
    "role":  "supervisor"
  }
}
```

This **replaces** the existing CRM role (removes previous one, adds new one).

---

### `POST /api/crm/admin/users/<id>/remove_role`

Strip all CRM roles from a user (sets them to `role: "none"`).  
Individual permission overrides are **preserved**.

```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

---

### `POST /api/crm/admin/users/bulk_assign`

Assign roles to multiple users in a single call.

**Request**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "assignments": [
      { "email": "user1@company.com", "role": "agent" },
      { "email": "user2@company.com", "role": "supervisor" },
      { "email": "user3@company.com", "role": "manager" }
    ]
  }
}
```

---

## 8. Admin — Permission Management

### `POST /api/crm/admin/users/<id>/permissions/get`

Returns the full 3-layer breakdown for a user — ideal for the admin permission editor screen.

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "user": {
        "id": 5, "name": "Ahmed Al-Farsi",
        "email": "ahmed@company.com", "job_title": "مشرف المبيعات",
        "role": "supervisor"
      },
      "layers": {
        "layer1_role_baseline": {
          "supply_chain": { "containers": { "list": true, "view": true, "create": true, "..." : "..." } }
        },
        "layer2_job_title_template": {
          "supply_chain": { "po": { "confirm": true } }
        },
        "layer3_individual_override": {
          "finance": { "invoices": { "list": true, "view": true } }
        }
      },
      "effective_permissions": {
        "supply_chain": { "..." : "..." },
        "finance": { "invoices": { "list": true, "view": true, "create": false, "..." : "..." } }
      },
      "job_title_override": "",
      "admin_notes": "Granted finance view access for Q2 audit",
      "has_individual_overrides": true
    }
  }
}
```

---

### `POST /api/crm/admin/users/<id>/permissions/set`

**The main endpoint for granting or restricting individual user permissions.**

Send only the keys you want to change (delta — not the full tree).

**Request — Grant specific permissions**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "permissions": {
      "finance": {
        "invoices": { "list": true, "view": true }
      },
      "inventory": {
        "stock": { "view": true, "adjust": true }
      }
    },
    "notes": "Q2 audit access — temporary"
  }
}
```

**Request — Apply to all users with the same job title**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "permissions": {
      "crm": { "analytics": { "view_team_data": true } }
    },
    "apply_to_all_same_job_title": true,
    "notes": "May 2026 — all supervisors now see team analytics"
  }
}
```

When `apply_to_all_same_job_title: true`:
- The backend saves the change as a **Job-Title Template** (Layer 2)
- Other users with the same job title automatically inherit it
- Existing individual overrides for those users are **not wiped**

**Request — Give user a different job title template temporarily**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "job_title_override": "مدير المستودع",
    "permissions": {},
    "notes": "Acting warehouse manager during leave"
  }
}
```

---

### `POST /api/crm/admin/users/<id>/permissions/reset`

Remove all individual overrides for a user. They fall back to their Job-Title Template → Role Baseline.

```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

---

## 9. Admin — Job-Title Templates

Templates define default permissions for a job title. Every user who has that job title automatically gets these permissions (Layer 2).

### `POST /api/crm/admin/permissions/schema`

Get the full permission tree structure + role baselines. Use this to **dynamically render the permission editor** in the FE — you never need to hardcode the tree.

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "tree": { "supply_chain": { "..." : "..." }, "crm": { "..." : "..." } },
      "roles": ["none", "agent", "supervisor", "manager", "general_manager", "qa_auditor", "qa_supervisor"],
      "role_baselines": {
        "agent":   { "supply_chain": { "containers": { "list": true, "view": true } } },
        "manager": { "finance": { "invoices": { "list": true, "view": true } } }
      }
    }
  }
}
```

---

### `POST /api/crm/admin/permissions/job_titles/list`

List all job-title permission templates.

**Request**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "search": "", "active": true }
}
```

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 8,
      "templates": [
        {
          "id": 1,
          "job_title": "مشرف المبيعات",
          "label": "Sales Supervisor",
          "crm_role": "supervisor",
          "is_active": true,
          "user_count": 7,
          "notes": ""
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/admin/permissions/job_titles/get`

Get full details of a single template including effective permissions.

**Request**
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
      "id": 1,
      "job_title": "مشرف المبيعات",
      "crm_role": "supervisor",
      "is_active": true,
      "user_count": 7,
      "permissions": { "...only the delta/overrides stored..." },
      "effective_permissions": { "...full resolved tree for this template..." }
    }
  }
}
```

---

### `POST /api/crm/admin/permissions/job_titles/upsert`

Create or update a job-title template. Optionally apply to all current users with that job title.

**Request — Create new template**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "job_title": "مشرف العمليات",
    "label":     "Operations Supervisor",
    "crm_role":  "supervisor",
    "permissions": {
      "supply_chain": {
        "containers": { "create": true, "edit": true, "add_penalty": true }
      },
      "inventory": {
        "stock": { "view": true, "adjust": true }
      }
    },
    "notes": "Standard template for operations supervisors",
    "apply_to_all_users": false
  }
}
```

**Request — Update template and push to all users**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "job_title": "مشرف العمليات",
    "permissions": {
      "finance": { "invoices": { "list": true, "view": true } }
    },
    "apply_to_all_users": true,
    "clear_individual_overrides": false
  }
}
```

When `apply_to_all_users: true`:
- All users with `job_title = "مشرف العمليات"` get their Layer 2 updated
- If `clear_individual_overrides: true` — individual overrides (Layer 3) are also wiped for those users

---

### `POST /api/crm/admin/permissions/job_titles/delete`

Soft-delete a job-title template (marks as inactive).

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "job_title": "مشرف العمليات" }
}
```

---

## 10. Admin — Bulk & Batch Operations

### `POST /api/crm/admin/users/bulk_permissions`

Apply the same permission changes to multiple users in one call.

**Request**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "user_ids": [5, 8, 12, 17, 23],
    "permissions": {
      "inventory": { "stock": { "view": true } },
      "analytics": { "dashboards": { "view": true } }
    },
    "mode":  "merge",
    "notes": "May 2026 update — new inventory view for supervisors"
  }
}
```

| `mode` | Behavior |
|--------|----------|
| `"merge"` | Deep-merge on top of each user's existing overrides *(default)* |
| `"replace"` | Wipe existing overrides and set these new ones |
| `"reset"` | Remove all individual overrides (`permissions` key is ignored) |

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 5,
      "processed": 5,
      "results": [
        { "user_id": 5,  "status": "merged" },
        { "user_id": 8,  "status": "merged" },
        { "user_id": 12, "status": "merged" },
        { "user_id": 17, "status": "error", "error": "User not found" },
        { "user_id": 23, "status": "merged" }
      ]
    }
  }
}
```

---

### `POST /api/crm/admin/users/compare_permissions`

Compare two users' effective permissions side-by-side. Returns only the keys that differ.

**Request**
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
            "add_penalty": { "user_a": false, "user_b": true },
            "delete":      { "user_a": false, "user_b": false }
          }
        },
        "finance": {
          "invoices": {
            "list": { "user_a": false, "user_b": true },
            "view": { "user_a": false, "user_b": true }
          }
        }
      },
      "permissions_a": { "...full tree for user A..." },
      "permissions_b": { "...full tree for user B..." }
    }
  }
}
```

---

## 11. Admin — Audit & Analytics

### `POST /api/crm/admin/audit/permissions`

Chronological log of all permission changes.

**Request**
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

All params are optional. Omit `user_id` to get all changes across all users.

**Response**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 3,
      "limit": 20,
      "offset": 0,
      "log": [
        {
          "id": 12,
          "user": {
            "id": 5,
            "name": "Ahmed Al-Farsi",
            "email": "ahmed@company.com",
            "job_title": "مشرف المبيعات"
          },
          "job_title_override": "",
          "permissions_delta": {
            "finance": { "invoices": { "list": true, "view": true } }
          },
          "notes": "Q2 audit access",
          "modified_by": {
            "id": 1, "name": "Admin", "email": "admin@company.com"
          },
          "modified_at": "2026-05-02T11:00:00",
          "last_write": "2026-05-02 11:00:00"
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/admin/stats`

High-level statistics for the admin dashboard. No params required.

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
        "no_role_list": [
          { "id": 9, "name": "New User", "email": "new@company.com" }
        ]
      },
      "roles": {
        "agent": 20,
        "supervisor": 10,
        "manager": 8,
        "general_manager": 2,
        "qa_auditor": 4,
        "qa_supervisor": 1
      },
      "templates": {
        "active": 8,
        "total": 9
      }
    }
  }
}
```

**Use this to power the admin dashboard cards:**

```tsx
function AdminDashboard() {
  const { data } = useAdminStats();
  return (
    <div>
      <StatCard label="Active Users"        value={data.users.total_active} />
      <StatCard label="No Role Assigned"    value={data.users.without_crm_role} color="warning" />
      <StatCard label="Custom Overrides"    value={data.users.with_individual_overrides} />
      <StatCard label="Job-Title Templates" value={data.templates.active} />
      <RoleChart data={data.roles} />
    </div>
  );
}
```

---

## 12. Admin — Export & Import

### `POST /api/crm/admin/export/permissions`

Export all users' permissions as a JSON snapshot (backup / bulk cache).

**Request**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "format": "full",
    "role":   "supervisor"
  }
}
```

| `format` | What's included |
|----------|----------------|
| `"full"` | Complete effective permissions for every user *(heavier)* |
| `"delta_only"` | Only individual overrides per user *(lighter, for backup)* |

`role` is optional — omit to export all users.

---

### `POST /api/crm/admin/import/permissions`

Restore individual permission overrides from a backup snapshot.

**Request**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "dry_run": true,
    "users": [
      {
        "email": "ahmed@company.com",
        "individual_overrides": {
          "finance": { "invoices": { "list": true, "view": true } }
        },
        "job_title_override": ""
      }
    ]
  }
}
```

Set `dry_run: true` first to preview what would change before committing.

---

## 13. All Endpoints — Quick Reference

### Current User

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/crm/me/permissions` | Get current user's full resolved permissions |

### Admin — Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/crm/admin/users/list` | List all users + roles |
| POST | `/api/crm/admin/users/create` | Create new user |
| POST | `/api/crm/admin/users/<id>/get` | Get user details + permissions |
| POST | `/api/crm/admin/users/<id>/update` | Update name, email, job title, phone, lang |
| POST | `/api/crm/admin/users/<id>/change_password` | Force change password |
| POST | `/api/crm/admin/users/<id>/deactivate` | Soft-disable user |
| POST | `/api/crm/admin/users/<id>/activate` | Re-enable user |
| POST | `/api/crm/admin/users/<id>/delete` | Permanently delete user |
| POST | `/api/crm/admin/users/assign_role` | Assign CRM role by email |
| POST | `/api/crm/admin/users/<id>/remove_role` | Strip all CRM roles |
| POST | `/api/crm/admin/users/bulk_assign` | Assign roles to multiple users |

### Admin — Permissions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/crm/admin/users/<id>/permissions/get` | 3-layer permission breakdown |
| POST | `/api/crm/admin/users/<id>/permissions/set` | Set individual overrides |
| POST | `/api/crm/admin/users/<id>/permissions/reset` | Remove all individual overrides |
| POST | `/api/crm/admin/users/bulk_permissions` | Apply permissions to multiple users |
| POST | `/api/crm/admin/users/compare_permissions` | Side-by-side permission diff |

### Admin — Job-Title Templates

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/crm/admin/permissions/schema` | Full permission tree + role baselines |
| POST | `/api/crm/admin/permissions/job_titles/list` | List all templates |
| POST | `/api/crm/admin/permissions/job_titles/get` | Get single template details |
| POST | `/api/crm/admin/permissions/job_titles/upsert` | Create / update template |
| POST | `/api/crm/admin/permissions/job_titles/delete` | Delete template |

### Admin — Audit & Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/crm/admin/audit/permissions` | Permission change history log |
| POST | `/api/crm/admin/stats` | Dashboard statistics |

### Admin — Export & Import

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/crm/admin/export/permissions` | Export all permissions as JSON |
| POST | `/api/crm/admin/import/permissions` | Restore permissions from backup |

---

## 14. Error Handling

All endpoints return consistent error shapes:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": false,
    "error":   "Human-readable error message",
    "code":    403
  }
}
```

| Scenario | `success` | `error` | `code` |
|----------|-----------|---------|--------|
| No JWT / expired token | `false` | `"Unauthorized"` | *(absent)* |
| Valid JWT but wrong role | `false` | `"Forbidden"` | `403` |
| Record not found | `false` | `"User not found"` / `"Template not found"` | *(absent)* |
| Missing required param | `false` | `"name and email are required"` | *(absent)* |
| Server exception | `false` | Exception message | *(absent)* |

### TypeScript error handler

```typescript
async function callApi(endpoint: string, params: object = {}) {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`,
    },
    body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params }),
  });

  const json = await response.json();
  const result = json.result;

  if (!result?.success) {
    if (result?.error === 'Unauthorized') {
      // redirect to login
      logout();
      return null;
    }
    if (result?.code === 403) {
      showToast('You do not have permission to perform this action', 'error');
      return null;
    }
    throw new Error(result?.error || 'Unknown error');
  }

  return result.data;
}
```

---

## 15. Frontend Integration Checklist

Use this checklist when building the admin UI:

### App Startup
- [ ] Call `POST /api/crm/me/permissions` immediately after successful login
- [ ] Store `permissions`, `role`, `job_title`, `has_individual_overrides` in global state
- [ ] Build `can()` / `canAll()` / `canAny()` helpers
- [ ] Use `can()` on all nav items, route guards, buttons, and action menus

### Admin Panel Screen
- [ ] Call `POST /api/crm/admin/stats` for dashboard cards
- [ ] Call `POST /api/crm/admin/users/list` (with search/filter) for user table
- [ ] Show badge/icon on users who have `has_individual_overrides: true`
- [ ] Show badge on users with `role: "none"` (no CRM role assigned)

### User Detail / Edit
- [ ] Call `POST /api/crm/admin/users/<id>/get` on open
- [ ] Show 3 tabs: Profile | Permissions | Audit Log
- [ ] Profile tab: use `POST /api/crm/admin/users/<id>/update`
- [ ] Permissions tab: call `POST /api/crm/admin/users/<id>/permissions/get` for 3-layer view
- [ ] Render the permission editor dynamically using `POST /api/crm/admin/permissions/schema`
- [ ] Save with `POST /api/crm/admin/users/<id>/permissions/set`
- [ ] Show "Apply to all same job title" checkbox → sets `apply_to_all_same_job_title: true`
- [ ] Audit tab: call `POST /api/crm/admin/audit/permissions` filtered by `user_id`

### Job-Title Templates Screen
- [ ] List with `POST /api/crm/admin/permissions/job_titles/list`
- [ ] Create/edit with `POST /api/crm/admin/permissions/job_titles/upsert`
- [ ] Show `user_count` to know how many are affected
- [ ] Show "Push to all current users" checkbox → sets `apply_to_all_users: true`

### Bulk Operations
- [ ] Multi-select users → "Apply Permissions" → `POST /api/crm/admin/users/bulk_permissions` with `mode: "merge"`
- [ ] Multi-select users → "Assign Role" → `POST /api/crm/admin/users/bulk_assign`
- [ ] "Compare" button on two users → `POST /api/crm/admin/users/compare_permissions`

### After Any Permission Change
- [ ] Refetch `POST /api/crm/me/permissions` if the admin changed **the current user's** permissions
- [ ] Show success toast with user name
- [ ] Refresh the user list or user detail as needed

---

## Appendix — Roles Default Permissions Summary

| Module / Section | Agent | Supervisor | Manager | GM | QA Auditor | QA Supervisor |
|-----------------|:-----:|:----------:|:-------:|:--:|:----------:|:-------------:|
| Supply Chain — view | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Supply Chain — create/edit | partial | ✅ | ✅ | ✅ | ❌ | ❌ |
| Supply Chain — delete | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Supply Chain — penalties | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| CRM — customers, tickets, tasks | ✅ | ✅ | ✅ | ✅ | view only | view only |
| CRM — delete records | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| CRM — analytics (team) | ❌ | ✅ | ✅ | ✅ | view only | view only |
| QA — score / review | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| QA — manage reviewers | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| POS — sessions / orders | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| POS — refund / delete | ❌ | partial | ✅ | ✅ | ❌ | ❌ |
| HR — own attendance/leaves | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| HR — team attendance/leaves | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| HR — salary / private data | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Inventory — view | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Inventory — adjust / transfer | ❌ | partial | ✅ | ✅ | ❌ | ❌ |
| Finance — invoices/bills | ❌ | ❌ | view | ✅ | ❌ | ❌ |
| Finance — full accounting | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Analytics — dashboards | view | view | ✅ | ✅ | view | view |
| Settings | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Admin Panel | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
