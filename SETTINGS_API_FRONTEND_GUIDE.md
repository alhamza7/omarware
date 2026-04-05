# Settings API — Complete Frontend Developer Guide

> **Version:** 1.0.0  
> **Date:** 2026-03-30  
> **Author:** Backend Team  
> **Base URL:** `http://<SERVER>:8070`

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Protocol Reference](#2-protocol-reference)
3. [Phase 1 — User Preferences API](#3-phase-1--user-preferences-api)
4. [Phase 2 — KPI Rules CRUD](#4-phase-2--kpi-rules-crud)
5. [Phase 3 — Single Shift Endpoint](#5-phase-3--single-shift-endpoint)
6. [Phase 4 — POS Settings Expansion](#6-phase-4--pos-settings-expansion)
7. [Phase 5 — System Admin API](#7-phase-5--system-admin-api)
8. [TypeScript Type Definitions](#8-typescript-type-definitions)
9. [Full Example — Hydrate Settings on Login](#9-full-example--hydrate-settings-on-login)
10. [Error Handling Reference](#10-error-handling-reference)

---

## 1. Authentication

All endpoints require a valid JWT token from `lugal_auth`.

### Obtaining a Token

```http
POST /lugal/auth/login
Content-Type: application/json

{
  "login": "user@example.com",
  "password": "yourpassword"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user_id": 5,
  "name": "Ahmed Ali"
}
```

### Using the Token

Add the `Authorization` header to every request:

```http
Authorization: Bearer eyJ...
```

---

## 2. Protocol Reference

### CRM Endpoints — JSON-RPC 2.0

All `/api/crm/...` endpoints use **JSON-RPC 2.0** over HTTP POST.

**Request wrapper:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    /* your actual parameters go here */
  }
}
```

**Success response wrapper:**
```json
{
  "jsonrpc": "2.0",
  "id": null,
  "result": {
    "success": true,
    "data": { /* payload */ }
  }
}
```

**Error response wrapper:**
```json
{
  "jsonrpc": "2.0",
  "id": null,
  "result": {
    "success": false,
    "error": "Error message here"
  }
}
```

> ⚠️ **Important:** JSON-RPC always returns HTTP 200 — even for errors.  
> Always check `result.success` to determine if the call succeeded.

### POS Endpoints — REST

All `/api/pos_perfume/...` endpoints use **standard REST** (GET/POST/PUT) with JSON bodies.

**Success response:**
```json
{
  "success": true,
  "message": "OK",
  "data": { /* payload */ }
}
```

**Error response (HTTP 4xx/5xx):**
```json
{
  "success": false,
  "error": "Error message here"
}
```

---

## 3. Phase 1 — User Preferences API

Stores user UI preferences (theme, notifications, dashboard, language) in the **database** so they persist across devices and sessions. Previously this data was stored only in Zustand (lost on page refresh).

### 3.1 — Get Preferences

```
GET / POST  /api/crm/users/me/preferences
Protocol:   JSON-RPC
Auth:       Bearer token required
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": null,
  "result": {
    "success": true,
    "data": {
      "theme": [
        { "id": "theme-mode",       "type": "select",  "value": "dark-gold" },
        { "id": "neumorphic",       "type": "toggle",  "value": true },
        { "id": "glassmorphic",     "type": "toggle",  "value": true },
        { "id": "animations",       "type": "toggle",  "value": true },
        { "id": "sidebar-collapsed","type": "toggle",  "value": false },
        { "id": "border-radius",    "type": "slider",  "value": 12 }
      ],
      "notifications": [
        {
          "id": "new-ticket",
          "label": "common.settings.notifications.newTicket",
          "description": "common.settings.notifications.newTicketDesc",
          "sound": true,
          "popup": true,
          "badge": true
        },
        {
          "id": "new-message",
          "label": "common.settings.notifications.newMessage",
          "description": "common.settings.notifications.newMessageDesc",
          "sound": true,
          "popup": true,
          "badge": true
        },
        {
          "id": "ticket-update",
          "label": "common.settings.notifications.ticketUpdate",
          "description": "common.settings.notifications.ticketUpdateDesc",
          "sound": false,
          "popup": true,
          "badge": true
        },
        {
          "id": "sla-breach",
          "label": "common.settings.notifications.slaBreach",
          "description": "common.settings.notifications.slaBreachDesc",
          "sound": true,
          "popup": true,
          "badge": true
        },
        {
          "id": "new-call",
          "label": "common.settings.notifications.newCall",
          "description": "common.settings.notifications.newCallDesc",
          "sound": true,
          "popup": true,
          "badge": false
        },
        {
          "id": "mention",
          "label": "common.settings.notifications.mention",
          "description": "common.settings.notifications.mentionDesc",
          "sound": true,
          "popup": true,
          "badge": true
        }
      ],
      "dashboard": [
        { "id": "active-tickets",   "visible": true,  "order": 1, "size": "md" },
        { "id": "team-performance", "visible": true,  "order": 2, "size": "lg" },
        { "id": "sla-status",       "visible": true,  "order": 3, "size": "sm" },
        { "id": "recent-activity",  "visible": true,  "order": 4, "size": "md" },
        { "id": "top-agents",       "visible": false, "order": 5, "size": "md" },
        { "id": "channel-stats",    "visible": true,  "order": 6, "size": "sm" }
      ],
      "language": [
        { "id": "language",    "value": "ar" },
        { "id": "direction",   "value": "rtl" },
        { "id": "date-format", "value": "dd/MM/yyyy" },
        { "id": "time-format", "value": "24h" }
      ]
    }
  }
}
```

> ℹ️ If the user has no saved preferences, defaults are returned automatically.  
> A new record is created in the database on the first call.

---

### 3.2 — Update Preferences

```
POST  /api/crm/users/me/preferences/update
Protocol:   JSON-RPC
Auth:       Bearer token required
```

All four sections are **optional** — only sections included in the request are updated. You can update just `theme` without touching `notifications`.

**Request (update theme only):**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "theme": [
      { "id": "theme-mode",       "type": "select", "value": "light" },
      { "id": "neumorphic",       "type": "toggle", "value": false },
      { "id": "glassmorphic",     "type": "toggle", "value": true },
      { "id": "animations",       "type": "toggle", "value": true },
      { "id": "sidebar-collapsed","type": "toggle", "value": false },
      { "id": "border-radius",    "type": "slider", "value": 8 }
    ]
  }
}
```

**Request (update all sections):**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "theme":         [ /* ThemeSetting[] */ ],
    "notifications": [ /* NotificationSetting[] */ ],
    "dashboard":     [ /* DashboardWidget[] */ ],
    "language":      [ /* LanguageSetting[] */ ]
  }
}
```

**Response:** Same shape as GET — returns full updated preferences snapshot.

---

### 3.3 — Integration Pattern (Recommended)

**On Login — Hydrate the store:**
```typescript
// In your auth hook or login action
const loginUser = async (credentials) => {
  const authResponse = await login(credentials);
  
  // After successful login, load preferences from backend
  const prefsResponse = await fetchUserPreferences();
  if (prefsResponse.success) {
    useSettingsStore.getState().hydrateFromBackend(prefsResponse.data);
  }
};
```

**On Settings Change — Save to backend:**
```typescript
// In your settings update handler
const updateTheme = async (newTheme: ThemeSetting[]) => {
  // Update local store immediately (optimistic)
  useSettingsStore.getState().setTheme(newTheme);
  
  // Persist to backend
  await updatePreferences({ theme: newTheme });
};
```

---

## 4. Phase 2 — KPI Rules CRUD

KPI rules define performance targets for agents. Used on supervisor dashboards and scorecards.

**Available metrics:**

| Key | Description |
|-----|-------------|
| `total_calls` | Total calls made |
| `answered_calls` | Calls answered (picked up) |
| `total_messages` | Total messages sent/received |
| `answered_messages` | Messages responded to |
| `conversions` | Interactions converted to sale orders |
| `avg_frt_seconds` | Average First Response Time in seconds |
| `avg_ttr_seconds` | Average Time To Resolution in seconds |
| `late_messages` | Count of messages that breached SLA |
| `late_calls` | Count of calls that were not answered in time |

**Available operators:** `>=`, `<=`, `=`, `>`, `<`

---

### 4.1 — List KPI Rules

```
POST  /api/crm/config/kpi_rules/list
Protocol:   JSON-RPC
Auth:       Bearer token required
Role:       Any authenticated user
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "is_active": true,
    "metric": "total_calls",
    "branch_id": 2
  }
}
```

> All params are optional — omit to fetch all rules.

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 1,
      "items": [
        {
          "id": 1,
          "name": "Minimum Daily Calls",
          "description": "Each agent must make at least 20 calls per day",
          "metric": "total_calls",
          "operator": ">=",
          "threshold": 20.0,
          "period_days": 1,
          "priority": 10,
          "is_active": true,
          "branch_id": 2,
          "branch_name": "Riyadh Branch"
        }
      ]
    }
  }
}
```

---

### 4.2 — Create KPI Rule

```
POST  /api/crm/config/kpi_rules/create
Protocol:   JSON-RPC
Auth:       Bearer token required
Role:       Supervisor or above
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "name": "Response Time Target",
    "metric": "avg_frt_seconds",
    "operator": "<=",
    "threshold": 300,
    "period_days": 7,
    "priority": 5,
    "is_active": true,
    "description": "First response must be within 5 minutes (300 seconds)",
    "branch_id": null
  }
}
```

**Required params:** `name`, `metric`  
**Optional params:** `operator` (default `>=`), `threshold` (default `0`), `period_days` (default `30`), `priority` (default `10`), `is_active` (default `true`), `description`, `branch_id`

**Response:** Returns the created rule object (same shape as list item).

---

### 4.3 — Update KPI Rule

```
POST  /api/crm/config/kpi_rules/<id>/update
Protocol:   JSON-RPC
Auth:       Bearer token required
Role:       Supervisor or above
```

**Request (partial update — only changed fields):**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "threshold": 25.0,
    "is_active": false
  }
}
```

**Response:** Returns the full updated rule object.

---

### 4.4 — Delete KPI Rule

```
POST  /api/crm/config/kpi_rules/<id>/delete
Protocol:   JSON-RPC
Auth:       Bearer token required
Role:       Supervisor or above
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {}
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": { "id": 1, "deleted": true }
  }
}
```

---

## 5. Phase 3 — Single Shift Endpoint

### 5.1 — Get Single Shift

```
POST  /api/crm/shifts/<id>
Protocol:   JSON-RPC
Auth:       Bearer token required
Role:       Any authenticated user
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {}
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "id": 3,
      "name": "Morning Shift",
      "name_ar": "الوردية الصباحية",
      "branch_id": 2,
      "branch_name": "Riyadh Branch",
      "shift_type": "morning",
      "start_time": 8.0,
      "end_time": 17.0,
      "is_active": true,
      "is_deleted": false,
      "assigned_users": [
        { "id": 5, "name": "Ahmed Ali",   "login": "ahmed@company.com" },
        { "id": 8, "name": "Sara Hassan", "login": "sara@company.com" }
      ]
    }
  }
}
```

> `start_time` and `end_time` are **float hours** (e.g. `8.5` = 8:30 AM, `17.0` = 5:00 PM).

---

## 6. Phase 4 — POS Settings Expansion

### 6.1 — Get All POS Settings

```
GET   /api/pos_perfume/v1/settings
Protocol:   REST
Auth:       Bearer token required
```

**Response:**
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "exchange_rate": 1470.0,
    "default_pricelist_id": 3,
    "default_warehouse_id": 2,
    "invoice_types": [
      { "key": "1", "label": "زبون محل" },
      { "key": "2", "label": "شركات توصيل" },
      { "key": "3", "label": "نقليات" },
      { "key": "4", "label": "ديلفري" },
      { "key": "5", "label": "NBS" },
      { "key": "6", "label": "شورجة" },
      { "key": "7", "label": "NA" },
      { "key": "8", "label": "مكاتب الشورجة" }
    ]
  }
}
```

> `default_pricelist_id = 0` means no default is set (auto-resolved at runtime).  
> `default_warehouse_id = 0` means no default is set (all warehouses used).

---

### 6.2 — Update POS Settings

```
PUT   /api/pos_perfume/v1/settings
Protocol:   REST
Auth:       Bearer token required
Content-Type: application/json
```

All fields are optional — include only what you want to change.

**Request:**
```json
{
  "exchange_rate": 1500.0,
  "default_pricelist_id": 3,
  "default_warehouse_id": 2,
  "invoice_types": [
    { "key": "1", "label": "زبون محل" },
    { "key": "2", "label": "شركات توصيل" }
  ]
}
```

**Response:** Returns the full updated settings snapshot (same shape as GET).

---

### 6.3 — List Invoice Types

```
GET   /api/pos_perfume/v1/settings/invoice_types
Protocol:   REST
Auth:       Bearer token required
```

**Response:**
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "total": 8,
    "items": [
      { "key": "1", "label": "زبون محل" },
      { "key": "2", "label": "شركات توصيل" },
      { "key": "3", "label": "نقليات" },
      { "key": "4", "label": "ديلفري" },
      { "key": "5", "label": "NBS" },
      { "key": "6", "label": "شورجة" },
      { "key": "7", "label": "NA" },
      { "key": "8", "label": "مكاتب الشورجة" }
    ]
  }
}
```

---

### 6.4 — Update Invoice Types

```
POST  /api/pos_perfume/v1/settings/invoice_types/update
Protocol:   REST
Auth:       Bearer token required
Content-Type: application/json
```

This **replaces the entire list**. Send the complete desired list.

**Request:**
```json
{
  "invoice_types": [
    { "key": "1", "label": "زبون محل" },
    { "key": "2", "label": "شركات توصيل" },
    { "key": "3", "label": "نقليات" },
    { "key": "9", "label": "طلب جديد" }
  ]
}
```

**Validation rules:**
- `invoice_types` must be a list
- Each item must be an object with `key` (non-empty string) and `label` (non-empty string)
- `key` values should be unique within the list

**Response:**
```json
{
  "success": true,
  "message": "Invoice types updated",
  "data": {
    "total": 4,
    "items": [ /* saved list */ ]
  }
}
```

---

## 7. Phase 5 — System Admin API

> ⚠️ **Access restricted** — requires `base.group_system` (Technical Admin) or `group_lugal_crm_general_manager`.  
> Supervisors and agents will receive a **403 Forbidden** response.

### 7.1 — Get System Parameters

```
GET / POST  /api/crm/admin/system
Protocol:   JSON-RPC
Auth:       Bearer token required
Role:       Admin or General Manager only
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {}
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "jwt_access_ttl_hours": "24",
      "jwt_refresh_ttl_days": "7",
      "rate_limit_max_attempts": "10",
      "rate_limit_window_minutes": "15",
      "pos_exchange_rate": "1470.0",
      "pos_default_pricelist_id": "3",
      "pos_default_warehouse_id": "2"
    }
  }
}
```

> All values are returned as **strings** (as stored in `ir.config_parameter`). Parse them as needed.

---

### 7.2 — Update System Parameters

```
POST  /api/crm/admin/system/update
Protocol:   JSON-RPC
Auth:       Bearer token required
Role:       Admin or General Manager only
```

Pass the **friendly name** (key from the GET response) and the new value as a string.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "jwt_access_ttl_hours": "48",
    "rate_limit_max_attempts": "5"
  }
}
```

**Response:** Returns the full updated system params snapshot.

> ✅ Only safe parameters listed in the response can be updated. Unknown keys are silently ignored.

---

### 7.3 — Get SAP Integration Status

```
GET / POST  /api/crm/admin/integrations/sap
Protocol:   JSON-RPC
Auth:       Bearer token required
Role:       Admin or General Manager only
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "id": 1,
      "name": "SAP B1 Production",
      "base_url": "https://sap.company.com:50000",
      "username": "manager",
      "has_password": true,
      "company_db": "NBS",
      "active": true,
      "connection_status": "connected",
      "last_status_check": "2026-03-30T10:00:00"
    }
  }
}
```

**`connection_status` values:**
| Value | Meaning |
|-------|---------|
| `connected` | Last test was successful |
| `error` | Last test failed |
| `not_tested` | Never been tested |

> 🔒 The actual SAP **password is never returned** — only `has_password: true/false`.

---

### 7.4 — Test SAP Connection

```
POST  /api/crm/admin/integrations/sap/test
Protocol:   JSON-RPC
Auth:       Bearer token required
Role:       Admin or General Manager only
```

Triggers a **live connection test** to SAP Service Layer. This actually attempts to authenticate with SAP — use with care in production.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {}
}
```

**Response (success):**
```json
{
  "result": {
    "success": true,
    "data": {
      "ok": true,
      "connection_status": "connected",
      "message": "Connection successful"
    }
  }
}
```

**Response (failure):**
```json
{
  "result": {
    "success": true,
    "data": {
      "ok": false,
      "connection_status": "error",
      "message": "Connection refused: Unable to reach SAP at https://sap.company.com:50000"
    }
  }
}
```

> Note: `success: true` at the outer level means the API call itself succeeded. Check `data.ok` for the actual SAP connection result.

---

## 8. TypeScript Type Definitions

Add these types to your project (e.g. `src/types/settings.ts`):

```typescript
// ── User Preferences ──────────────────────────────────────────────────────

export interface ThemeSetting {
  id: string;
  type: 'select' | 'toggle' | 'slider';
  value: string | boolean | number;
}

export interface NotificationSetting {
  id: string;
  label: string;
  description: string;
  sound: boolean;
  popup: boolean;
  badge: boolean;
}

export interface DashboardWidget {
  id: string;
  visible: boolean;
  order: number;
  size: 'sm' | 'md' | 'lg' | 'xl';
}

export interface LanguageSetting {
  id: string;
  value: string;
}

export interface UserPreferences {
  theme:         ThemeSetting[];
  notifications: NotificationSetting[];
  dashboard:     DashboardWidget[];
  language:      LanguageSetting[];
}

// ── KPI Rules ─────────────────────────────────────────────────────────────

export type KpiMetric =
  | 'total_calls'
  | 'answered_calls'
  | 'total_messages'
  | 'answered_messages'
  | 'conversions'
  | 'avg_frt_seconds'
  | 'avg_ttr_seconds'
  | 'late_messages'
  | 'late_calls';

export type KpiOperator = '>=' | '<=' | '=' | '>' | '<';

export interface KpiRule {
  id:          number;
  name:        string;
  description: string;
  metric:      KpiMetric;
  operator:    KpiOperator;
  threshold:   number;
  period_days: number;
  priority:    number;
  is_active:   boolean;
  branch_id:   number | null;
  branch_name: string;
}

// ── Shifts ────────────────────────────────────────────────────────────────

export interface ShiftUser {
  id:    number;
  name:  string;
  login: string;
}

export interface Shift {
  id:             number;
  name:           string;
  name_ar:        string;
  branch_id:      number | null;
  branch_name:    string;
  shift_type:     'morning' | 'evening' | 'night' | 'flexible';
  start_time:     number; // float hours: 8.0 = 08:00, 8.5 = 08:30
  end_time:       number;
  is_active:      boolean;
  is_deleted:     boolean;
  assigned_users: ShiftUser[];
}

// ── POS Settings ──────────────────────────────────────────────────────────

export interface InvoiceType {
  key:   string;
  label: string;
}

export interface PosSettings {
  exchange_rate:        number;
  default_pricelist_id: number;
  default_warehouse_id: number;
  invoice_types:        InvoiceType[];
}

// ── System Admin ──────────────────────────────────────────────────────────

export interface SystemParams {
  jwt_access_ttl_hours:      string;
  jwt_refresh_ttl_days:      string;
  rate_limit_max_attempts:   string;
  rate_limit_window_minutes: string;
  pos_exchange_rate:         string;
  pos_default_pricelist_id:  string;
  pos_default_warehouse_id:  string;
}

export type SapConnectionStatus = 'connected' | 'error' | 'not_tested';

export interface SapIntegrationStatus {
  id:                number;
  name:              string;
  base_url:          string;
  username:          string;
  has_password:      boolean;
  company_db:        string;
  active:            boolean;
  connection_status: SapConnectionStatus;
  last_status_check: string | null;
}
```

---

## 9. Full Example — Hydrate Settings on Login

```typescript
// src/api/settings.ts

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

function jsonRpcCall<T>(endpoint: string, params: Record<string, unknown> = {}, token: string): Promise<T> {
  return fetch(`${BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params }),
  })
    .then(r => r.json())
    .then(r => {
      if (!r.result?.success) throw new Error(r.result?.error ?? 'Unknown error');
      return r.result.data as T;
    });
}

export const settingsApi = {
  getPreferences: (token: string) =>
    jsonRpcCall<UserPreferences>('/api/crm/users/me/preferences', {}, token),

  updatePreferences: (token: string, patch: Partial<UserPreferences>) =>
    jsonRpcCall<UserPreferences>('/api/crm/users/me/preferences/update', patch, token),

  listKpiRules: (token: string, filters?: { is_active?: boolean; metric?: KpiMetric }) =>
    jsonRpcCall<{ items: KpiRule[]; total: number }>('/api/crm/config/kpi_rules/list', filters ?? {}, token),

  createKpiRule: (token: string, rule: Omit<KpiRule, 'id' | 'branch_name'>) =>
    jsonRpcCall<KpiRule>('/api/crm/config/kpi_rules/create', rule, token),

  updateKpiRule: (token: string, id: number, patch: Partial<KpiRule>) =>
    jsonRpcCall<KpiRule>(`/api/crm/config/kpi_rules/${id}/update`, patch, token),

  deleteKpiRule: (token: string, id: number) =>
    jsonRpcCall<{ id: number; deleted: boolean }>(`/api/crm/config/kpi_rules/${id}/delete`, {}, token),

  getShift: (token: string, id: number) =>
    jsonRpcCall<Shift>(`/api/crm/shifts/${id}`, {}, token),
};

// POS Settings use REST (not JSON-RPC)
export const posSettingsApi = {
  getSettings: async (token: string): Promise<PosSettings> => {
    const r = await fetch(`${BASE_URL}/api/pos_perfume/v1/settings`, {
      headers: { 'Authorization': `Bearer ${token}` },
    }).then(r => r.json());
    if (!r.success) throw new Error(r.error);
    return r.data;
  },

  updateSettings: async (token: string, patch: Partial<PosSettings>): Promise<PosSettings> => {
    const r = await fetch(`${BASE_URL}/api/pos_perfume/v1/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(patch),
    }).then(r => r.json());
    if (!r.success) throw new Error(r.error);
    return r.data;
  },

  getInvoiceTypes: async (token: string): Promise<InvoiceType[]> => {
    const r = await fetch(`${BASE_URL}/api/pos_perfume/v1/settings/invoice_types`, {
      headers: { 'Authorization': `Bearer ${token}` },
    }).then(r => r.json());
    if (!r.success) throw new Error(r.error);
    return r.data.items;
  },

  updateInvoiceTypes: async (token: string, invoice_types: InvoiceType[]): Promise<InvoiceType[]> => {
    const r = await fetch(`${BASE_URL}/api/pos_perfume/v1/settings/invoice_types/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ invoice_types }),
    }).then(r => r.json());
    if (!r.success) throw new Error(r.error);
    return r.data.items;
  },
};
```

---

## 10. Error Handling Reference

### Common Error Codes

| Scenario | `success` | `error` message | Action |
|----------|-----------|-----------------|--------|
| Missing / expired token | `false` | `"Unauthorized"` | Redirect to login |
| Insufficient role | `false` | `"Admin role required"` | Show access denied |
| Record not found | `false` | `"KPI rule not found"` | Show 404 state |
| Validation error | `false` | `"name is required"` | Show field error |
| Server crash | `false` | `"Internal Server Error"` | Show generic error |

### Recommended Pattern

```typescript
async function safeApiCall<T>(call: () => Promise<T>): Promise<[T | null, string | null]> {
  try {
    const data = await call();
    return [data, null];
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    if (message === 'Unauthorized') {
      // Clear token, redirect to login
      useAuthStore.getState().logout();
    }
    return [null, message];
  }
}

// Usage:
const [preferences, error] = await safeApiCall(() =>
  settingsApi.getPreferences(token)
);
if (error) {
  showToast({ type: 'error', message: error });
  return;
}
// use preferences...
```

---

*For questions or issues with these APIs, contact the backend team or open an issue in the project repository.*
