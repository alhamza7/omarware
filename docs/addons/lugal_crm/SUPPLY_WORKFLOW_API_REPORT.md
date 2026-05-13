# Supply Workflow API — Audit & Implementation Report

**Workflow:** Item Request → Negotiation → Order (PO) → Payment → Shipment  
**Auth:** All routes below use JSON-RPC `POST`, `type='jsonrpc'`, JWT via `Authorization: Bearer <token>` (`ensure_jwt_user_id()`).  
**Response shape:** `{ "success": true|false, "data": {...}, "error"?: "..." }` (wrapped in JSON-RPC `result` by Odoo).

---

## 1. Audit Summary

### Already available (reused, not duplicated)

| Area | Model / code | Notes |
|------|----------------|--------|
| Item request | `lugal.supply.item.request` | Sequences, mail.thread, attachments, priority, state, requester e-sign |
| Negotiation | `lugal.supply.negotiation`, `lugal.supply.negotiation.offer` | Supplier, optional agent, offer history, finalize/cancel, attachments |
| Order | `lugal.crm.supply.po`, `lugal.crm.supply.po.line` | Links to request + negotiation, payments, order e-sign, order attachments |
| Payment | `lugal.supply.payment` | Linked to PO, deposit/partial/full, receipt attachments, computed status |
| Shipment | `lugal.supply.container` | `shipment_ref`, tracking, `purchase_order_ids` (CRM), transport, ports |
| Vendors / PO CRUD | `supply_chain_api_controller` | Vendors, containers, PO, lines, po/suggested |
| Chat / stories | `supply_chat_controller`, `supply_stories_controller` | Unchanged |
| Upload | `upload_controller`, `supply_controller` (chat upload) | Multipart patterns for files |

### Critical fix

- `supply_extra_api_controller.py` **existed but was not imported** in `controllers/__init__.py`, so its routes were **never registered**. It is now **imported and loaded**.

### Missing before this work (now added or extended)

- Payment HTTP API (list/get/create/update/delete + receipt attachment link).
- Shipment API as **view over container** (no new SQL table).
- Negotiation: **confirm** / **e_sign_approve** (calls `action_finalize()`), **offers/add**, richer serialization (agent, offers, attachments).
- Item request: **requester_confirm**, **attachments/link** (link pre-uploaded `ir.attachment` ids).
- PO serializer extended with workflow + **order_e_sign** + **attachments/link**.
- PO create/update extended with `item_request_id`, `negotiation_id`, `agent_id`, dates, `payment_term`, `shipping_method`, `notes`.

### Comments (mail.thread)

- Models inherit `mail.thread`; structured comment REST API is **not** duplicated here. Use Odoo chatter / future `mail.message` endpoints if required.

### Database / migrations

- **No new tables** in this change set — workflow fields already exist on extended models.
- After deploy: `-u lugal_crm` (and `lugal_supply` if models change upstream).

---

## 2. Endpoint List (workflow-focused)

### Item Request (`lugal.supply.item.request`)

| Method | Path |
|--------|------|
| POST | `/api/crm/supply/item_requests/list` |
| POST | `/api/crm/supply/item_requests/<id>/get` |
| POST | `/api/crm/supply/item_requests/create` |
| POST | `/api/crm/supply/item_requests/<id>/update` |
| POST | `/api/crm/supply/item_requests/<id>/delete` |
| POST | `/api/crm/supply/item_requests/<id>/update_status` |
| POST | `/api/crm/supply/item_requests/<id>/requester_confirm` |
| POST | `/api/crm/supply/item_requests/<id>/attachments/link` |

### Negotiation (`lugal.supply.negotiation` + offers)

| Method | Path |
|--------|------|
| POST | `/api/crm/supply/negotiations/list` |
| POST | `/api/crm/supply/negotiations/<id>/get` |
| POST | `/api/crm/supply/negotiations/create` |
| POST | `/api/crm/supply/negotiations/<id>/update` |
| POST | `/api/crm/supply/negotiations/<id>/delete` |
| POST | `/api/crm/supply/negotiations/<id>/confirm` |
| POST | `/api/crm/supply/negotiations/<id>/e_sign_approve` |
| POST | `/api/crm/supply/negotiations/<id>/offers/add` |
| POST | `/api/crm/supply/negotiations/<id>/attachments/link` |

### Order (Purchase Order — `lugal.crm.supply.po`)

Implemented in `supply_chain_api_controller.py`:

| Method | Path |
|--------|------|
| POST | `/api/crm/supply/po/list` |
| POST | `/api/crm/supply/po/create` |
| POST | `/api/crm/supply/po/<id>/get` |
| POST | `/api/crm/supply/po/<id>/update` |
| POST | `/api/crm/supply/po/<id>/delete` |
| POST | `/api/crm/supply/po/<id>/confirm` |
| POST | `/api/crm/supply/po/<id>/cancel` |
| POST | `/api/crm/supply/po/<id>/reopen` |
| POST | `/api/crm/supply/po/<id>/lines/add` |
| POST | `/api/crm/supply/po/<id>/lines/<line_id>/update` |
| POST | `/api/crm/supply/po/<id>/lines/<line_id>/delete` |
| POST | `/api/crm/supply/po/<id>/attachments/list` |
| POST | `/api/crm/supply/po/<id>/attachments/link` |
| POST | `/api/crm/supply/po/<id>/order_e_sign` |

Also: `supply_controller`: `POST /api/crm/supply/po/suggested`.

### Payment (`lugal.supply.payment`)

| Method | Path |
|--------|------|
| POST | `/api/crm/supply/payments/list` |
| POST | `/api/crm/supply/payments/<id>/get` |
| POST | `/api/crm/supply/payments/create` |
| POST | `/api/crm/supply/payments/<id>/update` |
| POST | `/api/crm/supply/payments/<id>/delete` |
| POST | `/api/crm/supply/payments/<id>/attachments/link` |

### Shipment (mapped to `lugal.supply.container`)

| Method | Path |
|--------|------|
| POST | `/api/crm/supply/shipments/list` |
| POST | `/api/crm/supply/shipments/<id>/get` |
| POST | `/api/crm/supply/shipments/create` |
| POST | `/api/crm/supply/shipments/<id>/update` |
| POST | `/api/crm/supply/shipments/<id>/delete` |
| POST | `/api/crm/supply/shipments/<id>/link_orders` |

### Other supply extras (unchanged paths, now registered)

Container tracking POST aliases, clearance companies, inventory min/max, notifications — see `supply_extra_api_controller.py`.

---

## 3. File touched

- `addons/lugal_crm/controllers/__init__.py` — register `supply_extra_api_controller`.
- `addons/lugal_crm/controllers/supply_extra_api_controller.py` — serializers + payments + shipments + workflow routes.
- `addons/lugal_crm/controllers/supply_chain_api_controller.py` — PO workflow fields, `order_e_sign`, `attachments/link`.
- `addons/lugal_crm/controllers/supply_controller.py` — `_serialize_supply_po` workflow fields.

---

## 4. Attachment upload pattern

Multipart uploads typically use existing CRM/upload endpoints to obtain `ir.attachment` ids; then call the corresponding `attachments/link` route with `attachment_ids: [ ... ]`.
