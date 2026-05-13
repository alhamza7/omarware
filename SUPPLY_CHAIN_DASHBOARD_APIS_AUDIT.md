# Supply Chain Dashboard — Backend API Audit

Inventory of **`/api/crm/supply/*`** routes used for Supply Chain **dashboards, KPIs, lists, notifications, logistics, POs, payments, negotiations, chat, and stories**. Includes **HTTP vs JSON-RPC**, **params**, **response shape**, and **in-repo frontend** usage (`frontends/44`, `addons/lugal_crm/NBS CRM (16)`).

**Audit date:** 2026-05-12  
**Controllers:** `supply_chain_api_controller.py`, `supply_controller.py`, `supply_extra_api_controller.py`, `supply_chat_controller.py`, `supply_stories_controller.py`.

---

## Conventions

| Item | Detail |
|------|--------|
| **JSON-RPC** | `type='jsonrpc'` → Odoo JSON-RPC 2.0; `result` is usually `{ "success": bool, "error"?: str, "data"?: ... }`. |
| **Auth** | `auth='none'` + `ensure_jwt_user_id()` (Bearer JWT or session). |
| **HTTP** | Used for multipart uploads, GET tracking, CORS, some reminders. |

**FE columns:** **FE44** = match in `frontends/44/src/**`; **NBS16** = match in `addons/lugal_crm/NBS CRM (16)/src/**`. **No** = no string hit in this repo (external apps may still call).

---

## 1. Dedicated dashboard KPI API

| Route | Method | Transport | Purpose | Request params | Response `data` keys |
|-------|--------|-----------|---------|------------------|----------------------|
| `/api/crm/supply/dashboard/summary` | POST | JSON-RPC | Aggregate counts: item requests, negotiations, POs (incl. delayed receipt), payments total, container/shipment total, pending workflow approvals, `ir.config_parameter` flags. | None | `item_requests`, `negotiations`, `purchase_orders`, `payments`, `shipments`, `approvals`, `config_flags` |

| FE44 | NBS16 |
|------|-------|
| **No** | **No** |

**Recommendation:** Primary endpoint for **dashboard cards** without many list calls.

---

## 2. Vendors & supplier aliases

| Route | Method | Transport | Purpose | FE44 | NBS16 |
|-------|--------|-----------|---------|------|-------|
| `/api/crm/supply/vendors/list` | POST | JSON-RPC | Paginated vendors | Yes | Yes |
| `/api/crm/supply/vendors/<id>/get` | POST | JSON-RPC | Single vendor | Yes | Partial (`/vendors/${id}` without `/get` in NBS16) |
| `/api/crm/supply/vendors/create` | POST | JSON-RPC | Create | Yes | Yes |
| `/api/crm/supply/vendors/<id>/update` | POST | JSON-RPC | Update | Yes | Yes |
| `/api/crm/supply/vendors/<id>/delete` | POST | JSON-RPC | Soft-delete | Yes | No |
| `/api/crm/supply/suppliers/<id>/update` | POST | JSON-RPC | Alias (supplier-style kwargs) | No | No |
| `/api/crm/supply/suppliers/<id>/delete` | POST | JSON-RPC | Alias of vendor delete | No | No |

**List params:** `page`, `per_page`, `search`, optional `division`. **List response:** `items`, `total`, `page`, `per_page`.

---

## 3. Containers, shipments, tracking, reminders

| Route | Method | Transport | Purpose | FE44 | NBS16 |
|-------|--------|-----------|---------|------|-------|
| `/api/crm/supply/containers/list` | POST | JSON-RPC | List containers | No | Yes |
| `/api/crm/supply/containers/<id>/get` | POST | JSON-RPC | Get one | No | No |
| `/api/crm/supply/containers/create` | POST | JSON-RPC | Create | No | Yes |
| `/api/crm/supply/containers/<id>/update` | POST | JSON-RPC | Update | No | No |
| `/api/crm/supply/containers/<id>/delete` | POST | JSON-RPC | Soft-delete | No | No |
| `/api/crm/supply/containers/<id>/mark_arrived` | POST | JSON-RPC | Arrived / complete-style | Yes | No |
| `/api/crm/supply/containers/<id>/clearance_delivered` | POST | JSON-RPC | Clearance workflow | Yes | Yes |
| `/api/crm/supply/containers/<id>/assign_driver` | POST | JSON-RPC | Placeholder ack | Yes | No |
| `/api/crm/supply/containers/<id>/unassign_driver` | POST | JSON-RPC | Placeholder | Yes | No |
| `/api/crm/supply/containers/<id>/set_reminder` | POST | JSON-RPC | Set reminder | Yes | No |
| `/api/crm/supply/containers/<id>/reminder` | GET, DELETE, OPTIONS | **HTTP** | Get / clear reminder | No | No |
| `/api/crm/supply/containers/tracking/view` | GET, OPTIONS | **HTTP** | Tracking view (`?container_id=`) | No | No |
| `/api/crm/supply/containers/tracking/view` | POST | JSON-RPC | Same payload as GET style | No | No |
| `/api/crm/supply/containers/tracking/update` | POST | JSON-RPC | Update tracking URL/data | No | No |
| `/api/crm/supply/shipments/list` | POST | JSON-RPC | Shipment list (FE44 “containers”) | Yes | No |
| `/api/crm/supply/shipments/<id>/get` | POST | JSON-RPC | Get shipment | Yes | No |
| `/api/crm/supply/shipments/create` | POST | JSON-RPC | Create | Yes | No |
| `/api/crm/supply/shipments/<id>/update` | POST | JSON-RPC | Update | Yes | No |
| `/api/crm/supply/shipments/<id>/delete` | POST | JSON-RPC | Delete | Yes | No |
| `/api/crm/supply/shipments/<id>/link_orders` | POST | JSON-RPC | Link POs (`order_ids` / `po_ids`) | Yes | No |

**Container attachments & penalties** (`supply_controller.py`):  
`.../attachments/list` (POST JSON-RPC), `.../attachments/upload` (POST HTTP multipart), `.../attachments/<att_id>/delete` (POST JSON-RPC), `.../penalties/list`, `.../add_penalty`, `.../penalties/<pid>/delete` — **FE44: Yes** for all.

**Container comments** (`supply_chain_api_controller.py` stubs): `.../comments/list|add|.../delete` — return empty / stub; **FE44 calls list/add/delete** but **no real data** until wired.

---

## 4. Purchase orders

| Route | Method | Transport | Purpose | FE44 | NBS16 |
|-------|--------|-----------|---------|------|-------|
| `/api/crm/supply/po/list` | POST | JSON-RPC | PO list | Yes | Yes |
| `/api/crm/supply/po/suggested` | POST | JSON-RPC | `is_suggested` POs | Yes | Yes |
| `/api/crm/supply/po/create` | POST | JSON-RPC | Create | Yes | Yes |
| `/api/crm/supply/po/<id>/get` | POST | JSON-RPC | Get PO | Yes | Partial (NBS uses `/po/${id}`) |
| `/api/crm/supply/po/<id>/update` | POST | JSON-RPC | Update | Yes | Yes |
| `/api/crm/supply/po/<id>/delete` | POST | JSON-RPC | Soft-delete | Yes | No |
| `/api/crm/supply/po/<id>/order_e_sign` | POST | JSON-RPC | Order e-sign | **No** | No |
| `/api/crm/supply/po/<id>/confirm` | POST | JSON-RPC | Confirm | Yes | Yes (some flows) |
| `/api/crm/supply/po/<id>/submit` | POST | JSON-RPC | Alias of confirm | Yes | No |
| `/api/crm/supply/po/<id>/ship` | POST | JSON-RPC | Ship | Yes | No |
| `/api/crm/supply/po/<id>/receive` | POST | JSON-RPC | Receive | Yes | No |
| `/api/crm/supply/po/<id>/cancel` | POST | JSON-RPC | Cancel | Yes | Yes |
| `/api/crm/supply/po/<id>/reopen` | POST | JSON-RPC | Reopen draft | Yes | No |
| `/api/crm/supply/po/<id>/lines/add` | POST | JSON-RPC | Add line | Yes | Yes |
| `/api/crm/supply/po/<id>/lines/<line_id>/update` | POST | JSON-RPC | Update line | Yes | No |
| `/api/crm/supply/po/<id>/lines/<line_id>/delete` | POST | JSON-RPC | Delete line | Yes | No |
| `/api/crm/supply/po/<id>/attachments/list` | POST | JSON-RPC | List attachments | Yes | No |
| `/api/crm/supply/po/<id>/attachments/upload` | POST | **HTTP** multipart | Upload | Yes | No |
| `/api/crm/supply/po/<id>/attachments/link` | POST | JSON-RPC | Set M2M `attachment_ids` | **No** | No |
| `/api/crm/supply/po/<id>/attachments/<att_id>/delete` | POST | JSON-RPC | **See gaps** — not found in audited controllers | Yes (client) | No |
| `/api/crm/supply/po/<id>/packing-list/share` | POST | JSON-RPC | Plain text packing list | Yes | Yes |
| `/api/crm/supply/po/<id>/packing-list/pdf` | POST | JSON-RPC | PDF base64 | Yes | Yes |
| `/api/crm/supply/po/<id>/comments/list` | POST | JSON-RPC | Comments | Yes | No |
| `/api/crm/supply/po/<id>/comments/add` | POST | JSON-RPC | Add comment | Yes | No |
| `/api/crm/supply/po/<id>/comments/<msg_id>/delete` | POST | JSON-RPC | Delete comment | Yes | No |

---

## 5. Negotiations (`supply_extra_api_controller.py`)

| Route | Method | Transport | Purpose | FE44 | NBS16 |
|-------|--------|-----------|---------|------|-------|
| `/api/crm/supply/negotiations/list` | POST | JSON-RPC | List | Yes | No |
| `/api/crm/supply/negotiations/<id>/get` | POST | JSON-RPC | Detail | Yes | No |
| `/api/crm/supply/negotiations/create` | POST | JSON-RPC | Create | No | No |
| `/api/crm/supply/negotiations/<id>/update` | POST | JSON-RPC | Update | No | No |
| `/api/crm/supply/negotiations/<id>/delete` | POST | JSON-RPC | Delete | No | No |
| `/api/crm/supply/negotiations/<id>/confirm` | POST | JSON-RPC | Finalize | Yes | No |
| `/api/crm/supply/negotiations/<id>/finalize` | POST | JSON-RPC | Alias of confirm | Yes | No |
| `/api/crm/supply/negotiations/<id>/e_sign_approve` | POST | JSON-RPC | E-sign (ongoing) | Yes | No |
| `/api/crm/supply/negotiations/<id>/offers/add` | POST | JSON-RPC | Add offer | No | No |
| `/api/crm/supply/negotiations/<id>/offers/list` | POST | JSON-RPC | List offers | No | No |
| `/api/crm/supply/negotiations/<id>/comments/list` | POST | JSON-RPC | Comments | Yes | No |
| `/api/crm/supply/negotiations/<id>/comments/add` | POST | JSON-RPC | Add | Yes | No |
| `/api/crm/supply/negotiations/<id>/comments/<msg_id>/delete` | POST | JSON-RPC | Delete | Yes | No |
| `/api/crm/supply/negotiations/<id>/attachments/link` | POST | JSON-RPC | Link attachments | No | No |

**List params:** `page`, `per_page`, `state`, `vendor_id`, `item_request_id`, `search`. **Get response:** full serialized negotiation (see `_serialize_negotiation` in `supply_extra_api_controller.py`).

---

## 6. Item requests, clearance, inventory, notifications, payments

| Route | Method | Transport | FE44 | NBS16 |
|-------|--------|-----------|------|-------|
| `/api/crm/supply/item_requests/list` | POST | JSON-RPC | No | No |
| `/api/crm/supply/item_requests/<id>/get` | POST | JSON-RPC | No | No |
| `/api/crm/supply/item_requests/create` | POST | JSON-RPC | No | No |
| `/api/crm/supply/item_requests/<id>/update` | POST | JSON-RPC | No | No |
| `/api/crm/supply/item_requests/<id>/requester_confirm` | POST | JSON-RPC | No | No |
| `/api/crm/supply/item_requests/<id>/attachments/link` | POST | JSON-RPC | No | No |
| `/api/crm/supply/item_requests/<id>/update_status` | POST | JSON-RPC | No | No |
| `/api/crm/supply/item_requests/<id>/delete` | POST | JSON-RPC | No | No |
| `/api/crm/supply/clearance_companies/list|get|create|update|delete` | POST | JSON-RPC | No | No |
| `/api/crm/supply/inventory/minmax` | POST | JSON-RPC | No | No |
| `/api/crm/supply/inventory/minmax/update` | POST | JSON-RPC | No | No |
| `/api/crm/supply/inventory/minmax/delete` | POST | JSON-RPC | No | No |
| `/api/crm/supply/notifications/list|create|.../mark_read|mark_all_read|.../delete` | POST | JSON-RPC | No | No |
| `/api/crm/supply/payments/list` | POST | JSON-RPC | No | No |
| `/api/crm/supply/payments/<id>/get` | POST | JSON-RPC | No | No |
| `/api/crm/supply/payments/po/list` | POST | JSON-RPC | Yes | No |
| `/api/crm/supply/payments/create` | POST | JSON-RPC | Yes | No |
| `/api/crm/supply/payments/<id>/update` | POST | JSON-RPC | No | No |
| `/api/crm/supply/payments/<id>/delete` | POST | JSON-RPC | No | No |
| `/api/crm/supply/payments/<id>/attachments/link` | POST | JSON-RPC | No | No |

---

## 7. Supply chat (`supply_chat_controller.py`)

All **POST JSON-RPC** unless noted:  
`conversations/list`, `create`, `<id>/get`, `rename`, `archive`, `leave`, `update`, `mark_read`, `typing`, `members/list`, `members/add`, `members/remove`, `members/role`, `messages/list`, `messages/create`, `messages/<id>/edit`, `pin`, `react`, `delivered`, `read`, `messages/forward`, `conversations/<id>/pinned`, `messages/search`, `chat/bus_channels`.

| FE44 | NBS16 |
|------|-------|
| **No** | **No** |

**Also:** `POST /api/crm/supply/messages/<id>/delete` (`supply_controller.py`), `POST /api/crm/supply/chat/upload` (**HTTP** multipart) — **No** in-repo FE.

---

## 8. Supply stories (`supply_stories_controller.py`)

| Route | Method | Transport | FE44 | NBS16 |
|-------|--------|-----------|------|-------|
| `/api/crm/supply/stories/feed` | POST | JSON-RPC | No | No |
| `/api/crm/supply/stories/create` | POST | JSON-RPC | No | No |
| `/api/crm/supply/stories/<id>/view` | POST | JSON-RPC | No | No |
| `/api/crm/supply/stories/<id>/viewers` | POST | JSON-RPC | No | No |
| `/api/crm/supply/stories/<id>/delete` | POST | JSON-RPC | No | No |
| `/api/crm/supply/stories/upload` | POST | **HTTP** multipart | No | No |

---

## 9. Unused dashboard API candidates (in this repo)

Strong candidates to **power dashboard widgets** not yet used in **FE44** or **NBS16**:

- `POST /api/crm/supply/dashboard/summary`
- `POST /api/crm/supply/notifications/*`
- `POST /api/crm/supply/item_requests/*`
- `POST /api/crm/supply/payments/list`, `payments/<id>/get|update|delete`, `payments/<id>/attachments/link`
- `POST /api/crm/supply/inventory/minmax*`
- `POST /api/crm/supply/clearance_companies/*`
- Tracking + reminder **HTTP** routes
- Negotiations **create / update / offers / attachments**
- `POST .../po/<id>/order_e_sign`, `.../attachments/link`
- **Chat** and **Stories** APIs

---

## 10. Gaps / risks

| Topic | Detail |
|-------|--------|
| **PO attachment delete** | `supplyApi.poAttachDelete` targets `POST .../po/<id>/attachments/<att_id>/delete` — **no `@http.route` in the five audited controllers** (only container attachment delete exists). Implement route or remove client. |
| **Container comments** | Routes return **stub empty** data. |
| **NBS16 paths** | `/po/${id}` and `/vendors/${id}` do not match backend `/get` suffixes. |

---

## 11. File map

| File | Responsibility |
|------|----------------|
| `addons/lugal_crm/controllers/supply_chain_api_controller.py` | Vendors, containers, POs, lines, PO attachments upload/link, packing list, comments, **dashboard/summary**, stub container comments |
| `addons/lugal_crm/controllers/supply_controller.py` | Container attach/penalties, HTTP tracking GET, chat upload, message delete, **po/suggested** |
| `addons/lugal_crm/controllers/supply_extra_api_controller.py` | Negotiations, item requests, clearance, inventory, notifications, payments, shipments, JSON-RPC tracking |
| `addons/lugal_crm/controllers/supply_chat_controller.py` | Chat CRUD |
| `addons/lugal_crm/controllers/supply_stories_controller.py` | Stories |
| `frontends/44/src/services/supplyApi.ts` | FE44 client |
| `addons/lugal_crm/NBS CRM (16)/src/features/supply-chain/services/supplyService.ts` | NBS16 subset client |

---

*Disclaimer: “No” means no match in this repository search; other deployments may integrate these APIs.*
