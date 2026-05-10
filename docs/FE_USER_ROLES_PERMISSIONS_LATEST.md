# FE User Roles & Permissions Integration Guide

> **Changelog — 2026-05-10**
>
> Breaking / notable changes in this revision:
>
> 1. **`apply_to_all_same_job_title` removed** — replaced by `apply_to_all_same_crm_role` in `POST /api/crm/admin/users/<id>/permissions/set`. The new flag saves the permissions as a *role-level* template (e.g. "agent", "supervisor") rather than a job-title template.
>
> 2. **Permission schema trimmed** — `POST /api/crm/admin/permissions/schema` and all user permission responses now return **only the 5 FE modules** (crm, supply_chain, pos, admin, settings). Internal-only paths (crm.branches, crm.config, supply_chain clearance/tracking/etc.) no longer appear in responses.
>
> 3. **New FE permission keys added** — the following are now part of the schema:
>    - `crm.pipeline.view`
>    - `crm.promotions.{list,create,edit,delete}`
>    - `pos.products.{import,export}`
>    - `settings.templates.{view,create,edit,delete}`
>    - `settings.rules.{view,create,edit,delete}`
>    - `settings.channels.{view,edit}`
>    - `settings.sla.{view,edit}`
>    - `settings.shifts.{view,manage}`
>
> 4. **`routes` map added** — every user permission response now includes a `routes` key (see §Routes Map below). Use this to show/hide navigation items without inspecting individual leaf permissions.
>
> 5. **Permission resolution now has 5 layers** (was 3):
>    1. Empty PERMISSION_TREE
>    2. CRM role baseline (hardcoded)
>    3. **NEW** — CRM-role template (admin-set overrides for the whole role)
>    4. Job-title template
>    5. Individual user override

This is the current frontend contract for the CRM user roles and permissions system.

## Core Rule

The frontend must treat `POST /api/crm/me/permissions` as the single source of truth for UI permissions.

The backend computes permissions in this order:

1. CRM role baseline (hardcoded defaults per role).
2. CRM-role template — admin-customised overrides for the entire role group.
3. Job-title template — overrides for a specific job title.
4. Individual user override — highest priority.

The FE must not merge these layers itself. It receives the final resolved tree.

## Auth And JSON-RPC Shape

Every request is JSON-RPC:

```ts
const response = await api.post('/api/crm/me/permissions', {
  jsonrpc: '2.0',
  method: 'call',
  params: {},
});

const result = response.data?.result;
if (!result?.success) throw new Error(result?.error || 'Request failed');

const user = result.data;
const permissions = user.permissions;
```

Important: the data is under `response.data.result.data`, not `response.data.data`.

Required headers:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Login Bootstrap Flow

After successful login:

1. Store the JWT access token.
2. Call `POST /api/crm/me/permissions`.
3. Store the returned user profile and `permissions` tree in global state.
4. Render navigation, buttons, settings pages, and actions from that tree.

Recommended state shape:

```ts
type AuthState = {
  token: string;
  user: {
    id: number;
    name: string;
    email: string;
    login: string;
    role: CrmRole;
    role_label: string;
    job_title: string;
    has_individual_overrides: boolean;
    avatar_url: string;
  };
  permissions: PermissionTree;
  routes: RouteVisibility;  // NEW — use this to show/hide nav items
};
```

## Routes Map

Every permission response now includes a `routes` key alongside `permissions`:

```ts
// routes is a flat map of module and module.section → boolean
// A route is "true" when at least one action in that section is enabled.
type RouteVisibility = {
  // Module-level
  crm: boolean;
  supply_chain: boolean;
  pos: boolean;
  admin: boolean;
  settings: boolean;
  // Section-level
  'crm.customers': boolean;
  'crm.tickets': boolean;
  'crm.tasks': boolean;
  'crm.calls': boolean;
  'crm.omnichannel': boolean;
  'crm.knowledge': boolean;
  'crm.analytics': boolean;
  'crm.pipeline': boolean;
  'crm.promotions': boolean;
  'supply_chain.containers': boolean;
  'supply_chain.vendors': boolean;
  'supply_chain.po': boolean;
  'supply_chain.negotiations': boolean;
  'supply_chain.item_requests': boolean;
  'supply_chain.chat': boolean;
  'pos.products': boolean;
  'pos.orders': boolean;
  'pos.config': boolean;
  'admin.users': boolean;
  'admin.permissions': boolean;
  'admin.audit_logs': boolean;
  'settings.general': boolean;
  'settings.templates': boolean;
  'settings.rules': boolean;
  'settings.channels': boolean;
  'settings.sla': boolean;
  'settings.shifts': boolean;
};
```

**Usage in your router / sidebar:**

```ts
// Show a nav item only if the route is accessible
if (store.routes['crm.customers']) showNavItem('customers');
if (store.routes['admin']) showModule('admin');

// Or use a helper
function canAccessRoute(section: string): boolean {
  return store.routes[section] === true;
}
```

Roles:

```ts
type CrmRole =
  | 'none'
  | 'agent'
  | 'supervisor'
  | 'manager'
  | 'general_manager'
  | 'qa_auditor'
  | 'qa_supervisor';
```

## PermissionTree TypeScript Type

```ts
// Exact shape returned by /api/crm/me/permissions and /api/crm/admin/users/<id>/permissions/get
type PermissionTree = {
  crm: {
    customers:  { list: boolean; view: boolean; create: boolean; edit: boolean; delete: boolean; import: boolean; export: boolean; merge: boolean };
    tickets:    { list: boolean; view: boolean; create: boolean; edit: boolean; delete: boolean; assign: boolean; escalate: boolean; close: boolean };
    tasks:      { list: boolean; view: boolean; create: boolean; edit: boolean; delete: boolean; assign: boolean; close: boolean };
    calls:      { list: boolean; view: boolean; create: boolean; edit: boolean; delete: boolean; listen_recording: boolean };
    omnichannel:{ view: boolean; reply: boolean; assign: boolean };
    knowledge:  { list: boolean; view: boolean; create: boolean; edit: boolean; delete: boolean };
    analytics:  { view: boolean; export: boolean; view_team_data: boolean };
    pipeline:   { view: boolean };
    promotions: { list: boolean; create: boolean; edit: boolean; delete: boolean };
  };
  supply_chain: {
    containers:    { list: boolean; view: boolean; create: boolean; edit: boolean; delete: boolean; assign_driver: boolean; unassign_driver: boolean; mark_arrived: boolean; clearance_delivered: boolean; set_reminder: boolean; upload_attachment: boolean; delete_attachment: boolean; add_comment: boolean; delete_comment: boolean; add_penalty: boolean; delete_penalty: boolean };
    vendors:       { list: boolean; view: boolean; create: boolean; edit: boolean; delete: boolean };
    po:            { list: boolean; view: boolean; create: boolean; edit: boolean; delete: boolean; confirm: boolean; ship: boolean; receive: boolean; cancel: boolean; reopen: boolean; add_line: boolean; edit_line: boolean; delete_line: boolean; upload_attachment: boolean; delete_attachment: boolean; add_comment: boolean; delete_comment: boolean };
    negotiations:  { list: boolean; view: boolean; create: boolean; edit: boolean; delete: boolean; add_comment: boolean; delete_comment: boolean };
    item_requests: { list: boolean; view: boolean; create: boolean; edit: boolean; delete: boolean; approve: boolean; reject: boolean; fulfill: boolean };
    chat:          { view: boolean; send: boolean; delete_message: boolean };
  };
  pos: {
    products: { list: boolean; view: boolean; create: boolean; edit: boolean; delete: boolean; set_price: boolean; set_discount: boolean; import: boolean; export: boolean };
    orders:   { list: boolean; view: boolean; create: boolean; edit: boolean; delete: boolean; refund: boolean; export_pdf: boolean };
    config:   { view: boolean; edit: boolean };
  };
  admin: {
    users:       { list: boolean; view: boolean; create: boolean; assign_role: boolean; deactivate: boolean; activate: boolean };
    permissions: { view: boolean; set_job_title_defaults: boolean; set_user_overrides: boolean };
    audit_logs:  { view: boolean; export: boolean };
  };
  settings: {
    general:   { view: boolean; edit: boolean };
    templates: { view: boolean; create: boolean; edit: boolean; delete: boolean };
    rules:     { view: boolean; create: boolean; edit: boolean; delete: boolean };
    channels:  { view: boolean; edit: boolean };
    sla:       { view: boolean; edit: boolean };
    shifts:    { view: boolean; manage: boolean };
  };
};
```

## Permission Helpers

Use dot paths everywhere in the FE.

```ts
export function can(permissions: any, path: string): boolean {
  return path.split('.').reduce((obj, key) => obj?.[key], permissions) === true;
}

export function canAll(permissions: any, ...paths: string[]): boolean {
  return paths.every((path) => can(permissions, path));
}

export function canAny(permissions: any, ...paths: string[]): boolean {
  return paths.some((path) => can(permissions, path));
}
```

Example:

```tsx
{can(permissions, 'supply_chain.containers.create') && <CreateContainerButton />}
{can(permissions, 'admin.permissions.set_user_overrides') && <PermissionsEditor />}
```

## Admin Settings Page Requirements

The CRM settings page for permissions should be visible when:

```ts
can(permissions, 'admin.permissions.view')
```

Show user management actions when:

```ts
can(permissions, 'admin.users.list')
can(permissions, 'admin.users.view')
can(permissions, 'admin.users.create')
can(permissions, 'admin.users.assign_role')
can(permissions, 'admin.users.deactivate')
can(permissions, 'admin.users.activate')
```

Show permission editing actions when:

```ts
can(permissions, 'admin.permissions.set_user_overrides')
can(permissions, 'admin.permissions.set_job_title_defaults')
```

## Admin Endpoints

All admin endpoints require an admin user. Backend admin means one of:

- Odoo user id `1`.
- Odoo `base.group_system`.
- CRM `general_manager`.

### Permission Schema

Use this to render the permission editor dynamically:

```ts
POST /api/crm/admin/permissions/schema
params: {}
```

Response data:

```ts
{
  // FE-facing schema only — internal paths excluded
  tree: PermissionTree;
  roles: CrmRole[];
  // Each baseline is already filtered to the FE schema
  role_baselines: Record<CrmRole, PermissionTree>;
}
```

### Users List

```ts
POST /api/crm/admin/users/list
params: {
  page?: number;
  per_page?: number;
  active?: boolean;
  search?: string;
  role?: CrmRole;
  job_title?: string;
  with_perms?: boolean;
}
```

Use `with_perms: true` only when the list must show effective permission summaries. It is heavier.

### User Permission Detail

```ts
POST /api/crm/admin/users/:userId/permissions/get
params: {}
```

Use this when opening the permission editor for one user. It returns:

- User role.
- Role baseline.
- Job-title template snapshot.
- Individual overrides.
- Effective permissions.

### Set User Overrides

```ts
POST /api/crm/admin/users/:userId/permissions/set
params: {
  permissions: Partial<PermissionTree>;
  apply_to_all_same_crm_role?: boolean;  // replaces apply_to_all_same_job_title
  job_title_override?: string;
  notes?: string;
}
```

**`apply_to_all_same_crm_role`**: when `true`, the permissions are saved as a role-level template for the user's CRM role (e.g. "agent"). Every user with that role inherits them as their step-3 baseline. The current user's individual override is cleared. Use this from the admin permissions page to set defaults for an entire role.

Send only the delta the admin changed (partial tree is fine). Example — individual override:

```json
{
  "permissions": {
    "supply_chain": {
      "containers": { "create": true, "delete": false }
    }
  },
  "notes": "Temporary supervisor access for container creation"
}
```

Example — apply to entire role:

```json
{
  "permissions": {
    "crm": {
      "promotions": { "list": true, "create": true, "edit": true }
    }
  },
  "apply_to_all_same_crm_role": true,
  "notes": "Enable promotions for all supervisors"
}
```

### Reset User Overrides

```ts
POST /api/crm/admin/users/:userId/permissions/reset
params: {}
```

### Job-Title Templates

List:

```ts
POST /api/crm/admin/permissions/job_titles/list
params: {
  search?: string;
  active?: boolean;
}
```

Create/update:

```ts
POST /api/crm/admin/permissions/job_titles/upsert
params: {
  job_title: string;
  crm_role?: CrmRole;
  label?: string;
  notes?: string;
  permissions: Partial<PermissionTree>;
  apply_to_all_users?: boolean;
}
```

Delete:

```ts
POST /api/crm/admin/permissions/job_titles/delete
params: {
  job_title: string;
}
```

### Assign Role

```ts
POST /api/crm/admin/users/assign_role
params: {
  email: string;
  role: CrmRole;
}
```

Bulk:

```ts
POST /api/crm/admin/users/bulk_assign
params: {
  assignments: Array<{ email: string; role: CrmRole }>;
}
```

## Backend-Enforced Permission Paths

The following routes now enforce the same permission tree returned to the FE.

### Supply Chain

Vendors:

```ts
'supply_chain.vendors.list'
'supply_chain.vendors.view'
'supply_chain.vendors.create'
'supply_chain.vendors.edit'
'supply_chain.vendors.delete'
```

Containers:

```ts
'supply_chain.containers.list'
'supply_chain.containers.view'
'supply_chain.containers.create'
'supply_chain.containers.edit'
'supply_chain.containers.delete'
'supply_chain.containers.assign_driver'
'supply_chain.containers.unassign_driver'
'supply_chain.containers.mark_arrived'
'supply_chain.containers.clearance_delivered'
'supply_chain.containers.set_reminder'
'supply_chain.containers.upload_attachment'
'supply_chain.containers.delete_attachment'
'supply_chain.containers.add_comment'
'supply_chain.containers.delete_comment'
'supply_chain.containers.add_penalty'
'supply_chain.containers.delete_penalty'
```

Purchase orders:

```ts
'supply_chain.po.list'
'supply_chain.po.view'
'supply_chain.po.create'
'supply_chain.po.edit'
'supply_chain.po.delete'
'supply_chain.po.confirm'
'supply_chain.po.ship'
'supply_chain.po.receive'
'supply_chain.po.cancel'
'supply_chain.po.reopen'
'supply_chain.po.add_line'
'supply_chain.po.edit_line'
'supply_chain.po.delete_line'
'supply_chain.po.upload_attachment'
'supply_chain.po.delete_attachment'
'supply_chain.po.add_comment'
'supply_chain.po.delete_comment'
```

### CRM

Customers:

```ts
'crm.customers.list'
'crm.customers.view'
'crm.customers.create'
'crm.customers.edit'
'crm.customers.delete'
'crm.customers.import'
```

Calls:

```ts
'crm.calls.list'
'crm.calls.view'
'crm.calls.create'
'crm.calls.edit'
'crm.calls.delete'
```

Tickets:

```ts
'crm.tickets.list'
'crm.tickets.view'
'crm.tickets.create'
'crm.tickets.edit'
'crm.tickets.delete'
'crm.tickets.assign'
'crm.tickets.escalate'
'crm.tickets.close'
```

Tasks:

```ts
'crm.tasks.list'
'crm.tasks.view'
'crm.tasks.create'
'crm.tasks.edit'
'crm.tasks.delete'
'crm.tasks.assign'
'crm.tasks.close'
```

Branches:

```ts
'crm.branches.list'
'crm.branches.view'
'crm.branches.create'
'crm.branches.edit'
'crm.branches.delete'
```

Settings announcements / marquee:

```ts
'settings.general.view'
'settings.general.edit'
```

## UI Mapping Checklist

Use the exact same paths for buttons and pages:

```ts
const nav = [
  { key: 'customers', show: can(perms, 'crm.customers.list') },
  { key: 'tasks', show: can(perms, 'crm.tasks.list') },
  { key: 'tickets', show: can(perms, 'crm.tickets.list') },
  { key: 'calls', show: can(perms, 'crm.calls.list') },
  { key: 'supply', show: canAny(perms, 'supply_chain.containers.list', 'supply_chain.po.list') },
  { key: 'settings', show: can(perms, 'admin.permissions.view') || can(perms, 'settings.general.view') },
];
```

Examples:

```tsx
<Button hidden={!can(perms, 'crm.customers.create')}>New Customer</Button>
<Button hidden={!can(perms, 'crm.customers.edit')}>Edit Customer</Button>
<Button hidden={!can(perms, 'crm.customers.delete')}>Delete Customer</Button>

<Button hidden={!can(perms, 'supply_chain.po.confirm')}>Confirm PO</Button>
<Button hidden={!can(perms, 'supply_chain.po.ship')}>Ship PO</Button>
<Button hidden={!can(perms, 'supply_chain.po.receive')}>Receive PO</Button>

<Button hidden={!can(perms, 'admin.users.assign_role')}>Assign Role</Button>
<Button hidden={!can(perms, 'admin.permissions.set_user_overrides')}>Save User Permissions</Button>
```

## Error Handling

Permission failures return:

```json
{
  "success": false,
  "error": "Forbidden — permission required: crm.customers.delete",
  "code": 403,
  "error_code": "PERMISSION_DENIED",
  "permission": "crm.customers.delete"
}
```

FE behavior:

1. If `code === 403`, show a permission message.
2. If `permission` is present, optionally log/report which permission is missing.
3. Do not retry automatically.
4. If the user believes access should exist, tell them to ask an admin to update permissions.

## Known Remaining Backend Coverage

The backend now has a reusable permission-tree guard and the main CRM/supply routes above enforce it. Some secondary modules may still rely on JWT-only, ownership rules, or old group checks and should be aligned in the next backend pass:

- `supply_extended_controller.py`
- `config_controller.py`
- `qa_controller.py`
- `analytics_controller.py`
- `pos_bridge_controller.py`
- `price_list_controller.py`
- `supply_chat_controller.py`
- `supply_stories_controller.py`
- `crm_notifications_controller.py`

For FE, still guard those screens/actions with the permission tree. Backend hard enforcement will continue to be expanded route by route.
