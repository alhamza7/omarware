# Payment Form Frontend UX Fix

**Audience:** Frontend developers (Supply Chain SPA, e.g. `frontends/44`)  
**Related backend work:** `PAYMENT_FORM_BACKEND_SUPPORT_TASK.md`, `PAYMENT_FORM_BACKEND_SUPPORT_REPORT.md`

---

## Objective

Fix Supply Chain **payment create/edit** form UX.

### Current issues

1. **Linked Order ID** is a manual numeric input.
2. **Currency ID** is a manual numeric input.

Users should **not** manually type internal database IDs.

---

## 1. Linked Order field improvement

### Current

- Plain input field for linked order id.

### Required

- Replace with **searchable dropdown / autocomplete**.

### Backend API

**POST** `/api/crm/supply/payments/po/list`

Search should cover (as supported by the API):

- PO name / order reference
- Vendor name  
- (Optional broader search if backend exposes it, e.g. item request / negotiation names)

### Display

- Readable PO label (e.g. from `label`, or composed from `name` + vendor + `status`).
- Examples: `PO-2026-001`, `PO-2026-002`.

### Behavior

- Store the selected PO’s **internal `id`** in form state only; submit as `po_id` (or `linked_order_id` if the API accepts that alias).
- **Do not** expose a raw numeric ID field as the primary user input.

---

## 2. Currency field improvement

### Current

- Numeric Currency ID input.

### Required

- Replace with **dropdown / select**.

### Backend API

Use **`POST /api/crm/supply/currencies/list`** (or an existing documented endpoint if the project standardizes on another route with the same auth model).

### Display

- Human-readable options, e.g. **USD**, **EUR**, **INR**, **SAR** (name + symbol as appropriate).

### Behavior

- Store **`currency_id`** internally when an option is selected.
- **Do not** show a numeric currency id text input to the user.

---

## 3. Edit payment form prefill

When **editing** a payment:

- Show the selected PO as a **readable name** (e.g. `order_name`, `po_name`, or `label` from PO list if re-fetched).
- Show the selected currency as a **readable name** (e.g. `currency_name` + `currency_symbol` from payment GET).

### Examples (user-visible copy)

- Purchase Order: `PO-2026-001`
- Currency: `USD`

### Do not show as primary labels

- Raw values like `20` or `1` for PO / currency, except where unavoidable in debug-only tooling.

Internally, payloads may still use integer ids.

---

## 4. Form behavior

The payment form should:

- Work for **create** and **edit**.
- Keep **selected dropdown values** in sync with loaded payment data.
- **Submit** correct integer ids to the backend (`po_id`, `currency_id`, etc.).

The UI stays human-friendly; the payload may still look like:

```json
{
  "po_id": 20,
  "currency_id": 1
}
```

---

## UI requirements

- Searchable dropdown for purchase orders.
- Select dropdown for currency.
- Clear **validation** messages (missing PO, missing amount, invalid selection, etc.).
- **Loading** states while fetching PO options and currencies.

---

## Validation (QA)

Verify:

1. **Create** payment succeeds end-to-end.
2. **Edit** payment succeeds end-to-end.
3. **No** manual typing of internal PO / currency ids for normal flows.
4. Correct **`po_id`** / **`currency_id`** (and other required fields) are still sent to the backend.

---

## Deliverable

After implementation, create:

**`PAYMENT_FORM_FRONTEND_FIX_REPORT.md`**

Include:

- Files changed  
- Components updated  
- APIs integrated  
- Screenshots and/or short QA notes  

---

*End of task document.*
