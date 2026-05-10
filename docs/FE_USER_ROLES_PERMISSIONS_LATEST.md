# Frontend Integration: User Roles & Permissions
**Updated: 2026-05-10** — Schema v2.1 (real-time permission push)

---

## Changelog

| Date | Version | Summary |
|------|---------|---------|
| 2026-05-10 | **v2.1** | Added real-time `crm.permissions.updated` push event on `supply_user.<uid>` bus channel. Added recommended boot flow and WebSocket handler guidance. `route_visibility` overrides now correctly mask permission leaves. |
| 2026-05-10 | v2 | Full schema realignment to FE UI. Introduced `current_view_crm_tree` / `future_edits_crm_tree` split. Renamed `apply_to_all_same_job_title` → `apply_to_all_same_crm_role`. Added `routes` map to every permission response. All path keys updated to match FE route names. |
| 2026-05-06 | v1 | Initial backend permission system documentation. |

---

## Recommended FE Boot Flow

**This is the canonical flow after every login:**

```
1. POST /lugal/auth/login           → receive access_token (JWT)
2. POST /api/crm/me/permissions     → receive permissions + routes + route_visibility
3. Store in global app state (Redux / Pinia / Zustand / etc.)
4. Gate navigation from routes.*
5. Gate actions/buttons from permissions.*
```

**No username is passed to step 2.** The JWT in the `Authorization: Bearer` header identifies the user.

### Re-fetching permissions (without logout)

Call **`POST /api/crm/me/permissions`** again whenever:

- A `crm.permissions.updated` WebSocket event is received (see below — **preferred**).
- App is focused after idle > 30 min.
- User visits Settings page.

---

## Real-Time Permission Push (WebSocket)

When an admin changes any user's permissions (via `permissions/set` or `permissions/reset`),
the backend **automatically pushes** a `crm.permissions.updated` event to the affected
user's personal bus channel. No polling required.

### Channel

The event arrives on `supply_user.<uid>` — the **same channel** already subscribed to
for supply chat (returned by `POST /api/crm/supply/chat/bus_channels`).
No additional subscription is needed.

### Event payload

```json
{
  "type": "crm.permissions.updated",
  "changed_by_uid": 3,
  "timestamp": "2026-05-10T14:35:22"
}
```

### FE handler (recommended)

```javascript
// In your bus/WebSocket message handler:
if (message.type === 'crm.permissions.updated') {
  // Re-fetch and replace the cached permissions store
  const { data } = await api.post('/api/crm/me/permissions');
  permissionsStore.set(data);
  routesStore.set(data.routes);
}
```

**Do not** try to apply the push payload directly as the new permissions state —
it contains no permission data, just a signal. Always re-call `/api/crm/me/permissions`
to get the authoritative current state.

### When `apply_to_all_same_crm_role: true`

The push goes to **every active user** in that CRM role simultaneously,
so all affected users refresh without knowing the admin made a change.

---

## Overview

Every authenticated user has an **effective permissions** object that is a deep-merged result of:

1. Empty tree (all actions = `false`)
2. CRM role baseline (hardcoded defaults per role)
3. CRM-role template (admin-customised overrides for the whole role)
4. Job-title template (per-title overrides)
5. User-specific overrides (highest priority)

Admins use the Settings → Permissions page to customise steps 3–5.

---

## Permission Schema

### `current_view_crm_tree`
All routes currently rendered in the CRM frontend UI.

```json
{
  "dashboard":      { "view": bool, "view_team_data": bool, "export": bool },
  "customers":      { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "import": bool, "export": bool, "merge": bool },
  "products":       { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "set_price": bool, "set_discount": bool, "import": bool, "export": bool },
  "orders":         { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "create_invoice": bool, "refund": bool, "export_pdf": bool, "view_delivery": bool, "view_branches": bool, "view_samples": bool },
  "omni_channel":   { "view": bool, "reply": bool, "assign": bool },
  "tickets":        { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "assign": bool, "escalate": bool, "close": bool },
  "tasks":          { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "assign": bool, "close": bool, "view_projects": bool, "manage_projects": bool },
  "employees":      { "list": bool, "view": bool, "create": bool, "edit": bool, "deactivate": bool, "assign_role": bool, "add_task": bool, "message": bool },
  "sales_pipeline": { "view": bool },
  "forecasting":    { "view": bool, "export": bool },
  "supply_chain": {
    "containers":      { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "assign_driver": bool, "unassign_driver": bool, "mark_arrived": bool, "clearance_delivered": bool, "set_reminder": bool, "upload_attachment": bool, "delete_attachment": bool, "add_comment": bool, "delete_comment": bool, "add_penalty": bool, "delete_penalty": bool },
    "purchase_orders": { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "confirm": bool, "ship": bool, "receive": bool, "cancel": bool, "reopen": bool, "add_line": bool, "edit_line": bool, "delete_line": bool, "upload_attachment": bool, "delete_attachment": bool, "add_comment": bool, "delete_comment": bool, "export_pdf": bool },
    "negotiations":    { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "add_comment": bool, "delete_comment": bool },
    "item_requests":   { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "approve": bool, "reject": bool, "fulfill": bool },
    "vendors":         { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool }
  },
  "conversations": {
    "chat":      { "view": bool, "send": bool, "delete_message": bool, "create_group": bool, "add_member": bool, "remove_member": bool, "manage_group": bool, "pin_message": bool, "broadcast": bool, "forward": bool, "search": bool },
    "email":     { "view": bool, "send": bool, "reply": bool, "forward": bool, "delete": bool, "manage_rules": bool },
    "stories":   { "view": bool, "create": bool, "delete": bool },
    "localsend": { "view": bool, "send": bool }
  },
  "promotions":     { "list": bool, "create": bool, "edit": bool, "delete": bool },
  "analytics":      { "view": bool, "export": bool, "view_team_data": bool },
  "knowledge_base": { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool },
  "call_centre":    { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool, "listen_recording": bool },
  "event_log":      { "view": bool, "export": bool, "delete": bool },
  "admin_dashboard":{ "view": bool, "manage_users": bool, "manage_tasks": bool },
  "settings": {
    "general":      { "view": bool, "edit": bool },
    "permissions":  { "view": bool, "set_user_overrides": bool, "set_job_title_defaults": bool },
    "templates":    { "view": bool, "create": bool, "edit": bool, "delete": bool },
    "rules":        { "view": bool, "create": bool, "edit": bool, "delete": bool },
    "channels":     { "view": bool, "edit": bool },
    "sla":          { "view": bool, "edit": bool },
    "shifts":       { "view": bool, "manage": bool },
    "omni_channels":{ "view": bool, "edit": bool }
  }
}
```

### `future_edits_crm_tree`
Backend-only internal paths not yet exposed in the FE UI.

```json
{
  "branches": { "list": bool, "view": bool, "create": bool, "edit": bool, "delete": bool }
}
```

---

## Routes Map

Every permission response includes a `routes` object. Use this for **navigation visibility** — show/hide sidebar items, tabs, and menu entries.

```json
{
  "routes": {
    "dashboard":                   true,
    "customers":                   true,
    "products":                    false,
    "orders":                      false,
    "omni_channel":                true,
    "tickets":                     true,
    "tasks":                       true,
    "employees":                   false,
    "sales_pipeline":              false,
    "forecasting":                 false,
    "supply_chain":                true,
    "supply_chain.containers":     true,
    "supply_chain.purchase_orders":true,
    "supply_chain.negotiations":   false,
    "supply_chain.item_requests":  false,
    "supply_chain.vendors":        false,
    "conversations":               true,
    "conversations.chat":          true,
    "conversations.email":         false,
    "conversations.stories":       true,
    "conversations.localsend":     true,
    "promotions":                  false,
    "analytics":                   true,
    "knowledge_base":              true,
    "call_centre":                 true,
    "event_log":                   false,
    "admin_dashboard":             false,
    "settings":                    true,
    "settings.general":            true,
    "settings.permissions":        false,
    "settings.templates":          false,
    "settings.rules":              false,
    "settings.channels":           false,
    "settings.sla":                false,
    "settings.shifts":             false,
    "settings.omni_channels":      false
  }
}
```

### Route visibility — how it's computed

Each route key goes through **two steps** in priority order:

| Priority | Source | Wins when |
|----------|--------|-----------|
| 1 (low) | Computed from actions | `any(actions) == True` → route visible |
| 2 (high) | **Explicit `route_visibility` override** | Admin set an explicit `true`/`false` for that path |

An explicit override **always wins** over the computed value. When a route is explicitly set to `false`, the backend also masks every action permission under that route to `false` in responses and backend permission checks.

### Setting route visibility (admin)

Pass `route_visibility` alongside `permissions` in the `/permissions/set` call:

```json
{
  "params": {
    "permissions": {
      "supply_chain": { "containers": { "list": true, "view": true } }
    },
    "route_visibility": {
      "supply_chain.purchase_orders": false,
      "supply_chain.negotiations":    false,
      "conversations.email":          false,
      "event_log":                    false
    }
  }
}
```

- `false` → **always hide** this nav route for this user and force all permission leaves under that route to `false`.
- `true` → **always show** this nav route, even if all action permissions are currently `false`. This does not grant action permissions by itself.
- **Omit a key** → fall back to computed (route shown if any action in it is `true`).

> **Important:** Route visibility overrides are per-user (or per-role when `apply_to_all_same_crm_role: true`). The same API call, same endpoint — just add the `route_visibility` field.

### Getting all valid route paths

The schema endpoint returns `settable_route_paths` — the complete list of paths the FE can use in `route_visibility`:

```
POST /api/crm/admin/permissions/schema
→ data.settable_route_paths: [
    "dashboard", "customers", "products", "orders", "omni_channel",
    "tickets", "tasks", "employees", "sales_pipeline", "forecasting",
    "supply_chain", "supply_chain.containers", "supply_chain.purchase_orders",
    "supply_chain.negotiations", "supply_chain.item_requests", "supply_chain.vendors",
    "conversations", "conversations.chat", "conversations.email",
    "conversations.stories", "conversations.localsend",
    "promotions", "analytics", "knowledge_base", "call_centre",
    "event_log", "admin_dashboard",
    "settings", "settings.general", "settings.permissions",
    "settings.templates", "settings.rules", "settings.channels",
    "settings.sla", "settings.shifts", "settings.omni_channels"
  ]
```

---

## CRM Roles

| Value | Display Name | Notes |
|-------|-------------|-------|
| `none` | No Role | Minimal access |
| `agent` | Agent | Everyday CRM, basic supply chain |
| `supervisor` | Supervisor | Team management, approve POs |
| `manager` | Manager | Full ops, settings access |
| `general_manager` | General Manager | Full system access |
| `qa_auditor` | QA Auditor | Read-only + can score reviews |
| `qa_supervisor` | QA Supervisor | QA team management + exports |

System admins (Odoo uid=1 or `base.group_system`) bypass all permission checks.

---

## API Endpoints

### Get current user's permissions
```
POST /api/crm/me/permissions
Authorization: Bearer <jwt>
```
Response:
```json
{
  "success": true,
  "data": {
    "id": 5,
    "role": "agent",
    "permissions": { ...current_view_crm_tree with actual booleans... },
    "routes": { ...route visibility map... }
  }
}
```

### Get permission schema (admin only)
```
POST /api/crm/admin/permissions/schema
Authorization: Bearer <jwt>
```
Response:
```json
{
  "success": true,
  "data": {
    "current_view_crm_tree": { ...all false...  },
    "future_edits_crm_tree": { ...all false... },
    "roles":  ["none","agent","supervisor","manager","general_manager","qa_auditor","qa_supervisor"],
    "role_baselines": {
      "agent": {
        "current_view_crm_tree": { ...defaults for agent... },
        "future_edits_crm_tree": { ...internal defaults... }
      }
    }
  }
}
```

### Get a user's permissions (admin only)
```
POST /api/crm/admin/users/<id>/permissions/get
Authorization: Bearer <jwt>
```

### Set a user's permissions (admin only)
```
POST /api/crm/admin/users/<id>/permissions/set
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "permissions": {
      "customers":   { "delete": true, "export": true },
      "supply_chain":{ "purchase_orders": { "confirm": true, "ship": true } }
    },
    "route_visibility": {
      "supply_chain.negotiations": false,
      "conversations.email":       false,
      "event_log":                 false
    },
    "apply_to_all_same_crm_role": false,
    "notes": "Manager review — expanded access approved by John"
  }
}
```

**`route_visibility`** (object, optional) — explicit route-level show/hide map.
- Keys must be valid paths from `data.settable_route_paths` (returned by the schema endpoint).
- `false` → **always hide** this nav section for the user, even if they have action permissions inside it.
- `true` → **always show** this nav section, even if all action permissions inside it are `false`.
- **Omit a key** → computed automatically: route visible if at least one action inside is `true`.

**`apply_to_all_same_crm_role`** (boolean, default `false`):
- `false` → Save as this user's individual override only.
- `true` → Upsert the **role-level template** for the user's CRM role. All users with that role will inherit it (step 3 in the resolution chain). This user's own individual override is cleared.

### Reset user to role defaults
```
POST /api/crm/admin/users/<id>/permissions/reset
Authorization: Bearer <jwt>
```
Clears all individual overrides. The user reverts to their role baseline + any role template + job-title template.

### List all users (admin only)
```
POST /api/crm/admin/users/list
Authorization: Bearer <jwt>
```

---

## Permission Check Examples (Frontend)

```javascript
// Can this user see the customers list page?
const canAccessCustomers = routes['customers'];

// Can this user create a purchase order?
const canCreatePO = permissions.supply_chain?.purchase_orders?.create;

// Should the supply chain nav item be visible?
const showSupplyChain = routes['supply_chain'];

// Should the "Containers" sub-tab be visible?
const showContainers = routes['supply_chain.containers'];

// Can the user access settings at all?
const showSettings = routes['settings'];

// Can the user view the permissions settings page?
const canViewPermSettings = permissions.settings?.permissions?.view;
```

---

## Group Chat Member Management

The `conversations.chat` section has **three independent group permission flags**:

| Permission key | What it controls |
|---------------|-----------------|
| `create_group` | Can create a new group chat |
| `add_member` | Can add new participants to an existing group |
| `remove_member` | Can kick / remove participants from a group |
| `manage_group` | Can rename group, change avatar, promote/demote admins |

These are separate so the admin can grant, e.g., "can add members but not remove" without giving full management rights.

**FE check example:**
```javascript
// Show the "Add Member" button inside the group chat UI
const canAddMember = permissions.conversations?.chat?.add_member;

// Show the "Remove Member" action on a participant card
const canRemoveMember = permissions.conversations?.chat?.remove_member;
```

**Set via the same API** — no structural change needed:
```json
{
  "params": {
    "permissions": {
      "conversations": {
        "chat": {
          "add_member": true,
          "remove_member": false
        }
      }
    }
  }
}
```

---

## Notes for Admin UI

1. **The schema endpoint** (`/api/crm/admin/permissions/schema`) returns `current_view_crm_tree` — use this to render the permissions form checkboxes dynamically.
2. **Role baselines** in the schema show what each role gets by default before any admin customisation.
3. **Section-level toggle:** Turning off an entire section (e.g. "supply_chain") means setting all its leaf actions to `false`. The backend computes `routes["supply_chain"] = false` automatically.
4. **Internal paths** (`future_edits_crm_tree`) are not shown in the permissions UI — they are backend-only guards for routes not yet visible in the FE.
5. **System admin bypass:** Users with Odoo admin or General Manager role always have full access regardless of the permission tree.
