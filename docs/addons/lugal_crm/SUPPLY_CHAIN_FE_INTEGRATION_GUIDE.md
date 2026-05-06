# Supply Chain APIs — Frontend Integration Guide

Single reference for integrating **`/api/crm/supply/*`** (workflow + vendors/containers/PO + chat).  
All technical content is **English** for API consumption.

---

## How to share this with the FE team

| Channel | Action |
|--------|--------|
| **Repository** | Point them to this file: `docs/addons/lugal_crm/SUPPLY_CHAIN_FE_INTEGRATION_GUIDE.md` (same branch as backend). |
| **Wiki / Notion / Slack** | Paste the markdown or export PDF/HTML from your IDE (“Markdown: Export” / print to PDF). |
| **Ticket** | Attach the file + backend base URL + environment (`dev` / `staging`). |
| **Pin version** | Mention **Git commit** or **release tag** so FE matches the deployed Odoo module version. |

Optional: generate a PDF locally:

```bash
# Example: pandoc (if installed)
pandoc docs/addons/lugal_crm/SUPPLY_CHAIN_FE_INTEGRATION_GUIDE.md -o SUPPLY_CHAIN_FE_INTEGRATION_GUIDE.pdf
```

---

## 1. Base URL and dev proxy

| Mode | Base URL | Notes |
|------|-----------|--------|
| **Vite dev** (recommended) | Same origin as the SPA, e.g. `http://localhost:5174` | Leave `VITE_ODOO_URL` empty; Vite proxies `/api`, `/web`, `/lugal` to Odoo (`VITE_PROXY_TARGET` in `frontends/44/.env`). |
| **Direct Odoo** | `https://<host>:<port>` | Set `VITE_ODOO_URL` to that origin (no trailing slash). Watch **CORS** if the SPA origin differs. |

Workflow SPA client pattern (see `frontends/44/src/services/supplyApi.ts`): JSON `POST` with JSON-RPC envelope.

---

## 2. Authentication

- Most `/api/crm/supply/*` routes expect:

  `Authorization: Bearer <access_token>`

- Obtain tokens via your existing Lugal auth endpoint used by the CRM app (e.g. **Login** in `supplyApi.ts`: `POST /lugal/auth/login` with JSON-RPC body).

- On **401**, refresh or redirect to login.

---

## 3. Request format (JSON-RPC)

**HTTP:** `POST`  
**Headers:** `Content-Type: application/json`, plus `Authorization` when logged in.

**Body:**

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "page": 1,
    "per_page": 20
  }
}
```

Route-specific parameters go inside **`params`** (flat object). Odoo returns:

```json
{
  "jsonrpc": "2.0",
  "id": null,
  "result": {
    "success": true,
    "data": { }
  }
}
```

Read **`result`** (or unwrap `json.result` in fetch code). Errors: `success: false`, `error` string.

**Pagination (when listed):** commonly `page`, `per_page` inside `params`.

---

## 4. Workflow integration map

Suggested UI flow and primary endpoints:

| Step | Backend concept | Main endpoints |
|------|------------------|----------------|
| 1 | Item request | `item_requests/*` |
| 2 | Negotiation | `negotiations/*` (+ `confirm` / `e_sign_approve`, `offers/add`) |
| 3 | Purchase order (order) | `po/*` (+ `order_e_sign`, link `item_request_id`, `negotiation_id`) |
| 4 | Payment | `payments/*` |
| 5 | Shipment | `shipments/*` (backed by container records) |

Supporting: `vendors/*`, `containers/*`, notifications, inventory min/max, clearance companies.

---

## 5. Endpoint catalogue

Unless noted: **`POST`**, JSON-RPC, **`type=jsonrpc`**.

### 5.1 Item requests

| Path | Purpose |
|------|---------|
| `/api/crm/supply/item_requests/list` | List + filters (`state`, `priority`, `search`, pagination) |
| `/api/crm/supply/item_requests/<id>/get` | Detail |
| `/api/crm/supply/item_requests/create` | Create (`item_name` required; optional `packing` alias for pcs/carton) |
| `/api/crm/supply/item_requests/<id>/update` | Update |
| `/api/crm/supply/item_requests/<id>/delete` | Soft delete |
| `/api/crm/supply/item_requests/<id>/update_status` | Set `state` |
| `/api/crm/supply/item_requests/<id>/requester_confirm` | Requester confirmation (e-sign on request) |
| `/api/crm/supply/item_requests/<id>/attachments/link` | Set `attachment_ids` after upload (`attachment_ids`: number[]) |

### 5.2 Negotiations

| Path | Purpose |
|------|---------|
| `/api/crm/supply/negotiations/list` | List |
| `/api/crm/supply/negotiations/<id>/get` | Detail (includes offer history when serialized) |
| `/api/crm/supply/negotiations/create` | Create (`item_request_id`, `vendor_id` required; optional `agent_id`, `offered_price` seeds first offer) |
| `/api/crm/supply/negotiations/<id>/update` | Update |
| `/api/crm/supply/negotiations/<id>/delete` | Soft delete |
| `/api/crm/supply/negotiations/<id>/confirm` | Finalize negotiation (approval) |
| `/api/crm/supply/negotiations/<id>/e_sign_approve` | Same as confirm (negotiation-stage approval) |
| `/api/crm/supply/negotiations/<id>/offers/add` | Add offer row (`price` required) |
| `/api/crm/supply/negotiations/<id>/attachments/link` | Link `ir.attachment` ids |

### 5.3 Purchase orders (orders)

| Path | Purpose |
|------|---------|
| `/api/crm/supply/po/list` | List POs |
| `/api/crm/supply/po/suggested` | List suggested POs (`is_suggested`) |
| `/api/crm/supply/po/create` | Create (vendor via `vendor_customer_id` partner; optional `item_request_id`, `negotiation_id`, `agent_id`, `lines[]`) |
| `/api/crm/supply/po/<id>/get` | Detail + lines |
| `/api/crm/supply/po/<id>/update` | Update header + workflow fields |
| `/api/crm/supply/po/<id>/delete` | Soft delete |
| `/api/crm/supply/po/<id>/confirm` | Status → confirmed |
| `/api/crm/supply/po/<id>/ship` | Maps to confirmed (model has no separate shipped state) |
| `/api/crm/supply/po/<id>/receive` | Same |
| `/api/crm/supply/po/<id>/cancel` | Cancel |
| `/api/crm/supply/po/<id>/reopen` | Draft |
| `/api/crm/supply/po/<id>/order_e_sign` | Order confirmation signature (PO extend) |
| `/api/crm/supply/po/<id>/lines/add` | Add line |
| `/api/crm/supply/po/<id>/lines/<line_id>/update` | Update line |
| `/api/crm/supply/po/<id>/lines/<line_id>/delete` | Delete line |
| `/api/crm/supply/po/<id>/attachments/list` | List order attachments |
| `/api/crm/supply/po/<id>/attachments/link` | Link attachment ids |
| `GET /api/products/search` | Product picker (REST + JWT) — see **`docs/addons/lugal_crm/SUPPLY_PO_REST_FE_INTEGRATION.md`** |
| `POST /api/purchase-orders` | Create supply PO with **`items[].product_id`** from search — same short guide |

### 5.4 Payments

| Path | Purpose |
|------|---------|
| `/api/crm/supply/payments/list` | List (`po_id`, filters) |
| `/api/crm/supply/payments/<id>/get` | Detail |
| `/api/crm/supply/payments/create` | Create (`po_id` or `linked_order_id`, `amount`, …) |
| `/api/crm/supply/payments/<id>/update` | Update |
| `/api/crm/supply/payments/<id>/delete` | Delete record |
| `/api/crm/supply/payments/<id>/attachments/link` | Receipt files |

### 5.5 Shipments (container-backed)

| Path | Purpose |
|------|---------|
| `/api/crm/supply/shipments/list` | List |
| `/api/crm/supply/shipments/<id>/get` | Detail (`id` = container id) |
| `/api/crm/supply/shipments/create` | Create container/shipment |
| `/api/crm/supply/shipments/<id>/update` | Update |
| `/api/crm/supply/shipments/<id>/delete` | Soft delete |
| `/api/crm/supply/shipments/<id>/link_orders` | `order_ids` or `po_ids`: list of PO ids |

### 5.6 Vendors & containers (SPA)

| Area | Prefix |
|------|--------|
| Vendors | `/api/crm/supply/vendors/list`, `.../create`, `.../<id>/get|update|delete` |
| Containers | `/api/crm/supply/containers/list`, `.../create`, `.../<id>/get|update|delete`, `mark_arrived`, `clearance_delivered`, `assign_driver`, `unassign_driver`, `set_reminder` |

### 5.7 Tracking & extras (same controller family)

| Path | Notes |
|------|--------|
| `/api/crm/supply/containers/tracking/view` | **POST** JSON-RPC alias (params: `container_id`) or **GET** with query `container_id` (see `supply_controller`) |
| `/api/crm/supply/containers/tracking/update` | POST — update `tracking_url` / `tracking_data` |
| `/api/crm/supply/containers/<id>/attachments/list` | From `supply_controller` |
| `/api/crm/supply/containers/<id>/penalties/list` | Penalties |
| `/api/crm/supply/clearance_companies/*` | CRUD |
| `/api/crm/supply/inventory/minmax` | List / upsert / delete |
| `/api/crm/supply/notifications/*` | User notifications |

### 5.8 Multipart (not JSON-RPC params only)

| Path | Method | Purpose |
|------|--------|---------|
| `/api/crm/supply/chat/upload` | POST multipart | Chat files (see controller for field names) |

### 5.9 Supply chat & stories (optional UI)

- **Chat:** `/api/crm/supply/conversations/*`, `/api/crm/supply/messages/*`, `/api/crm/supply/chat/bus_channels`
- **Stories:** `/api/crm/supply/stories/*`

---

## 6. Attachments pattern

1. Upload binary via an existing upload endpoint (generic CRM upload or `chat/upload` depending on product rules) to obtain **`ir.attachment` `id`** values.
2. Call the corresponding **`.../attachments/link`** route with `attachment_ids: [<id>, ...]` in JSON-RPC `params`.

---

## 7. TypeScript client

The SPA already centralizes many calls in:

`frontends/44/src/services/supplyApi.ts`

Extend that module (or add `supplyWorkflowApi.ts`) for new paths (`item_requests`, `negotiations`, `payments`, `shipments`) using the same **`rpc()`** helper pattern.

**REST product search + PO create** (plain `fetch` / `axios`, not JSON-RPC): see **`docs/addons/lugal_crm/SUPPLY_PO_REST_FE_INTEGRATION.md`**.

---

## 8. Related documents

- `SUPPLY_WORKFLOW_API_REPORT.md` — audit + workflow endpoint summary (backend-focused).
- Controller source for exact validation messages: `addons/lugal_crm/controllers/supply_*_*.py`.

---

## 9. Checklist for FE before go-live

- [ ] Confirm **base URL** and **proxy env** (`VITE_PROXY_TARGET`) match deployed Odoo.
- [ ] Login flow returns JWT and **Authorization** header is set on every supply call.
- [ ] Parse **`result.success`**; surface **`result.error`** to the user.
- [ ] Workflow: create request → negotiation → PO with links → payments → shipment `link_orders`.
- [ ] Run **module upgrade** on server (`-u lugal_crm`) when backend ships new routes.
