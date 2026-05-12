# Frontend Supply Chain API Audit — Task Brief

This document defines a structured audit for all Supply Chain user-facing surfaces. Treat **`docs/addons/lugal_crm/SUPPLY_CHAIN_FE_INTEGRATION_GUIDE.md`** as the **single source of truth** for which backend routes exist, their transport type (JSON-RPC vs multipart vs HTTP GET/DELETE), and expected request shapes.

---

## Objective

Ensure every Supply Chain screen and action in the frontend is **aligned with real backend APIs**: correct routes, correct payloads, real data instead of mocks, and no non-functional controls. Where the backend already exposes an endpoint, the UI should use it. Where it does not, the gap should be **documented separately** for backend prioritization (no silent failures or fake success).

---

## Scope

- **In scope:** All UI modules, routes, tabs, modals, and actions labeled or understood as **Supply Chain** (vendors/suppliers, POs, shipments/containers, workflow, payments, chat, stories, etc.) across every frontend that ships this product (e.g. `frontends/44`, NBS CRM supply-chain bundle under `addons/lugal_crm/NBS CRM (16)/`, and any other client calling `/api/crm/supply/*`).
- **Out of scope:** Unrelated CRM areas; non-supply REST endpoints (e.g. product search / REST PO create) except where the integration guide explicitly cross-references them.
- **Authority:** Endpoint list, methods, and parameters — **`docs/addons/lugal_crm/SUPPLY_CHAIN_FE_INTEGRATION_GUIDE.md`** only. If code and guide disagree, **flag the discrepancy** and verify against `addons/lugal_crm/controllers/supply_*.py`.

---

## Rules

1. **No guessing URLs.** Every call must match a path and transport type documented in the integration guide (including **multipart** and **GET** where applicable).
2. **JSON-RPC:** Use the standard envelope; pass route parameters inside **`params`**; read **`result.success`**, **`result.data`**, **`result.error`**.
3. **Auth:** Supply calls use **`Authorization: Bearer <token>`** unless the guide states otherwise.
4. **Stubs:** If the guide marks an endpoint as a **stub** (e.g. some comment routes), document current behavior and do not pretend full functionality exists.
5. **Mocks / hardcoded data:** Any screen still driven by static arrays, demo IDs, or copy-pasted JSON must be listed and replaced or clearly gated as “demo only” with product approval.
6. **Dead UI:** Buttons or menu items that do nothing, throw uncaught errors, or always fail must be fixed (wire-up or remove/disable with explanation).
7. **Reporting:** Use the report template at **`frontend/SUPPLY_CHAIN_API_AUDIT_REPORT_TEMPLATE.md`** to record findings per feature.

---

## Features to audit

For **each** feature below, walk through **every** screen, sub-tab, modal, and primary/secondary action. Map each action to **one** integration-guide endpoint (or mark “none”).

| Feature | Focus |
|---------|--------|
| **Suppliers** | List/get/create/update/delete; alias **`/suppliers/*`** vs **`/vendors/*`**; field mapping (`contact_person`, `country`, etc.). |
| **Purchase Orders** | List, suggested, CRUD, status transitions, lines, attachments upload/link, packing list share/PDF, e-sign, comment stubs. |
| **Packing List** | Share and PDF actions vs **`/po/<id>/packing-list/share`** and **`/packing-list/pdf`**. |
| **Containers** | Legacy **`/containers/*`** vs workflow; mark arrived, clearance, driver, reminder (JSON + HTTP GET/DELETE), attachments, penalties, tracking GET/POST, comment stubs. |
| **Shipments** | **`/shipments/*`** list/get/create/update/delete, **`link_orders`**. |
| **Payments** | List/get/create/update/delete, **`payments/po/list`** for pickers, attachments link. |
| **Negotiations** | Full CRUD, confirm/e-sign, offers, comments, attachments link. |
| **Item Requests** | List/get/create/update/delete, status, requester confirm, attachments link. |
| **Notifications** | List, create (if used), mark read, mark all read, delete. |
| **Inventory Min/Max** | List, update/upsert, delete. |
| **Clearance Companies** | Full CRUD. |
| **Chat** | Conversations, messages (list/create/edit/pin/react/receipts/forward/search/delete), **`/chat/upload`**, **`/chat/bus_channels`**. |
| **Stories** | Feed, create, view, viewers, delete, **`/stories/upload`**. |

Also verify **dashboard summary** if a dashboard tile exists (**`/dashboard/summary`**).

---

## Expected fixes

| Finding | Expected action |
|---------|------------------|
| Wrong path or HTTP method | Update client to match the integration guide. |
| JSON-RPC body not in `params` | Fix envelope; retest. |
| Multipart call sent as JSON-RPC | Switch to `multipart/form-data` and correct field names (`file` / `files[]`). |
| Backend exists, UI missing | Implement call + loading/error/empty states + list refresh. |
| Backend missing or stub only | Do **not** fake data; file under **Missing Backend APIs** in the report template. |
| Dead button | Wire to API, or remove/disable with tooltip or doc note. |
| Mock/hardcoded data | Replace with API-driven state or document as demo-only. |

---

## Deliverables

1. **Completed audit** using **`frontend/SUPPLY_CHAIN_API_AUDIT_REPORT_TEMPLATE.md`** (one filled copy per repo or per app, as agreed with PM).
2. **PR(s)** integrating missing calls where the guide documents a live endpoint.
3. **Issue list** (tickets or markdown) for **missing backend APIs**, **stub-only** behavior that blocks UX, and **guide vs code** mismatches.
4. Short **summary note** (for release notes): what was integrated, what remains backend-dependent, and any breaking URL changes.

---

## Acceptance Criteria

- [ ] Every scoped Supply Chain screen has a **traceability row**: UI action → guide endpoint (or “N/A — documented gap”).
- [ ] No production-critical action relies on **undocumented** or **incorrect** URLs.
- [ ] **Multipart** and **GET/DELETE** routes are implemented per the guide (not all are JSON-RPC POST).
- [ ] **Suppliers**, **Purchase Orders** (including **Packing List**), **Containers**, **Shipments**, **Payments**, **Negotiations**, **Item Requests**, **Notifications**, **Min/Max**, **Clearance Companies**, **Chat**, and **Stories** have been reviewed per the table above.
- [ ] Dead controls are either **fixed** or **removed/disabled** with clear UX.
- [ ] Mock/hardcoded data is **eliminated** or **explicitly labeled** and approved.
- [ ] Report template sections are filled: **Fully Integrated**, **Missing Integrations Fixed**, **Missing Backend APIs**, **Dead UI Removed**, **Wrong API Fixed**, **Pending Manual Review**.
- [ ] Final review against **`docs/addons/lugal_crm/SUPPLY_CHAIN_FE_INTEGRATION_GUIDE.md`** revision used (commit hash or date noted in the report).
