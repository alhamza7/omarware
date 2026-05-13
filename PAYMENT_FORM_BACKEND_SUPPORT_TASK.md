# Payment Form — Backend Support Improvements

**Audience:** Backend developers (Odoo / `lugal_crm` supply APIs)  
**Goal:** Improve API payloads and endpoints so the **Supply Chain → Payments → Create/Edit** form can use **searchable PO selection** and **currency dropdowns** without exposing raw internal IDs as the primary user input.  
**Related frontend task:** `PAYMENT_FORM_UX_FIX_TASK.md` (if present) — FE consumes the APIs described here.

---

## 1. Objective

Remove the need for end users (and ideally frontends) to **manually type**:

1. **Linked order ID** — numeric PO primary key  
2. **Currency ID** — numeric `res.currency` primary key  

by providing:

- A **richer, searchable** PO list API (or an enhanced existing one) with human-readable labels and fields needed for filters/display.  
- A **currency list** API (or documented reuse of an existing global endpoint) for dropdown population.  
- **Read-friendly** fields on **payment get** for edit-form prefills.

---

## 2. Current backend state (audit snapshot)

*As implemented in `addons/lugal_crm/controllers/supply_extra_api_controller.py` (verify on branch before coding).*

### 2.1 `POST /api/crm/supply/payments/po/list`

| Property | Current behavior |
|----------|------------------|
| **Handler** | `supply_payments_po_dropdown_list` |
| **Response envelope** | `{ "success": true, "data": { "total", "page", "per_page", "items": [...] } }` — **not** a bare array at `data`. |
| **Search** | `search` applies `ilike` on PO **`name`** OR **`vendor_id.name`**. |
| **Filters** | Optional `status`, `division` (same as PO list patterns). |
| **Each item** | `_serialize_po_for_payment_dropdown(po)` → `{ "id", "name", "supplier" }` where `supplier` is the vendor name string. |

**Gaps vs UX needs:**

| Desired field | Present? |
|-----------------|----------|
| `id` | Yes |
| `name` / order number | Yes (`name`) |
| Vendor display | Yes (as `supplier`, not `vendor_name`) |
| `status` | **No** |
| `division` | **No** |
| `currency_id` | **No** |
| Explicit `label` / `display_name` for combobox | **No** (FE can compose `name + supplier`) |

### 2.2 `POST /api/crm/supply/payments/<id>/get`

| Property | Current behavior |
|----------|------------------|
| **Serializer** | `_serialize_payment(p)` |
| **PO / order** | Includes `po_id`, `linked_order_id`, `order_name` |
| **Currency** | Includes `currency_id`, `currency_name` |
| **Missing for polish** | `currency_symbol`, explicit `po_name` duplicate of `order_name` (optional), PO `status` for read-only context |

### 2.3 Currency listing

| Finding | Detail |
|---------|--------|
| **Dedicated supply endpoint** | No `POST /api/crm/supply/currencies/list` (or similar) found under `addons/lugal_crm/controllers` at audit time. |
| **Alternatives** | Standard Odoo RPC to `res.currency` from FE (if allowed by deployment), or a **new** thin JSON-RPC route under `/api/crm/supply/` for consistency with the rest of the Supply SPA. |

---

## 3. Task 1 — Purchase Order search support for payments

### 3.1 Audit

- **Endpoint:** `POST /api/crm/supply/payments/po/list`  
- **File:** `supply_extra_api_controller.py` — functions `supply_payments_po_dropdown_list`, `_serialize_po_for_payment_dropdown`.

### 3.2 Required outcome

Response items must be sufficient for a **searchable dropdown** without extra round-trips per row.

**Minimum recommended fields per item:**

| Field | Description |
|-------|-------------|
| `id` | PO database id (value submitted as `po_id`) |
| `name` | PO reference / order number |
| `vendor_name` | Supplier label (align naming with other supply APIs; can keep `supplier` as alias for backward compatibility) |
| `status` | PO status (`draft` / `confirmed` / `cancelled`) |
| `division` | If field exists on PO |
| `currency_id` | PO currency (helps default payment currency when PO is selected) |
| `currency_name` | Human-readable currency |
| `label` *(optional)* | Single string for UI, e.g. `PO-2026-001 — ABC Supplier (confirmed)` |

**Example item (illustrative):**

```json
{
  "id": 20,
  "name": "PO-2026-001",
  "vendor_name": "ABC Supplier",
  "status": "confirmed",
  "division": "china",
  "currency_id": 1,
  "currency_name": "USD",
  "label": "PO-2026-001 — ABC Supplier"
}
```

### 3.3 Implementation notes

- Preserve existing keys (`id`, `name`, `supplier`) if any client already depends on them; **add** new keys rather than breaking silently where possible.  
- Keep pagination: `total`, `page`, `per_page`, `items`.  
- Ensure search still covers **PO name** and **vendor**; optionally extend to **item request** / **negotiation** names if those fields exist on `lugal.crm.supply.po` and product wants broader search.

### 3.4 Acceptance

- [ ] `items[]` entries include at least: `id`, `name`, vendor display, `status`, `currency_id`, `currency_name`.  
- [ ] `division` included when the PO model exposes it.  
- [ ] Backward compatible OR version note in `PAYMENT_FORM_BACKEND_SUPPORT_REPORT.md`.

---

## 4. Task 2 — Currency listing support

### 4.1 Audit

- Search codebase for existing **currency** list endpoints exposed to the same auth model as supply JSON-RPC (`ensure_jwt_user_id`).  
- If none suitable, implement a dedicated endpoint.

### 4.2 Preferred new endpoint (if needed)

| Property | Value |
|----------|--------|
| **Route** | `POST /api/crm/supply/currencies/list` |
| **Transport** | JSON-RPC (`type='jsonrpc'`, `auth='none'`, JWT guard) |
| **Purpose** | Return currencies safe for a payment form dropdown (typically **active** currencies used by the company). |

**Example response:**

```json
{
  "success": true,
  "data": {
    "items": [
      { "id": 1, "name": "USD", "symbol": "$", "position": "before" },
      { "id": 2, "name": "EUR", "symbol": "€", "position": "after" }
    ]
  }
}
```

Use `res.currency` (`active=True` unless product requires inactive). Include `symbol` and, if useful, `decimal_places` / `position` for display.

### 4.3 Alternatives

- Document reuse of an **existing** Odoo or CRM route if the SPA is allowed to call it with the same token.  
- If company multi-currency is filtered elsewhere, align domain with that logic.

### 4.4 Acceptance

- [ ] FE can populate a **dropdown** without hardcoding currency ids.  
- [ ] Endpoint documented in English API notes (see workspace rules for API `.md`).

---

## 5. Task 3 — Payment detail API readability

### 5.1 Audit

- **Endpoint:** `POST /api/crm/supply/payments/<payment_id>/get`  
- **Serializer:** `_serialize_payment`

### 5.2 Enhancements

Ensure the payment payload includes everything needed to **prefill** create/edit UI without guessing:

| Field | Purpose |
|-------|---------|
| `po_id` / `linked_order_id` | Already present — keep |
| `order_name` or `po_name` | Clear PO label (alias ok) |
| `currency_id` | Already present |
| `currency_name` | Already present |
| **`currency_symbol`** | **Add** from `res.currency.symbol` (when `currency_id` set) |
| Optional | PO `status`, vendor name on nested read for tooltip |

**Example fragment:**

```json
{
  "po_id": 20,
  "order_name": "PO-2026-001",
  "currency_id": 1,
  "currency_name": "USD",
  "currency_symbol": "$"
}
```

### 5.3 Acceptance

- [ ] Edit form can show **symbol + name** without a second currency fetch (optional second fetch still allowed).  
- [ ] No breaking removal of existing keys used by `frontends/44` or other clients.

---

## 6. Validation (after backend changes)

- [ ] Payment **create** still accepts `po_id` / `linked_order_id` and `currency_id` as integers in JSON body (unchanged contract).  
- [ ] FE can build forms using **only** list/get responses + user picks — no manual typing of raw ids for normal flows.  
- [ ] `payments/po/list` remains paginated and searchable under load.  
- [ ] New or changed routes registered and **module upgrade** not required for pure Python/controller changes unless new models are added (note in report if DB migration needed).

---

## 7. Deliverable — implementation report

After completing work, create:

**`PAYMENT_FORM_BACKEND_SUPPORT_REPORT.md`**

It must include:

| Section | Content |
|---------|---------|
| **APIs audited** | `payments/po/list`, `payments/<id>/get`, any currency-related routes found |
| **New APIs** | e.g. `currencies/list` route signature |
| **Enhanced fields** | Before/after for `_serialize_po_for_payment_dropdown` and `_serialize_payment` |
| **Routes / files changed** | Paths and PR link |
| **Module upgrade** | `lugal_crm` bump / `-u` if applicable |
| **FE handoff** | Example JSON snippets for QA |

---

## 8. References

| Resource | Path / note |
|----------|-------------|
| Payment PO dropdown + payment serializer | `addons/lugal_crm/controllers/supply_extra_api_controller.py` (`_serialize_po_for_payment_dropdown`, `_serialize_payment`, `supply_payments_po_dropdown_list`) |
| Payment model | `addons/lugal_crm/models/lugal_supply_payment.py` |
| PO model | `addons/lugal_crm/models/crm_supply_po.py` |

---

*End of task document.*
