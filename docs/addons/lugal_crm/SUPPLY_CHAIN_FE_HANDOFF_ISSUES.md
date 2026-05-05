# Supply Chain Frontend — Issue Handoff & Integration Notes

**Audience:** Frontend developers (Supply Chain SPA)  
**Scope:** Payments, Purchase Order attachments, and related API usage  
**Backend status:** Items below are implemented in `lugal_crm` on `development` unless noted.

> **Note:** This document was prepared from the agreed backend/FE alignment work. If you have extra rows in a separate issue PDF, append them under [§ Additional items from product QA](#additional-items-from-product-qa).

---

## 1. Payments — Create / Edit

### 1.1 Issue summary

- Purchase Order must not rely on manual/free-text PO identifiers for create flows.
- Payment type options must match backend values.
- Invalid or deleted POs should show a clear message, not a generic or raw DB error.

### 1.2 Expected behavior (acceptance)

- **PO selection:** Searchable control (async search / combobox) listing active, non-deleted purchase orders; display **reference + supplier (vendor) name**; submit **`po_id` as integer** (database id).
- **Payment type:** Allowed values: `deposit`, `installment`, `final`, `other`. Labels in UI may be human-readable; payload must use these keys. Legacy synonyms accepted by API: `partial` → `installment`, `full` → `final` (prefer sending canonical keys from FE).
- **Errors:** Surface API `error` string when `success === false` (e.g. `Invalid Purchase Order selected`).

### 1.3 APIs

| Purpose | Method | Path | Type |
|--------|--------|------|------|
| PO list for dropdown | POST | `/api/crm/supply/payments/po/list` | JSON-RPC |
| Create payment | POST | `/api/crm/supply/payments/create` | JSON-RPC |
| List payments (optional filters) | POST | `/api/crm/supply/payments/list` | JSON-RPC |

**PO dropdown — request (typical params):**

```json
{
  "search": "PO-001",
  "page": 1,
  "per_page": 20
}
```

Optional: `status`, `division`.

**PO dropdown — response (`data`):**

```json
{
  "total": 42,
  "page": 1,
  "per_page": 20,
  "items": [
    { "id": 12, "name": "PO-0012", "supplier": "ABC Supplier" }
  ]
}
```

**Create payment — request (minimal):**

```json
{
  "po_id": 12,
  "amount": 1500.0,
  "payment_type": "final"
}
```

Also supported: `linked_order_id` (alias for `po_id`), `currency_id`, `payment_date`, `payment_method`, `notes`, `paid_to`, `payee_partner_id`, attachments per existing supply attachment patterns.

### 1.4 Frontend checklist

- [ ] Bind dropdown option value to **`items[].id`** → `po_id`.
- [ ] Option label: e.g. `name — supplier`.
- [ ] Debounce search; support pagination via `page` / `per_page`.
- [ ] Client-side: require PO + amount + `payment_type` before submit.
- [ ] Display backend `error` on failure.

---

## 2. Purchase Orders — Attachments tab (upload)

### 2.1 Issue summary

- Uploads targeting `POST /api/crm/supply/po/{po_id}/attachments/upload` previously returned **404** because the route was missing; route is **registered** now.

### 2.2 Expected behavior (acceptance)

- User selects file(s); upload succeeds; new files appear after refresh or after merging response into state.
- On failure, show **`error`** from JSON body (and HTTP status when useful).

### 2.3 API

| Purpose | Method | Path | Type |
|--------|--------|------|------|
| Upload files | POST | `/api/crm/supply/po/<po_id>/attachments/upload` | **HTTP** multipart |
| List attachments | POST | `/api/crm/supply/po/<po_id>/attachments/list` | JSON-RPC |
| Link existing attachment ids | POST | `/api/crm/supply/po/<po_id>/attachments/link` | JSON-RPC |

**Upload — requirements**

- **Not** JSON-RPC on this URL: use **`multipart/form-data`** (`FormData`).
- **Auth:** Same JWT as other Supply APIs (`Authorization` header as already used in the app).
- **Form field names:** `file`, `files`, or `files[]` (at least one file).

**Upload — success response (JSON body, HTTP 200):**

```json
{
  "success": true,
  "data": {
    "po_id": 25,
    "uploaded_count": 1,
    "files": [
      {
        "id": 123,
        "name": "document.pdf",
        "mimetype": "application/pdf",
        "size": 45678,
        "url": "/web/content/123",
        "file_url": "/web/content/123?access_token=...",
        "uploaded_by_name": "",
        "created_at": "2026-05-05T12:00:00"
      }
    ]
  }
}
```

**Typical errors:** `401` Unauthorized, `404` PO not found, `400` no files / unsupported type / size limit, `500` with `error` message.

### 2.4 Frontend checklist

- [ ] Use **HTTP client** with `FormData` for upload (not the JSON-RPC transport).
- [ ] Send JWT on upload request.
- [ ] After success, call **`attachments/list`** or append `data.files` to UI state.
- [ ] Handle CORS preflight (`OPTIONS`) if calling from browser (route allows CORS).

---

## 3. Additional items from product QA

*Paste any extra issues from your PDF here (one bullet per issue). For each, add: screen, current behavior, expected behavior, and API if applicable.*

- …
- …

---

## 4. References (repo)

- Supply models / endpoints overview: `docs/addons/lugal_crm/SUPPLY_CHAIN_MODELS_API.md`
- FE integration: `docs/addons/lugal_crm/SUPPLY_CHAIN_FE_INTEGRATION_GUIDE.md`

---

*End of handoff document.*
