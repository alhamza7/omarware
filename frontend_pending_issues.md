# Frontend Pending Issues

Supply Chain module — items to resolve in the frontend (and verify backend where noted).

---

## Issue 1 — Packing List modal: Share and PDF buttons not actionable

### Issue Found

In the Packing List modal, **Share** and **PDF** controls are visible but **not clickable** (or they do not run any flow).

### Current Behavior

Users see Share/PDF UI affordances; nothing useful happens on interaction (no share sheet, no download, no error feedback).

### Required Fix

1. Confirm backend routes respond successfully for the active environment (see API notes).
2. If APIs exist: wire both buttons — handlers, loading/error states, and JWT on requests where applicable.
3. If APIs are missing or return errors: document the gap for backend and disable or hide buttons until fixed.
4. **Share:** trigger the platform share flow (e.g. Web Share API with title + text from API) and/or copy-to-clipboard fallback where share is unavailable.
5. **PDF:** download or open the PDF from the API response (e.g. decode `pdf_base64`, create blob, trigger download with server-provided filename).

### API / Integration Notes

- **Share (plain text):** `POST /api/crm/supply/po/<po_id>/packing-list/share` — JSON-RPC, auth as other supply routes; expect payload with text/title suitable for sharing.
- **PDF:** `POST /api/crm/supply/po/<po_id>/packing-list/pdf` — JSON-RPC; expect e.g. `filename`, `pdf_base64`, `mimetype`.
- Audit both in the target deployment before shipping UI logic.

### Acceptance Criteria

- Share initiates a real share or clipboard fallback; user gets clear feedback on failure.
- PDF results in a downloaded or opened PDF file with the correct name.
- Buttons are disabled or hidden when the PO id is invalid or the API is unavailable (no dead clicks).
- No silent failures: errors from the API are surfaced in the UI.

---

## Issue 2 — Container → Link Purchase Order: replace manual Order ID with searchable PO picker

### Issue Found

The “Link Purchase Order” flow relies on a **manual numeric Order ID** field instead of a searchable, server-backed selector.

### Current Behavior

Users must know and type internal PO ids; high error rate and poor discoverability.

### Required Fix

1. Remove the free-text / numeric-only Order ID input as the primary linking control.
2. Add a **searchable dropdown** (combobox/async select) that queries the backend as the user types.
3. Bind the selected row’s **`id`** to the internal field used for create/link (e.g. **`po_id`**), not a manually typed string.
4. Debounce search input; handle empty results and loading state.

### API / Integration Notes

- **PO dropdown (lightweight list):** `POST /api/crm/supply/payments/po/list`
- Body (typical): `page`, `per_page`, optional `search`, `status`, `division`.
- Response items: use each item’s **`id`** as **`po_id`** for payment/link create endpoints.
- Same JSON-RPC + JWT pattern as other `/api/crm/supply/*` routes.

### Acceptance Criteria

- No requirement for users to type raw numeric Odoo ids for normal linking.
- Search returns PO rows (reference + vendor/supplier label as returned by API).
- Selected PO’s `id` is what gets submitted as `po_id` (or equivalent) on save.
- Empty search and errors are handled in the UI.

---

## Issue 3 — Supplier detail modal: Edit and Delete not working

### Issue Found

**Edit** and **Delete** actions on the supplier detail modal do not complete successfully (or are not wired).

### Current Behavior

Clicks on Edit/Delete either do nothing, fail silently, or error without a proper flow.

### Required Fix

1. **Edit:** Open an edit state or form; on save, call the vendor/supplier **update** API with changed fields only; refresh detail and list on success; show API errors.
2. **Delete:** Open a **confirmation** modal; on confirm, call the **delete** API; remove from list / close detail on success; show API errors.
3. Align field names with the API (e.g. `contact_name` vs `contact_person` if using supplier alias routes — see notes).

### API / Integration Notes

- **Update (existing):** `POST /api/crm/supply/vendors/<vendor_id>/update`
- **Delete (existing):** `POST /api/crm/supply/vendors/<vendor_id>/delete` — soft delete pattern (`is_deleted` / inactive) on backend.
- **Alias routes (optional, supplier naming + `contact_person` / string `country`):**
  - `POST /api/crm/supply/suppliers/<supplier_id>/update`
  - `POST /api/crm/supply/suppliers/<supplier_id>/delete`
- Use the same auth envelope as other supply JSON-RPC calls.

### Acceptance Criteria

- Edit saves changes and the UI reflects updated data without a full page reload (refetch or local merge acceptable).
- Delete asks for confirmation, then removes the supplier from the list view and closes or clears the detail modal on success.
- Invalid id / not found / unauthorized responses show a clear message.
- No dead buttons: loading state while requests are in flight.
