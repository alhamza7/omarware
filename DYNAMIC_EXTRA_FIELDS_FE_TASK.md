# Supply Chain Dynamic Extra Fields — Frontend Task

This document defines the frontend work required to integrate **dynamic custom fields** (`extra_fields`) across Supply Chain surfaces. Use the backend reference **`docs/addons/lugal_crm/SUPPLY_EXTRA_FIELDS_JSON.md`** (and the mixin **`lugal.supply.dynamic.extra.mixin`**) as the authoritative description of models, JSON shape, key rules, and JSON-RPC behavior.

---

## Issue

The backend persists and exposes **`extra_fields`** (a JSON object: string keys → JSON-serializable values) on selected models. List/detail responses include **`extra_fields`**, and create/update routes accept it (create stores a sanitized object; update **merges** new keys into the existing object). The frontend does not yet expose a clear, visible **Custom Fields** experience, so users cannot manage these values from the app.

---

## Backend reference (summary)

| Model | Technical name |
|-------|----------------|
| Item request | `lugal.supply.item.request` |
| Negotiation | `lugal.supply.negotiation` |
| Supply purchase order | `lugal.crm.supply.po` |

- **Create:** send a full **`extra_fields`** object (after sanitization on the server).
- **Update:** send **`extra_fields`** as a **merge** payload; keys omitted are not removed by merge (see backend docs for deletion semantics if any).
- **Responses:** **`extra_fields`** is included where the field exists on the model.

Concrete route names and parameters are implemented in **`addons/lugal_crm/controllers/supply_extra_api_controller.py`** and **`addons/lugal_crm/controllers/supply_chain_api_controller.py`** (PO). Verify paths and `params` against those controllers and the integration guide when implementing.

---

## Modules to cover

1. **Item Requests** — forms/modals and detail views for `lugal.supply.item.request`.
2. **Negotiations** — forms/modals and detail views for `lugal.supply.negotiation`.
3. **Purchase Orders** — forms/modals and detail views for `lugal.crm.supply.po`.

---

## Requirements

### Audit

- Confirm whether the client already **reads** `extra_fields` from list/get responses (types, parsing, defaults).
- Confirm whether **create** and **update** calls include `extra_fields` in `params` when appropriate.
- Identify any hidden, incomplete, or dead UI related to custom fields.

### API integration

- **Create:** send the full object, for example:

  ```json
  { "extra_fields": { "fe.displaySku": "SR-50-GL" } }
  ```

- **Update:** send a merge payload (only the keys being set or changed in that request), for example:

  ```json
  { "extra_fields": { "fe.priorityTag": "urgent" } }
  ```

  Align with product expectations: if the UX edits “all visible rows,” the implementation may send one object containing every key currently shown in the form; the server still merges that object into the stored JSON.

### UI — all three modules

- Add a clearly visible tab (or equivalent primary navigation within the screen) labeled **Custom Fields**.
- Inside that tab:
  - Button: **Add Custom Field**.
  - Allow the user to define **key** and **value** (inputs plus confirm/add action).
  - Render existing and newly added entries as **editable rows** (edit in place or inline).
  - Allow **remove** before submit (and define behavior on update if removal must clear a key on the server — confirm with backend if not documented).

### Display

- In **detail** and **edit** flows, if the record already has `extra_fields`, show every key-value pair in the Custom Fields tab (read-only where the record is not editable).

### Validation (client-side)

- **Key** required; trim; reject empty keys.
- **Value** required per product rule (if empty string is invalid, block submit).
- **Duplicate keys** forbidden in the same form.
- Respect backend key pattern rules (see **`SUPPLY_EXTRA_FIELDS_JSON.md`**: length, allowed characters). Surface friendly English errors.

### UX

- Clean table or list layout consistent with the rest of the Supply Chain UI.
- **Empty state** copy: `No custom fields added`.

---

## Acceptance criteria

- **Custom Fields** tab (or equivalent) is visible and reachable in **Item Requests**, **Negotiations**, and **Purchase Orders**.
- **Add Custom Field** control is visible where users add or edit records.
- **Create** and **update** requests include `extra_fields` when the user has defined custom fields (and omit or send `{}` per agreed contract when none).
- **Existing** `extra_fields` from the API render correctly in detail/edit views.
- No hidden-only or non-functional custom-field UI remains undocumented.

---

## Deliverable

Complete the implementation checklist above, then fill in **`DYNAMIC_EXTRA_FIELDS_FE_REPORT_TEMPLATE.md`** with concrete file paths, API verification notes, and any follow-ups.

---

## Out of scope (unless product expands)

- Defining new server-side attributes or EAV models; this task is **JSON `extra_fields`** only.
- Non–Supply Chain modules.
