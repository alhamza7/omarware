# Cursor agent prompt: Negotiations status filters & Purchase Order create error

**How to use:** Open the correct frontend workspace in Cursor, create a new agent chat, and paste the entire **“Agent instructions”** block below (from the horizontal rule through the end of that section). Adjust file paths if your app lives outside the paths listed under **Codebase hints**.

---

## Agent instructions

You are working on our Supply Chain frontend. Complete the following two tasks. Prefer minimal, focused changes; match existing patterns (components, styling, API layer).

### Task 1 — Negotiations: add three status filters (pending UI)

**Goal:** The Negotiations list view must let users filter negotiations by lifecycle state. The backend filter parameter uses **stored values**; the UI must show **human-readable labels**.

**State → label mapping (use exactly these stored values in API requests):**


| Stored value (`state`) | UI label  |
| ---------------------- | --------- |
| `ongoing`              | Ongoing   |
| `finalized`            | Finalized |
| `cancelled`            | Cancelled |


**Requirements:**

1. Add filter controls on the Negotiations screen (e.g. next to the existing search bar): either a single select / segmented control / three toggle chips — whichever fits the existing design system. “All” (no filter) must remain the default.
2. When the user selects a status, refetch the list with the corresponding `state` value. Reset pagination to page 1 when the filter changes.
3. Ensure the value sent to the API is the **stored value** (`ongoing`, `finalized`, `cancelled`), not the display label.
4. If the list API client already accepts a `state` field, wire it through instead of reimplementing RPC.

**Acceptance criteria:**

- With no filter selected, behavior matches today (all statuses, subject to other existing params).
- Selecting each of the three options returns only negotiations in that state (verify in Network tab: request body includes `state: "<value>"`).
- Labels in the UI read “Ongoing”, “Finalized”, “Cancelled”.

**Optional hardening (if the screen exposes “finalize” / e-sign / approve):** The backend may return `success: false` with an error such as `Only ongoing negotiations can be finalized.` for `e_sign_approve`. Disable or hide that action unless the negotiation is `ongoing`, and surface the server error in the UI if it still occurs.

---

### Task 2 — Purchase Order creation: fix `_config.signal.addEventListener is not a function`

**Observed behavior:** Saving a new purchase order shows a toast like:  
`Failed to create purchase order: _config.signal.addEventListener is not a function`  
Product search (`GET /api/products/search?...`) may still return 200; the failure is likely on the **create** request path (Axios/fetch wrapper).

**Likely cause:** The HTTP client (often **Axios v1**) expects `config.signal` to be a real **[AbortSignal](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal)**. Something is passing a non-signal object (e.g. a plain object, `undefined` coerced incorrectly, or a custom “signal” field from another library) into `signal`, so internal code calls `.addEventListener` on the wrong type.

**What to do:**

1. Locate the code path for **create purchase order** (submit handler → service → HTTP client).
2. Inspect every request option passed to Axios (or the shared API wrapper): find `signal`, `cancelToken`, or any interceptor that sets `signal`.
3. Fix by one or more of:
  - Pass `signal: abortController.signal` from a real `AbortController` when cancellation is needed, or **omit** `signal` entirely if not needed.
  - Remove or correct any spread that accidentally puts a non-signal field into Axios config under the name `signal`.
  - If using a wrapper, ensure you are not renaming unrelated props (e.g. passing `{ signal: someConfigObject }`).
4. Align **Axios** and **TypeScript** types if the project recently upgraded Axios; confirm no duplicate or incompatible client versions in `node_modules`.
5. After the fix, verify in DevTools: **Save purchase order** issues a successful create request and the UI updates (or shows a proper business validation error from the server, not a client TypeError).

**Acceptance criteria:**

- No `_config.signal.addEventListener` error when saving a valid PO.
- Invalid server responses still show readable error messages from `error.response` / your existing error mapper, not raw stack traces.

---

### Codebase hints (this repository)

Use these as starting points if they exist in your checkout; if your deployed app is a fork, search for equivalents.

- **Negotiations (table-style UI):** `frontends/44/src/features/supply/containers/NegotiationContainer.tsx` — today calls `supplyApi.negotiationList({ page, per_page, search })`; extend with `state` when a filter is selected.
- **API layer:** `frontends/44/src/services/supplyApi.ts` — `negotiationList` already forwards `filter.state` to `/api/crm/supply/negotiations/list`.
- **Types:** `frontends/44/src/types/supply.ts` — `NegotiationListFilter` includes optional `state?: string`.
- **Alternate / demo Negotiations UI (cards, mock data):** `addons/lugal_crm/NBS CRM (16)/src/app/components/supply-chain/sc-negotiations.tsx` — may need real API + filters if that is the target app.
- **PO services (JSON-RPC style):** `addons/lugal_crm/NBS CRM (16)/src/features/supply-chain/services/supplyService.ts` uses `apiPost` / `fetch`; if your failing app uses Axios for `/api/products/search` or PO create, search that frontend for `axios` and `createPurchaseOrder` / `po/create`.

Deliver **small commits** or a short summary of files touched and how you verified each acceptance criterion.

---

## End of agent instructions