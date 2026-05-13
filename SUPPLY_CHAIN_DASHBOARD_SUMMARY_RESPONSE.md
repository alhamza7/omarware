# Supply Chain Dashboard Summary API — Implementation & Response

**Endpoint:** `POST /api/crm/supply/dashboard/summary`  
**Transport:** JSON-RPC (`type='jsonrpc'` on the route).  
**Auth:** `auth='none'`; handler calls `ensure_jwt_user_id()` (Bearer JWT or Odoo session).  
**Request body:** No parameters are read from `kwargs` for aggregation logic (empty `{}` is fine).

---

## 1. Controller and method

| Item | Value |
|------|--------|
| **File** | `addons/lugal_crm/controllers/supply_chain_api_controller.py` |
| **Class** | Controller class that contains `supply_po_list` / `supply_dashboard_summary` (same module as other `/api/crm/supply/*` chain routes). |
| **Method** | `supply_dashboard_summary(self, **kwargs)` |
| **Route decorator** | `@http.route('/api/crm/supply/dashboard/summary', type='jsonrpc', auth='none', csrf=False, methods=['POST'])` |

**Execution flow (high level)**

1. `ensure_jwt_user_id()` — if falsy → `{'success': False, 'error': 'Unauthorized', 'data': None}`.
2. Load model proxies (all `.sudo()`):  
   `ir.config_parameter`, `lugal.supply.item.request`, `lugal.supply.negotiation`, `lugal.crm.supply.po`, `lugal.supply.payment`, `lugal.supply.container`, `lugal.supply.workflow.approval.line`.
3. Define nested **`alive_domain(model)`** (local function):  
   - If model has `is_deleted` → append `('is_deleted', '=', False)`.  
   - If model has `active` → append `('active', '=', True)`.  
4. Build `item_dom`, `neg_dom`, `po_dom`, `pay_dom`, `cont_dom` by calling `alive_domain` for each respective model.
5. **Delayed receipt:** `confirmed_pos = Po.search(po_dom + [('status', '=', 'confirmed')])`.  
   If field `lead_time_delay_days` exists on `lugal.crm.supply.po`, set `delayed_receipt = sum(1 for p in confirmed_pos if (p.lead_time_delay_days or 0) > 0)`; else `0`.  
   (`lead_time_delay_days` is a computed field from `crm_supply_po_chain_enhance.py`, depending on `planned_receipt_date` and `status == 'confirmed'`.)
6. Build dict **`data`** with only `search_count` / Python `sum` (no other services or helpers called).
7. Return `{'success': True, 'data': data}`.
8. On exception: `crm_error(e, 'supply_dashboard_summary')` (same module pattern as other routes).

**Not used in this method:** `_pagination`, `_parse_date`, serializers, bus, mail.

---

## 2. Exact JSON-RPC `result` shape (success)

Odoo returns this object as **`result`** in the JSON-RPC envelope:

```json
{
  "success": true,
  "data": {
    "item_requests": {
      "draft": 0,
      "in_progress": 0,
      "completed": 0
    },
    "negotiations": {
      "ongoing": 0,
      "finalized": 0,
      "cancelled": 0
    },
    "purchase_orders": {
      "draft": 0,
      "confirmed": 0,
      "cancelled": 0,
      "delayed_receipt": 0
    },
    "payments": {
      "total": 0
    },
    "shipments": {
      "total": 0
    },
    "approvals": {
      "pending": 0
    },
    "config_flags": {
      "workflow_level_count": 0,
      "budget_control_enabled": false,
      "stock_validate_po": true,
      "workflow_activity_notify": true
    }
  }
}
```

All numeric counts are **integers** from `search_count` or from the `delayed_receipt` sum. Booleans in `config_flags` come from string comparison on `ir.config_parameter` values.

**Failure (unauthorized example):**

```json
{
  "success": false,
  "error": "Unauthorized",
  "data": null
}
```

**Full JSON-RPC envelope (conceptual):**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": { }
  }
}
```

The inner `result` matches the success/failure objects above.

---

## 3. `data` keys — calculation, model, domain, logic

### 3.1 `item_requests`

| Key | Calculation | Model | Domain / filters |
|-----|-------------|--------|------------------|
| `draft` | `Item.search_count(domain)` | `lugal.supply.item.request` | `item_dom` AND `('state', '=', 'draft')` |
| `in_progress` | `search_count` | same | `item_dom` AND `('state', '=', 'in_progress')` |
| `completed` | `search_count` | same | `item_dom` AND `('state', '=', 'completed')` |

**`item_dom`:** `('is_deleted', '=', False)` and `('active', '=', True)` (both fields exist on the model).

**Note:** Other `state` values are not counted (model selection is only draft / in_progress / completed).

---

### 3.2 `negotiations`

| Key | Calculation | Model | Domain / filters |
|-----|-------------|--------|------------------|
| `ongoing` | `Neg.search_count(domain)` | `lugal.supply.negotiation` | `neg_dom` AND `('state', '=', 'ongoing')` |
| `finalized` | `search_count` | same | `neg_dom` AND `('state', '=', 'finalized')` |
| `cancelled` | `search_count` | same | `neg_dom` AND `('state', '=', 'cancelled')` |

**`neg_dom`:** `is_deleted=False`, `active=True` when those fields exist.

---

### 3.3 `purchase_orders`

| Key | Calculation | Model | Domain / filters |
|-----|-------------|--------|------------------|
| `draft` | `Po.search_count(domain)` | `lugal.crm.supply.po` | `po_dom` AND `('status', '=', 'draft')` |
| `confirmed` | `search_count` | same | `po_dom` AND `('status', '=', 'confirmed')` |
| `cancelled` | `search_count` | same | `po_dom` AND `('status', '=', 'cancelled')` |
| `delayed_receipt` | **Not** `search_count`: Python `sum(1 for p in confirmed_pos if (p.lead_time_delay_days or 0) > 0)` | same PO model | `confirmed_pos = Po.search(po_dom + [('status', '=', 'confirmed')])` then in-memory filter on `lead_time_delay_days` **if** the field exists on the model; else `0` |

**`po_dom`:** `is_deleted=False`, `active=True`.

**Note:** PO `status` selection in code is only `draft` | `confirmed` | `cancelled` (legacy shipped/received were migrated to `confirmed` in model `init`). There is **no** separate count for suggested POs (`is_suggested`).

---

### 3.4 `payments`

| Key | Calculation | Model | Domain / filters |
|-----|-------------|--------|------------------|
| `total` | `Pay.search_count(pay_dom)` | `lugal.supply.payment` | `pay_dom` only |

**`pay_dom`:** This model has **`active`** but **no `is_deleted`** in `lugal_supply_payment.py`, so `alive_domain` only adds `('active', '=', True)`.

**Note:** No breakdown by `payment_type`, `payment_status`, currency, or sum of `amount`.

---

### 3.5 `shipments`

| Key | Calculation | Model | Domain / filters |
|-----|-------------|--------|------------------|
| `total` | `Cont.search_count(cont_dom)` | `lugal.supply.container` | `cont_dom` only |

**`cont_dom`:** `is_deleted=False`, `active=True`.

**Naming:** The API key is `shipments`, but the model is **`lugal.supply.container`** (containers used as shipment records in the product). There is **no** breakdown by `status` (`waiting` / `active` / `at_port` / `completed`) or `division`.

---

### 3.6 `approvals`

| Key | Calculation | Model | Domain / filters |
|-----|-------------|--------|------------------|
| `pending` | `Line.search_count([('state', '=', 'pending')])` | `lugal.supply.workflow.approval.line` | **Only** `state = pending` — **no** `alive_domain`, no filter on parent document existence or soft-delete |

So pending lines for archived/deleted parents may still be counted until DB cascades or records are cleaned up.

---

### 3.7 `config_flags`

| Key | Calculation | Source |
|-----|-------------|--------|
| `workflow_level_count` | `max(0, int(icp.get_param('lugal_supply.workflow_level_count', '0') or 0))` | `ir.config_parameter` key `lugal_supply.workflow_level_count` |
| `budget_control_enabled` | `icp.get_param('lugal_supply.budget_control_enabled', 'False') == 'True'` | `lugal_supply.budget_control_enabled` |
| `stock_validate_po` | `icp.get_param('lugal_supply.stock_validate_po', 'True') == 'True'` | `lugal_supply.stock_validate_po` |
| `workflow_activity_notify` | `icp.get_param('lugal_supply.workflow_activity_notify', 'True') == 'True'` | `lugal_supply.workflow_activity_notify` |

These mirror settings in `addons/lugal_crm/models/supply_workflow_config.py` (`ResConfigSettings` / helpers).

---

## 4. Frontend dashboard use (by key)

| Area | Useful for |
|------|------------|
| `item_requests.*` | Pipeline cards: draft vs in progress vs completed. |
| `negotiations.*` | Negotiation workload / funnel cards. |
| `purchase_orders.draft|confirmed|cancelled` | PO pipeline KPIs. |
| `purchase_orders.delayed_receipt` | Alert / red badge when &gt; 0 (late vs planned receipt on confirmed POs). |
| `payments.total` | Simple “number of payment records” only — **not** monetary KPI without extra API. |
| `shipments.total` | Total active containers — **not** in-transit vs completed without extra breakdown. |
| `approvals.pending` | “Action required” badge for workflow (subject to caveat on orphan lines). |
| `config_flags.*` | Feature toggles in UI (show/hide budget check, stock validation, activity creation, number of approval levels). |

---

## 5. Metrics that exist in the codebase but are **not** in this response

These could extend the same endpoint or separate widgets:

| Topic | Exists elsewhere | Not in `dashboard/summary` |
|-------|------------------|----------------------------|
| **PO `is_suggested`** | Field on `lugal.crm.supply.po` | No count of suggested / reorder POs |
| **PO by `division`** | `po/list` supports `division` filter | No per-division PO counts |
| **Container `status`** | `waiting` / `active` / `at_port` / `completed` on `lugal.supply.container` | Only `shipments.total` |
| **Container `division`** | `europe` / `china` on container | Not aggregated |
| **Payment `payment_type` / `payment_status`** | Selection + computed `payment_status` on `lugal.supply.payment` | Only total row count |
| **Payment sums** | `amount`, `currency_id` on payments | No `sum(amount)` or per-currency totals |
| **Approval lines** | States `approved`, `rejected`, `skipped` on `lugal.supply.workflow.approval.line` | Only `pending` count |
| **Item request total** | Could derive sum of three states | No single `total` field |
| **Negotiation total** | Same | No single `total` |
| **Vendor / container list metrics** | Various list APIs | No vendor counts |
| **Notifications** | `supply_extra_api_controller` notifications list | Not linked |
| **Item requests not in draft/in_progress/completed** | N/A if DB clean | Any legacy state would be invisible |

---

## 6. Code reference

Implementation span (for review in IDE):

```1040:1108:addons/lugal_crm/controllers/supply_chain_api_controller.py
    @http.route('/api/crm/supply/dashboard/summary', type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def supply_dashboard_summary(self, **kwargs):
        """Aggregate counts for supply dashboard (extends metrics without replacing existing list APIs)."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': None}
            icp = request.env['ir.config_parameter'].sudo()
            Item = request.env['lugal.supply.item.request'].sudo()
            Neg = request.env['lugal.supply.negotiation'].sudo()
            Po = request.env['lugal.crm.supply.po'].sudo()
            Pay = request.env['lugal.supply.payment'].sudo()
            Cont = request.env['lugal.supply.container'].sudo()
            Line = request.env['lugal.supply.workflow.approval.line'].sudo()

            def alive_domain(model):
                dom = []
                if 'is_deleted' in model._fields:
                    dom.append(('is_deleted', '=', False))
                if 'active' in model._fields:
                    dom.append(('active', '=', True))
                return dom

            item_dom = alive_domain(Item)
            neg_dom = alive_domain(Neg)
            po_dom = alive_domain(Po)
            pay_dom = alive_domain(Pay)
            cont_dom = alive_domain(Cont)

            confirmed_pos = Po.search(po_dom + [('status', '=', 'confirmed')])
            delayed_receipt = 0
            if 'lead_time_delay_days' in Po._fields:
                delayed_receipt = sum(1 for p in confirmed_pos if (p.lead_time_delay_days or 0) > 0)

            data = {
                'item_requests': {
                    'draft': Item.search_count(item_dom + [('state', '=', 'draft')]),
                    'in_progress': Item.search_count(item_dom + [('state', '=', 'in_progress')]),
                    'completed': Item.search_count(item_dom + [('state', '=', 'completed')]),
                },
                'negotiations': {
                    'ongoing': Neg.search_count(neg_dom + [('state', '=', 'ongoing')]),
                    'finalized': Neg.search_count(neg_dom + [('state', '=', 'finalized')]),
                    'cancelled': Neg.search_count(neg_dom + [('state', '=', 'cancelled')]),
                },
                'purchase_orders': {
                    'draft': Po.search_count(po_dom + [('status', '=', 'draft')]),
                    'confirmed': Po.search_count(po_dom + [('status', '=', 'confirmed')]),
                    'cancelled': Po.search_count(po_dom + [('status', '=', 'cancelled')]),
                    'delayed_receipt': delayed_receipt,
                },
                'payments': {
                    'total': Pay.search_count(pay_dom),
                },
                'shipments': {
                    'total': Cont.search_count(cont_dom),
                },
                'approvals': {
                    'pending': Line.search_count([('state', '=', 'pending')]),
                },
                'config_flags': {
                    'workflow_level_count': max(0, int(icp.get_param('lugal_supply.workflow_level_count', '0') or 0)),
                    'budget_control_enabled': icp.get_param('lugal_supply.budget_control_enabled', 'False') == 'True',
                    'stock_validate_po': icp.get_param('lugal_supply.stock_validate_po', 'True') == 'True',
                    'workflow_activity_notify': icp.get_param('lugal_supply.workflow_activity_notify', 'True') == 'True',
                },
            }
            return {'success': True, 'data': data}
        except Exception as e:
            return crm_error(e, 'supply_dashboard_summary')
```

---

*End of report.*
