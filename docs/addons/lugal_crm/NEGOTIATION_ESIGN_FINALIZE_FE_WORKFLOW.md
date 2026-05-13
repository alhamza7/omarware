# Negotiation detail — E-sign approve vs Confirm / Finalize (FE bug fix handoff)

**Module:** Supply Chain → Negotiations  
**Audience:** Frontend (Cursor / SPA)  
**Language:** English only  

---

## 1. Issue summary

In the **negotiation details** modal (or sheet), when status is **`ongoing`**, two actions are shown:

- **E-sign approve**
- **Confirm / Finalize**

That initial state is correct.

**Bug:** After a successful **E-sign approve** request, **both** buttons disappear.

**Root cause (typical FE mistake):** The UI treats **“e-sign succeeded”** as equivalent to **“negotiation finalized”** (e.g. a single flag such as `esignApproved === finalized`, or hiding all action buttons whenever the first action completes).  

**Business rule:** E-sign approval and finalization are **two different** steps. Hiding **Confirm / Finalize** after e-sign only is incorrect while the negotiation should still be treated as **ongoing** from a workflow perspective.

---

## 2. Expected workflow (product)

### Step 1 — `ongoing`

When negotiation **`state`** is **`ongoing`** (or equivalent primary status from API):

| Control              | Visibility |
|----------------------|------------|
| **E-sign approve**   | Visible (and enabled if user may e-sign) |
| **Confirm / Finalize** | Visible (and enabled if user may finalize) |

Both may be shown at the same time.

### Step 2 — User clicks **E-sign approve**

- **API:** `POST /api/crm/supply/negotiations/<id>/e_sign_approve`  
  (JSON-RPC: standard envelope; params as per project integration guide.)

- **After success:**  
  - **Hide** the **E-sign approve** button **or** **disable** it (product choice).  
  - **Do not** hide **Confirm / Finalize** while the record is still in the **pre-finalize** phase of the workflow (negotiation not yet finalized in business terms).

So: **only** the e-sign control should be removed/disabled after e-sign; **Confirm / Finalize** must **remain** available until finalization actually happens.

### Step 3 — User clicks **Confirm / Finalize**

- **API:** `POST /api/crm/supply/negotiations/<id>/confirm`

- **After success:**  
  - Negotiation **`state`** becomes **`finalized`** (or whatever the API returns as terminal “done”).  
  - **Hide** **Confirm / Finalize** (and e-sign if still visible).  
  - Move the row to the **Finalized** list/tab/filter per product rules.

---

## 3. Correct FE state model (do not conflate actions)

Use **separate** concepts in code and UI:

| Concept | Meaning |
|---------|--------|
| `canShowEsign` | User may perform e-sign (role + workflow + not yet e-signed). |
| `canShowFinalize` | User may finalize (role + workflow + not yet finalized). |

**Wrong:**

```text
afterEsignSuccess → hideEverything
// or
esignApproved === finalized
```

**Right:**

```text
afterEsignSuccess → set eSignDone = true (or use server field) → hide/disable ONLY e-sign
afterFinalizeSuccess → set finalized → hide BOTH, update list/tab
```

Prefer driving visibility from **server-returned fields** after `negotiationGet` / successful mutation response, not only from optimistic local flags, unless the API does not yet expose e-sign completion (see section 5).

---

## 4. Suggested visibility rules (pseudocode)

After each successful action, **refresh** negotiation from **`POST .../negotiations/<id>/get`** (or use the mutation response body if it is the full negotiation object).

```text
const state = negotiation.state ?? negotiation.status; // align with API

const eSignDone = negotiation.<serverFieldForEsign>;   // see section 5
const isFinalized = state === 'finalized';

showEsignButton = !isFinalized && !eSignDone && <roleAllows>;
showFinalizeButton = !isFinalized && <roleAllows>;
// Optional: after backend exposes e-sign only, showFinalizeButton can stay true while state still 'ongoing' && eSignDone
```

**Empty state / errors:** On API error, do not flip flags that hide both buttons; show toast and keep prior visibility.

---

## 5. Backend alignment (read this before shipping)

**Current server behavior (verify in repo):** In `addons/lugal_crm/controllers/supply_extra_api_controller.py`, both:

- `POST /api/crm/supply/negotiations/<id>/e_sign_approve`
- `POST /api/crm/supply/negotiations/<id>/confirm`

call the same Odoo method **`action_finalize()`** on `lugal.supply.negotiation`, which sets **`state` = `finalized`**.

The negotiation model selection is **`ongoing` | `finalized` | `cancelled`** — there is **no** separate persisted “e-signed but not finalized” state in that model today.

**Implications:**

1. If the API already returns **`state: finalized`** immediately after **e_sign_approve**, then **by data alone** the negotiation is finalized; showing **Confirm / Finalize** again would be misleading unless the backend is changed.
2. To match the **product workflow** in sections 2–3 **fully**, the **backend** likely needs a distinct step (for example: a boolean `e_sign_approved`, or a dedicated sub-state), where:
   - **E-sign** route only records e-sign and keeps **`state: ongoing`**
   - **Confirm** route performs **`action_finalize()`** and sets **`state: finalized`**

**FE action items:**

- [ ] Confirm actual **`state`** / **`status`** values returned after **`e_sign_approve`** and after **`confirm`** in your environment (network tab + `negotiationGet`).
- [ ] If both endpoints return **`finalized`**, file a **backend** ticket to split behavior; adjust FE only after the API exposes a clear **“e-sign done, not finalized”** signal.
- [ ] Until backend supports two steps, FE should **not** simulate a second finalize if the server already finalized on the first call (avoid double submit / `UserError`).

---

## 6. API reference (negotiation)

| Action | Method | Route |
|--------|--------|--------|
| Refresh row | POST | `/api/crm/supply/negotiations/<id>/get` |
| E-sign approve | POST | `/api/crm/supply/negotiations/<id>/e_sign_approve` |
| Confirm / finalize | POST | `/api/crm/supply/negotiations/<id>/confirm` |

Use the same JSON-RPC and auth patterns as other Supply Chain routes (`Authorization: Bearer …`, `params` in body).

---

## 7. Acceptance criteria (FE)

- [ ] While negotiation is in the **ongoing** phase per API, **both** buttons can appear as required by product.
- [ ] After **successful e-sign only**, **E-sign approve** is hidden or disabled; **Confirm / Finalize** **remains** visible **if and only if** the server still reports a non-finalized negotiation (see section 5).
- [ ] After **successful finalize**, **Confirm / Finalize** is hidden; negotiation appears under **Finalized** where applicable.
- [ ] No shared boolean equates **e-sign success** with **finalized** unless the API explicitly defines that (today it may — verify).

---

## 8. Likely files to inspect (examples)

Paths depend on which app ships Negotiations UI; search the repo for:

- `e_sign_approve`, `e_sign`, `esign`, `finalize`, `negotiations/confirm`
- `NegotiationDetail`, `NegotiationModal`, `negotiationGet`

Example in this repo: `frontends/44/src/features/supply/containers/NegotiationContainer.tsx` (add actions + visibility there or in extracted components); extend `supplyApi.ts` if routes are missing.

---

## 9. Copy / labels (English)

- List or filter for completed negotiations: **Finalized**

---

*End of handoff document.*
