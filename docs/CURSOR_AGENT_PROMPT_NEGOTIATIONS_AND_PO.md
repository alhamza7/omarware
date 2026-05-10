# Cursor agent prompt: Negotiations filters + Purchase Order creation

Copy everything below the horizontal rule into a **new Cursor chat** (or paste into **Composer**) so another developer (or the agent) can implement fixes with full context.

---

## Role and scope

You are working on the **Supply Chain** React app under `frontends/44/`. Implement the following **two** product issues. Prefer small, reviewable changes; match existing patterns (Tailwind, `Button` / `Input`, `supplyApi`, `toast`, `useSupplyStore`).

**Stack reference:** TypeScript, React, Vite, existing UI components in `frontends/44/src/components/ui/`.

---

## Issue 1 — Negotiations: wire the three list filters (currently pending)

### Problem

In the **Negotiations** tab, the list API supports filters that are **not exposed in the UI**. Only text search is implemented today. Product expects **three additional filters** on the list screen (commonly: **state**, **vendor**, **item request** — align with the design mockup if labels differ).

### Evidence in code

- **UI container:** `frontends/44/src/features/supply/containers/NegotiationContainer.tsx`  
  - `load()` calls `supplyApi.negotiationList({ page, per_page, search })` only.
- **Client API:** `frontends/44/src/services/supplyApi.ts` — `negotiationList` already forwards optional `state`, `vendor_id`, `item_request_id`, and `search`.
- **Types:** `frontends/44/src/types/supply.ts` — `NegotiationListFilter` already includes `state`, `vendor_id`, `item_request_id`.
- **Backend contract (authoritative):** `docs/NEW_SUPPLY_APIS_EN.md` — section `**POST /api/crm/supply/negotiations/list`**  
  - `state`: optional — `ongoing` | `finalized` | `cancelled`  
  - `vendor_id`: optional — vendor record id (`lugal.supply.vendor`)  
  - `item_request_id`: optional — item request id  
  - `search`: optional — search in item name or negotiation reference

### What to implement

1. Add UI controls for **state**, **vendor**, and **item request** (same row or filter bar as search — follow the product mockup).
2. When any filter changes, reset to **page 1** and refetch the list.
3. Pass non-empty values through `negotiationList` using the existing filter shape (do not invent new param names).
4. Provide a **clear / reset filters** affordance consistent with the existing “Clear” behavior for search.
5. **Vendor and item request pickers:**
  - Reuse existing supply APIs if the app already lists vendors or item requests (e.g. vendor list used in PO screens).  
  - If there is no existing “item request list” call in this frontend, add a minimal integration: locate the correct endpoint in `supplyApi.ts` / `docs/NEW_SUPPLY_APIS_EN.md` or related supply docs, add a typed wrapper if missing, and use it to populate a select or searchable dropdown. Avoid hard-coded IDs.
6. Empty option should mean “no filter” (omit that key from the RPC payload — the `negotiationList` helper already omits unset fields).

### Acceptance criteria

- With backend data present, changing **state** narrows rows to that state only.
- Selecting a **vendor** narrows rows to negotiations for that vendor.
- Selecting an **item request** narrows rows for that request.
- Filters compose correctly with **search** and **pagination**.
- No regression to login, detail sheet, or comments.

---

## Issue 2 — Purchase Order creation

### Problem

*(Product-specific — attach the screenshot or paste the exact error from the 2nd image here.)*

**Example placeholders (replace with real observations):**

- Creating a PO fails with API error: `…`
- UI validation blocks submit incorrectly when: `…`
- Missing fields required by workflow: `…`

### Evidence in code

- **Create modal:** `frontends/44/src/features/supply/containers/PoContainer.tsx` — `CreatePoModal`  
  - Submits via `supplyApi.poCreate` with `name`, `vendor_customer_id`, optional `division`, and `lines`.
- **Client API:** `frontends/44/src/services/supplyApi.ts` — `poCreate`  
- **Types:** `frontends/44/src/types/supply.ts` — `PoCreateInput`
- **Backend:** `addons/lugal_crm/controllers/supply_chain_api_controller.py` — `supply_po_create`  
  - Resolves `vendor_customer_id` through `_vendor_from_partner_id`. If the partner is not linked to a supply vendor, API returns:  
  `**vendor_customer_id must reference a vendor-linked partner`**
  - Supports additional optional fields on create (examples): `currency_id`, `container_id`, `branch_id`, `item_request_id`, `negotiation_id`, dates, `notes`, etc. The current **Create** modal may not expose fields the business process requires—confirm against product spec and `docs/NEW_SUPPLY_APIS_EN.md` (PO create section).

### What to do

1. Reproduce the bug with the running app and capture the **network response** for `POST /api/crm/supply/po/create` (status + JSON `error` message).
2. Fix **frontend** validation, payload mapping, or missing fields so creation matches backend expectations and product design.
3. If the backend error is correct but UX is poor, improve **inline error display** and guardrails (e.g. disable submit, explain vendor must be a supply-linked vendor).
4. Verify TypeScript builds: `npm run build` (or project-equivalent) from `frontends/44/`.

### Acceptance criteria

- PO creation succeeds for the scenario shown in the product issue.
- User sees a clear message when the API rejects the request (show server `error` string when available).
- No regressions to PO list, edit, or status actions.

---

## General instructions for the agent

1. Read the files cited above before editing.
2. After changes, run the frontend **lint/build** command used in this package and fix any new issues.

---

## Attachments checklist for the human reviewer

- Issue 1: mockup or screenshot of the three filters (Negotiations).
- Issue 2: screenshot of PO create failure + browser Network tab response body for `po/create`.

When pasting into Cursor, drag those images into the chat or describe the exact error text so the agent does not guess.