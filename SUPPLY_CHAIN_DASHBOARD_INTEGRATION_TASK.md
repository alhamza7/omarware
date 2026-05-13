# Supply Chain Dashboard — Frontend Integration Task

**Document type:** Implementation task for frontend developers  
**Feature:** Integrate the backend **Supply Chain dashboard summary** API into the product dashboard / Supply Chain home experience.  
**Primary API:** `POST /api/crm/supply/dashboard/summary`  
**Related backend reference:** `SUPPLY_CHAIN_DASHBOARD_SUMMARY_RESPONSE.md` (response structure and calculation details)

---

## 1. Objective

Consume **`POST /api/crm/supply/dashboard/summary`** after the user is authenticated (same JWT / session pattern as existing Supply Chain calls), render **KPI cards** (and optional small charts) from `result.data`, and handle **loading**, **error**, and **refresh** states in line with the rest of the Supply Chain UI.

---

## 2. API contract

### 2.1 Endpoint

| Property | Value |
|-----------|--------|
| **URL** | `/api/crm/supply/dashboard/summary` |
| **Method** | `POST` |
| **Transport** | Odoo **JSON-RPC 2.0** (same as existing `rpc(...)` helpers in `frontends/44/src/services/supplyApi.ts`) |
| **Auth** | `Authorization: Bearer <token>` **or** valid Odoo session cookie — backend uses `ensure_jwt_user_id()` |

### 2.2 Request body

No required fields for aggregation. Sending `{}` is valid. Reuse the same JSON-RPC envelope and `params` shape as other supply endpoints.

### 2.3 Success response (`result`)

```json
{
  "success": true,
  "data": {
    "item_requests": {
      "draft": 0,
      "in_progress": 0,
      "completed": 0
    },
    "negotiations": {
      "ongoing": 0,
      "finalized": 0,
      "cancelled": 0
    },
    "purchase_orders": {
      "draft": 0,
      "confirmed": 0,
      "cancelled": 0,
      "delayed_receipt": 0
    },
    "payments": {
      "total": 0
    },
    "shipments": {
      "total": 0
    },
    "approvals": {
      "pending": 0
    },
    "config_flags": {
      "workflow_level_count": 0,
      "budget_control_enabled": false,
      "stock_validate_po": true,
      "workflow_activity_notify": true
    }
  }
}
```

All count fields are **non-negative integers**. `config_flags` values are **integer** (`workflow_level_count`) or **boolean** (others).

### 2.4 Error response (`result`)

| Condition | Typical `result` |
|-----------|------------------|
| Not authenticated | `{ "success": false, "error": "Unauthorized", "data": null }` |
| Server / unexpected error | `{ "success": false, "error": "<message>", "data": null }` (shape aligned with `crm_error`) |

Treat any `success !== true` or missing `data` as failure for UI purposes.

---

## 3. API integration (engineering checklist)

1. **Add a typed client** (e.g. in `frontends/44/src/services/supplyApi.ts`):
   - `dashboardSummary()` → `POST /api/crm/supply/dashboard/summary` with `{}`.
   - Export from the default `supplyApi` object if the app uses the bundle pattern.
2. **Add TypeScript types** (e.g. in `frontends/44/src/types/supply.ts`):
   - `SupplyDashboardSummary` mirroring `data` above (nested objects, strict literals for known keys).
3. **Wire authentication:**
   - Reuse the same `rpc` / base URL / `Authorization` header as `negotiationList`, `poList`, etc.
4. **Call site:**
   - Supply Chain **dashboard / home** tab (or first screen of the Supply section): fetch on mount and optionally on **pull-to-refresh** / **manual refresh** / **focus return** (product decision).
5. **Do not block the whole app** on summary failure; show the dashboard shell with an inline error for the summary region only unless product specifies otherwise.

---

## 4. Dashboard cards mapping

Map each **`data`** section to one or more UI cards. Suggested layout (adjust to design system).

### 4.1 Item requests pipeline

| Card / section | Data path | Label idea | Notes |
|----------------|-----------|--------------|--------|
| Draft | `data.item_requests.draft` | “Item requests — Draft” | Pipeline stage |
| In progress | `data.item_requests.in_progress` | “Item requests — In progress” | |
| Completed | `data.item_requests.completed` | “Item requests — Completed” | |

**Optional:** Single **stacked bar** or three **donut segments** if design wants one widget (derive segments from the three counts).

### 4.2 Negotiations

| Card / section | Data path | Label idea | Notes |
|----------------|-----------|--------------|--------|
| Ongoing | `data.negotiations.ongoing` | “Negotiations — Ongoing” | Primary workload |
| Finalized | `data.negotiations.finalized` | “Negotiations — Finalized” | |
| Cancelled | `data.negotiations.cancelled` | “Negotiations — Cancelled” | |

### 4.3 Purchase orders

| Card / section | Data path | Label idea | Notes |
|----------------|-----------|--------------|--------|
| Draft | `data.purchase_orders.draft` | “POs — Draft” | |
| Confirmed | `data.purchase_orders.confirmed` | “POs — Confirmed” | |
| Cancelled | `data.purchase_orders.cancelled` | “POs — Cancelled” | |
| Delayed receipt | `data.purchase_orders.delayed_receipt` | “POs — Delayed receipt” | **Alert-style** if &gt; 0 (badge / accent color). Not a `search_count`; explain in tooltip: confirmed POs with positive delay metric. |

### 4.4 Payments

| Card / section | Data path | Label idea | Notes |
|----------------|-----------|--------------|--------|
| Payment records | `data.payments.total` | “Payment records” | Count of `lugal.supply.payment` rows (active), **not** currency total. Tooltip: “Number of payment entries” to avoid confusion with amount. |

### 4.5 Shipments / containers

| Card / section | Data path | Label idea | Notes |
|----------------|-----------|--------------|--------|
| Active containers | `data.shipments.total` | “Containers / shipments” | Backend counts `lugal.supply.container` (non-deleted, active). Align label with existing “Containers” vs “Shipments” wording in the app. |

### 4.6 Approvals

| Card / section | Data path | Label idea | Notes |
|----------------|-----------|--------------|--------|
| Pending approvals | `data.approvals.pending` | “Pending approvals” | Workflow lines with `state === 'pending'`. Good for **CTA** (“Review”) linking to first relevant screen if product defines it. |

### 4.7 Configuration flags (secondary row)

| UI element | Data path | Use |
|------------|-----------|-----|
| Settings / badges | `data.config_flags.workflow_level_count` | Show “N approval levels” in settings preview or admin strip |
| Toggles (read-only) | `data.config_flags.budget_control_enabled` | “Budget control on” chip |
| | `data.config_flags.stock_validate_po` | “Stock validation on” chip |
| | `data.config_flags.workflow_activity_notify` | “Workflow activities on” chip |

**Recommendation:** Render `config_flags` as a **compact “System configuration”** strip or footnote, not primary KPI tiles, unless the audience is admins only.

---

## 5. Loading, error, and empty states

### 5.1 Loading

- On initial fetch: show **skeleton placeholders** for the KPI grid **or** a single section-level spinner (match existing Supply pages).
- Disable or dim **“Refresh”** while loading to avoid duplicate requests (debounce if needed).

### 5.2 Error

- If `success === false` or network failure:
  - Show **non-blocking** inline alert in the dashboard summary region with `error` message when present.
  - Provide **Retry** that re-calls `dashboard/summary`.
- Map `Unauthorized` to existing **login / token refresh** flow (same as `negotiationList` / `poList`).

### 5.3 Empty / all zeros

- All counts `=== 0` is **valid**, not an error. Still render cards with **“0”** (or “—” per design).
- Do **not** hide the section unless product explicitly wants a minimal empty state message (e.g. “No supply activity yet”).

### 5.4 Stale data

- If user performs actions elsewhere (create PO, finalize negotiation), summary may be stale until refetch. Optional: refetch summary when navigating back to the dashboard tab or after known mutations (product scope).

---

## 6. Non-functional expectations

- **Performance:** One request per dashboard visit (or refresh); avoid polling unless product requires it (interval + visibility API).
- **Consistency:** Numbers are **eventually consistent** with list screens (same domains as backend; small timing differences possible).
- **Security:** Never log full JWT; errors may be logged per app policy.
- **Accessibility:** Card values should be exposed with clear headings; alert region for errors should be announced where applicable.

---

## 7. Acceptance criteria

Use this as the **Definition of Done** for the task.

- [ ] **`supplyApi` (or equivalent)** exposes a function that calls `POST /api/crm/supply/dashboard/summary` with the same JSON-RPC wiring as other supply APIs.
- [ ] **TypeScript types** exist for the full `data` tree; no `any` for the summary payload in new code paths.
- [ ] **Authenticated users** see the summary load successfully when the backend returns `success: true`.
- [ ] **KPI cards** (or agreed chart widgets) display all keys under `data.item_requests`, `data.negotiations`, `data.purchase_orders`, `data.payments`, `data.shipments`, and `data.approvals` with correct labels.
- [ ] **`delayed_receipt`** is visually distinct when `> 0` (badge, color, or icon) per design.
- [ ] **`config_flags`** are shown in the agreed secondary UI (or explicitly deferred with sign-off).
- [ ] **Loading state** is visible during the request; no blank flash that looks like “0” before data arrives (unless skeleton shows zeros clearly).
- [ ] **Error state** shows a readable message and **Retry**; **Unauthorized** follows existing auth UX.
- [ ] **Manual refresh** (if in scope) re-fetches summary without a full page reload.
- [ ] **No regression** to existing Supply tabs (PO, containers, negotiations) routing and auth.
- [ ] **Documentation:** Link to this task and/or `SUPPLY_CHAIN_DASHBOARD_SUMMARY_RESPONSE.md` from the FE README or internal wiki if the team maintains one.

---

## 8. Final report section *(to be completed by implementer)*

*Copy this block into the merge request description or fill it in before closing the task.*

### 8.1 Summary

- **Implemented by:**  
- **Date completed:**  
- **Branch / PR:**  

### 8.2 What was shipped

- **Screens / routes touched:**  
- **New API client method name:**  
- **UI components added or updated:**  

### 8.3 Verification

- [ ] Tested with a user that has **non-zero** counts in at least one category (staging data).  
- [ ] Tested **all zeros** dashboard.  
- [ ] Tested **401 / Unauthorized** (expired token).  
- [ ] Tested **500 / network error** and Retry.  

### 8.4 Screenshots / recordings

- Attach dashboard with loaded KPIs.  
- Attach error + Retry state (optional).  

### 8.5 Follow-ups (if any)

- Items deferred (e.g. charts, refetch-on-mutation, i18n):  

---

## 9. References

| Document | Purpose |
|----------|---------|
| `SUPPLY_CHAIN_DASHBOARD_SUMMARY_RESPONSE.md` | Backend field-by-field behavior and code reference |
| `SUPPLY_CHAIN_DASHBOARD_APIS_AUDIT.md` | Wider `/api/crm/supply/*` audit and unused API ideas |
| `addons/lugal_crm/controllers/supply_chain_api_controller.py` | Source of `supply_dashboard_summary` |

---

*End of task document.*
