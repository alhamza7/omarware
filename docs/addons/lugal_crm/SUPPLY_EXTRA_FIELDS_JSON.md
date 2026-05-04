# Supply chain dynamic fields (`extra_fields`)

English reference for the JSON **`extra_fields`** column on item requests, negotiations, and supply purchase orders.

## Models

| Model | Technical name |
|-------|----------------|
| Item request | `lugal.supply.item.request` |
| Negotiation | `lugal.supply.negotiation` |
| Supply order (PO) | `lugal.crm.supply.po` |

Implementation: abstract mixin **`lugal.supply.dynamic.extra.mixin`** (`addons/lugal_supply/models/lugal_supply_dynamic_extra_mixin.py`).

## Field

- **Name:** `extra_fields`
- **Type:** `fields.Json` (PostgreSQL `jsonb` in typical Odoo installs)
- **Default:** `{}`
- **Content:** One JSON **object** (key → value). Values must be **JSON-serializable** (string, number, boolean, null, array, nested object).

## Key rules

- Keys must match: start with a letter; then letters, digits, `_`, `.`, `-`; max **128** characters.
- Recommended: namespace FE keys, e.g. `fe.lineOfBusiness`, `portal.customLabel`.
- Do not store secrets (passwords, tokens) in plain JSON.

## Python API (server / server actions)

```python
record.set_dynamic_field('fe.priorityTag', 'urgent')
val = record.get_dynamic_field('fe.priorityTag', default=None)
record.merge_extra_fields({'fe.a': 1, 'fe.b': {'nested': True}})
clean = env['lugal.supply.item.request'].sanitize_extra_fields_input({'fe.x': 10})
```

## JSON-RPC (frontend)

Pass **`extra_fields`** in **`params`**:

- **Create:** full object is stored (after sanitization).
- **Update:** payload is **merged** into the existing object (existing keys not sent are kept).

Example:

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "item_name": "Serum 50ml",
    "extra_fields": {
      "fe.displaySku": "SR-50-GL",
      "fe.tags": ["showroom", "q2"]
    }
  },
  "id": 1
}
```

List/detail responses include **`extra_fields`** as a JSON object.

## UI

Form views include a **Custom fields** tab showing `extra_fields` (editable where the user has write access).

## Upgrade

After pulling code, upgrade modules so the column is created:

```text
-u lugal_supply,lugal_crm
```

## Alternative: attribute / value model (EAV-style)

Use a separate model, e.g. `lugal.supply.dynamic.attribute` (name, type, validation) and `lugal.supply.dynamic.value` (`res_model`, `res_id`, `attribute_id`, `value_text`, `value_float`, …).

| Approach | Pros | Cons |
|----------|------|------|
| **JSON `extra_fields`** | Few tables, fast to ship, easy for FE, good for unstructured data | Weak typing, limited reporting/SQL filters unless JSON operators |
| **EAV lines** | Typed fields, constraints, search domains, security per attribute | More models, migrations when adding attributes, more code |

**Practice:** start with **`extra_fields`** for FE-driven labels and flags; move critical, reportable attributes to **real fields** or to an **EAV** (or `ir.property`) when you need constraints, access rules, or heavy reporting.
