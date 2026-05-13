# Payment Form — Backend Support (Implementation Report)

This document summarizes changes made per `PAYMENT_FORM_BACKEND_SUPPORT_TASK.md`: richer PO rows for payment linking, a currencies list endpoint, clearer payment serialization, frontend consumption, and create behavior when `currency_id` is omitted.

---

## 1. APIs audited

| Endpoint | Handler | Notes |
|----------|---------|--------|
| `POST /api/crm/supply/payments/po/list` | `supply_payments_po_dropdown_list` | Pagination + search; serializer extended. |
| `POST /api/crm/supply/payments/<id>/get` | `supply_payments_get` | Uses `_serialize_payment` (extended). |
| `POST /api/crm/supply/payments/create` | `supply_payments_create` | Defaults `currency_id` from PO when omitted. |
| Currency listing (supply namespace) | **New** `supply_currencies_list` | Active `res.currency` rows for dropdowns. |

No other CRM supply currency route was reused; a dedicated supply JSON-RPC route keeps the same JWT guard as other supply APIs.

---

## 2. New API

### `POST /api/crm/supply/currencies/list`

- **Transport:** JSON-RPC (`type='jsonrpc'`, `auth='none'`, CSRF off), same pattern as other `/api/crm/supply/*` routes; requires valid JWT (`ensure_jwt_user_id`).
- **Body (typical):** `page`, `per_page` (defaults via `_pagination`), optional `search` (matches `name` or `symbol`, `ilike`).
- **Response:**

```json
{
  "success": true,
  "data": {
    "total": 12,
    "page": 1,
    "per_page": 200,
    "items": [
      {
        "id": 1,
        "name": "USD",
        "symbol": "$",
        "position": "before",
        "decimal_places": 2
      }
    ]
  }
}
```

- **Model:** `res.currency`, domain `active=True`.

---

## 3. Enhanced fields

### `_serialize_po_for_payment_dropdown`

| Before | After |
|--------|--------|
| `id`, `name`, `supplier` | Same keys preserved; added `vendor_name`, `status`, `division`, `currency_id`, `currency_name`, `currency_symbol`, `label` |

`supplier` remains the vendor display string (duplicate of `vendor_name` for backward compatibility).

### `supply_payments_po_dropdown_list` (search)

- Search still matches PO `name` and `vendor_id.name`.
- If the model defines `item_request_id` / `negotiation_id`, search also matches related `name` fields.

### `_serialize_payment`

| Addition | Purpose |
|----------|---------|
| `currency_symbol` | From `res.currency.symbol` for display without a second fetch. |
| `po_name` | Alias of PO reference (alongside `order_name`). |
| `po_status` | PO `status` when a linked PO exists. |

Existing keys (`po_id`, `linked_order_id`, `order_name`, `currency_id`, `currency_name`, etc.) are unchanged.

### `supply_payments_create`

- If `currency_id` is **not** sent and the linked PO has `currency_id`, the created payment uses the **PO currency**.
- If neither is set, the payment model falls back to its default (company currency).

---

## 4. Files changed

| Path | Change |
|------|--------|
| `addons/lugal_crm/controllers/supply_extra_api_controller.py` | PO serializer, payment serializer, PO search, `supply_currencies_list`, create `currency_id` default. |
| `frontends/44/src/types/supply.ts` | `PaymentPoDropdownItem`, `SupplyPayment`, `CurrencyDropdownItem`, `PaymentCurrenciesListData`. |
| `frontends/44/src/services/supplyApi.ts` | `paymentsCurrenciesList`, default export. |
| `frontends/44/src/features/supply/containers/PoContainer.tsx` | `RecordPaymentModal`: load currencies, currency `<select>`, richer PO labels. |
| `PAYMENT_FORM_BACKEND_SUPPORT_REPORT.md` | This report. |

---

## 5. Module upgrade

- **Database migration:** Not required (controller-only and optional serializer fields).
- **Deploy:** Restart Odoo / reload Python so the new route and serializer changes apply (same as any controller edit). No `-u lugal_crm` needed for these changes alone.

---

## 6. Frontend handoff / QA snippets

**PO list item (example):**

```json
{
  "id": 20,
  "name": "PO-2026-001",
  "supplier": "ABC Supplier",
  "vendor_name": "ABC Supplier",
  "status": "confirmed",
  "division": "china",
  "currency_id": 1,
  "currency_name": "USD",
  "currency_symbol": "$",
  "label": "PO-2026-001 — ABC Supplier (confirmed)"
}
```

**Payment get fragment:**

```json
{
  "po_id": 20,
  "order_name": "PO-2026-001",
  "po_name": "PO-2026-001",
  "po_status": "confirmed",
  "currency_id": 1,
  "currency_name": "USD",
  "currency_symbol": "$"
}
```

**Create body (unchanged contract):** integer `po_id` (or `linked_order_id`), `amount`, optional `currency_id`, optional `payment_type`, etc.

---

*End of report.*
