# Purchase Order API — Complete Reference
**Version:** 1.0 | **Base URL:** `/api/crm/supply` | **Protocol:** JSON-RPC 2.0

---

## Table of Contents

1. [Authentication](#authentication)
2. [Request Format](#request-format)
3. [Response Format](#response-format)
4. [PO Status Flow](#po-status-flow)
5. [Endpoints](#endpoints)
   - [List POs](#1-list-purchase-orders)
   - [Get PO](#2-get-single-purchase-order)
   - [Create PO](#3-create-purchase-order)
   - [Update PO](#4-update-purchase-order)
   - [Delete PO](#5-delete-purchase-order)
   - [Confirm PO](#6-confirm-po)
   - [Mark Shipped](#7-mark-po-shipped)
   - [Mark Received](#8-mark-po-received)
   - [Cancel PO](#9-cancel-po)
   - [Reopen PO](#10-reopen-po)
   - [Add Line](#11-add-po-line)
   - [Update Line](#12-update-po-line)
   - [Delete Line](#13-delete-po-line)
   - [Upload Attachment](#14-upload-attachment)
   - [List Attachments](#15-list-attachments)
   - [Delete Attachment](#16-delete-attachment)
   - [List Comments](#17-list-comments)
   - [Add Comment](#18-add-comment)
   - [Delete Comment](#19-delete-comment)
   - [Add Penalty (Container)](#20-add-container-penalty)
   - [List Penalties (Container)](#21-list-container-penalties)
   - [Delete Penalty (Container)](#22-delete-container-penalty)
   - [Assign Driver (Container)](#23-assign-container-driver)
   - [Unassign Driver (Container)](#24-unassign-container-driver)
6. [Object Schemas](#object-schemas)
7. [Enums](#enums)
8. [Error Reference](#error-reference)

---

## Authentication

All endpoints require a **JWT Bearer token** obtained from the login endpoint.

### Login

```
POST /lugal/auth/login
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "username": "admin",
    "password": "admin"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": null,
  "result": {
    "success": true,
    "data": {
      "access_token":  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "user_id":       2,
      "name":          "Admin"
    }
  }
}
```

Pass the `access_token` in every subsequent request:

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## Request Format

Every request body must be valid **JSON-RPC 2.0**:

```json
{
  "jsonrpc": "2.0",
  "id":      1,
  "method":  "call",
  "params":  { ...endpoint-specific fields... }
}
```

> All endpoints accept **POST** only. Sending GET returns **405 Method Not Allowed**.  
> Missing `Content-Type: application/json` returns **415 Unsupported Media Type**.

---

## Response Format

### Success

```json
{
  "jsonrpc": "2.0",
  "id":      1,
  "result": {
    "success": true,
    "data":    { ...payload... }
  }
}
```

### Error

```json
{
  "jsonrpc": "2.0",
  "id":      1,
  "result": {
    "success": false,
    "error":   "Error description",
    "code":    400
  }
}
```

---

## PO Status Flow

```
         ┌──────────┐
         │  draft   │◄────────────────── reopen ──────────────────┐
         └────┬─────┘                                              │
              │ confirm                                            │
              ▼                                                    │
         ┌──────────┐                                             │
         │confirmed │                                             │
         └────┬─────┘                                             │
              │ ship                                              │
              ▼                                                   │
         ┌──────────┐                                            │
         │ shipped  │                                            │
         └────┬─────┘                                           │
              │ receive                                         │
              ▼                                                 │
         ┌──────────┐       cancel        ┌───────────┐        │
         │ received │ ───────────────────►│ cancelled │────────┘
         └──────────┘ (not cancellable)   └───────────┘
```

| Transition | From Status | Endpoint |
|---|---|---|
| Confirm | `draft` | `/po/{id}/confirm` |
| Mark Shipped | `confirmed` | `/po/{id}/ship` |
| Mark Received | `shipped` | `/po/{id}/receive` |
| Cancel | `draft`, `confirmed`, `shipped` | `/po/{id}/cancel` |
| Reopen | `cancelled` | `/po/{id}/reopen` |

---

## Endpoints

---

### 1. List Purchase Orders

```
POST /api/crm/supply/po/list
```

Retrieve a paginated list of purchase orders with optional filters.

**Params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `page` | int | No | Page number (default: 1) |
| `per_page` | int | No | Items per page (default: 20, max: 100) |
| `status` | string | No | Filter by status: `draft`, `confirmed`, `shipped`, `received`, `cancelled` |
| `search` | string | No | Search in PO name or vendor name |
| `vendor_customer_id` | int | No | Filter by vendor/contact ID |
| `division` | string | No | Filter by division: `europe`, `china` |

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {
    "page":     1,
    "per_page": 20,
    "status":   "draft",
    "search":   "Armani"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": {
      "total":    45,
      "page":     1,
      "per_page": 20,
      "items": [
        {
          "id":                    18,
          "name":                  "PO-2026-04-04-1775310328134",
          "vendor_customer_id":    1913,
          "vendor_customer_name":  "Armani Beauty EU",
          "vendor_customer_phone": "+39-02-1234",
          "vendor_id":             null,
          "vendor_name":           "Armani Beauty EU",
          "division":              "europe",
          "currency_id":           null,
          "currency_name":         "",
          "container_id":          null,
          "container_name":        "",
          "branch_id":             null,
          "branch_name":           "",
          "status":                "draft",
          "status_label":          "Draft / مسودة",
          "is_suggested":          false,
          "line_count":            3,
          "total_amount":          1500.00,
          "created_by_id":         2,
          "created_by_name":       "Admin",
          "created_at":            "2026-04-04T13:45:29",
          "updated_at":            "2026-04-04T13:45:29",
          "lines": [
            {
              "id":                  101,
              "sequence":            10,
              "product_name":        "Acqua di Gio 100ml",
              "item_code":           "ADG-100",
              "uom":                 "pcs",
              "quantity":            50,
              "unit_price":          20.00,
              "total_price":         1000.00,
              "currency_id":         null,
              "currency_name":       "",
              "last_purchase_price": 0,
              "last_purchase_date":  null,
              "min_qty":             0,
              "max_qty":             0
            }
          ]
        }
      ]
    }
  }
}
```

---

### 2. Get Single Purchase Order

```
POST /api/crm/supply/po/{id}/get
```

Retrieve full details of a single PO including all lines.

**URL Params:** `id` (int) — PO ID

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {}
}
```

**Response:** Same as a single item in the list, always includes `lines` array.

---

### 3. Create Purchase Order

```
POST /api/crm/supply/po/create
```

Create a new PO in `draft` status, optionally with line items.

**Params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | PO reference (e.g. `PO-2026-001`) |
| `vendor_customer_id` | int | Recommended | ID from `/api/crm/supply/vendors/list` |
| `vendor_id` | int | Legacy | Old vendor ID (use `vendor_customer_id` instead) |
| `division` | string | No | `europe` or `china` |
| `currency_id` | int | No | `res.currency` ID |
| `container_id` | int | No | Link to a container |
| `branch_id` | int | No | Link to a branch |
| `lines` | array | No | Line items to create with the PO |

**Line item object:**

| Field | Type | Required | Description |
|---|---|---|---|
| `product_name` | string | No | Product description |
| `item_code` | string | No | SKU / item code |
| `uom` | string | No | Unit of measure (e.g. `pcs`, `kg`) |
| `quantity` | float | Yes | Order quantity |
| `unit_price` | float | Yes | Price per unit |
| `min_qty` | float | No | Minimum reorder quantity |
| `max_qty` | float | No | Maximum reorder quantity |
| `currency_id` | int | No | Line-level currency |

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {
    "name":               "PO-2026-001",
    "vendor_customer_id": 1913,
    "division":           "europe",
    "lines": [
      {
        "product_name": "Acqua di Gio 100ml",
        "item_code":    "ADG-100",
        "uom":          "pcs",
        "quantity":     50,
        "unit_price":   20.00
      },
      {
        "product_name": "Acqua di Gio 50ml",
        "item_code":    "ADG-050",
        "uom":          "pcs",
        "quantity":     100,
        "unit_price":   12.50
      }
    ]
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": {
      "id":                   18,
      "name":                 "PO-2026-001",
      "vendor_customer_id":   1913,
      "vendor_customer_name": "Armani Beauty EU",
      "status":               "draft",
      "status_label":         "Draft / مسودة",
      "line_count":           2,
      "total_amount":         2250.00,
      "lines":                [ ...line objects... ]
    }
  }
}
```

---

### 4. Update Purchase Order

```
POST /api/crm/supply/po/{id}/update
```

Update header fields of an existing PO. Lines must be managed individually via the line endpoints.

**Allowed fields:**

| Field | Type | Description |
|---|---|---|
| `name` | string | PO reference |
| `division` | string | `europe` or `china` |
| `container_id` | int | Link/change container |
| `branch_id` | int | Link/change branch |
| `currency_id` | int | Currency |
| `is_suggested` | bool | Flag as suggested PO |
| `vendor_customer_id` | int | Change vendor |

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {
    "division":     "china",
    "container_id": 5
  }
}
```

**Response:** Updated PO object.

---

### 5. Delete Purchase Order

```
POST /api/crm/supply/po/{id}/delete
```

Permanently delete a PO. **Only allowed for `draft` or `cancelled` status.**

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {}
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "id":      18,
      "deleted": true
    }
  }
}
```

**Error (wrong status):**
```json
{
  "result": {
    "success": false,
    "error":   "Cannot delete a PO with status 'confirmed'. Cancel it first.",
    "code":    400
  }
}
```

---

### 6. Confirm PO

```
POST /api/crm/supply/po/{id}/confirm
```

Transition PO from `draft` → `confirmed`. Requires at least one line item.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {}
}
```

**Response:** Updated PO object with `"status": "confirmed"`.

---

### 7. Mark PO Shipped

```
POST /api/crm/supply/po/{id}/ship
```

Transition PO from `confirmed` → `shipped`.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {}
}
```

**Response:** Updated PO object with `"status": "shipped"`.

---

### 8. Mark PO Received

```
POST /api/crm/supply/po/{id}/receive
```

Transition PO from `shipped` → `received`. After this, **lines cannot be modified**.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {}
}
```

**Response:** Updated PO object with `"status": "received"`.

---

### 9. Cancel PO

```
POST /api/crm/supply/po/{id}/cancel
```

Cancel a PO that is in `draft`, `confirmed`, or `shipped` status.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {}
}
```

**Response:** Updated PO object with `"status": "cancelled"`.

---

### 10. Reopen PO

```
POST /api/crm/supply/po/{id}/reopen
```

Reopen a `cancelled` PO back to `draft`.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {}
}
```

**Response:** Updated PO object with `"status": "draft"`.

---

### 11. Add PO Line

```
POST /api/crm/supply/po/{id}/lines/add
```

Add a single line item to an existing PO. **Not allowed if status is `received`.**

**Params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `product_name` | string | No | Product description |
| `item_code` | string | No | SKU / item code |
| `uom` | string | No | Unit of measure |
| `quantity` | float | Yes | Order quantity |
| `unit_price` | float | Yes | Price per unit |
| `min_qty` | float | No | Min reorder qty |
| `max_qty` | float | No | Max reorder qty |
| `currency_id` | int | No | Line-level currency |

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {
    "product_name": "Armani Code 75ml",
    "item_code":    "AC-075",
    "uom":          "pcs",
    "quantity":     30,
    "unit_price":   35.00
  }
}
```

**Response:** The newly created line object.

---

### 12. Update PO Line

```
POST /api/crm/supply/po/{po_id}/lines/{line_id}/update
```

Update fields on an existing line. **Not allowed if PO status is `received`.**

**Params:** Same fields as Add Line (all optional).

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {
    "quantity":   50,
    "unit_price": 32.00
  }
}
```

**Response:** The updated line object.

---

### 13. Delete PO Line

```
POST /api/crm/supply/po/{po_id}/lines/{line_id}/delete
```

Remove a line from a PO. **Not allowed if PO status is `received`.**

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {}
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "id":      101,
      "deleted": true
    }
  }
}
```

---

### 14. Upload Attachment

```
POST /api/crm/supply/po/{id}/attachments/upload
```

Upload a file and attach it to the PO. Uses **multipart/form-data** (not JSON-RPC).

**Headers:**
```
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Form Fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | Yes | The file to upload (PDF, images, Office) |
| `label` | string | No | Display name override |

**Example (curl):**
```bash
curl -X POST http://localhost:8070/api/crm/supply/po/18/attachments/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@invoice.pdf" \
  -F "label=Supplier Invoice"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "attachments": [
      {
        "id":               55,
        "name":             "invoice.pdf",
        "mimetype":         "application/pdf",
        "size":             204800,
        "url":              "/web/content/55?download=true",
        "uploaded_by_name": "Admin",
        "created_at":       "2026-04-04T14:30:00"
      }
    ]
  }
}
```

---

### 15. List Attachments

```
POST /api/crm/supply/po/{id}/attachments/list
```

List all attachments for a PO.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {}
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "po_id":       18,
      "po_name":     "PO-2026-001",
      "total":       2,
      "attachments": [ ...attachment objects... ]
    }
  }
}
```

---

### 16. Delete Attachment

```
POST /api/crm/supply/po/{po_id}/attachments/{att_id}/delete
```

Permanently delete an attachment from a PO.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {}
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": { "deleted_id": 55 }
  }
}
```

---

### 17. List Comments

```
POST /api/crm/supply/po/{id}/comments/list
```

Retrieve comments and internal notes on a PO.

**Params:**

| Field | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": { "page": 1 }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 3,
      "items": [
        {
          "id":          201,
          "body":        "Vendor confirmed shipment for next week.",
          "type":        "comment",
          "author_id":   2,
          "author_name": "Admin",
          "created_at":  "2026-04-04T12:00:00"
        },
        {
          "id":          200,
          "body":        "Check pricing before confirming.",
          "type":        "note",
          "author_id":   2,
          "author_name": "Admin",
          "created_at":  "2026-04-03T10:30:00"
        }
      ]
    }
  }
}
```

---

### 18. Add Comment

```
POST /api/crm/supply/po/{id}/comments/add
```

Post a comment or internal note on a PO.

**Params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `body` | string | Yes | Comment text (plain text or HTML) |
| `is_note` | bool | No | `true` = internal note (default: `false`) |

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {
    "body":    "Vendor confirmed delivery date: April 15.",
    "is_note": false
  }
}
```

**Response:** The created comment object.

---

### 19. Delete Comment

```
POST /api/crm/supply/po/{po_id}/comments/{msg_id}/delete
```

Delete a comment from a PO.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {}
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": { "id": 201 }
  }
}
```

---

## Container Endpoints

---

### 20. Add Container Penalty

```
POST /api/crm/supply/containers/{id}/add_penalty
```

Record a financial penalty against a container (storage fees, damage, customs fines, etc.).

**Params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `penalty_type` | string | Yes | See [Penalty Types](#penalty-types) |
| `amount` | float | Yes | Monetary value (must be >= 0) |
| `reason` | string | No | Free-text explanation |
| `penalty_date` | string | No | `YYYY-MM-DD` (defaults to today) |
| `currency_id` | int | No | `res.currency` ID |

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {
    "penalty_type":  "storage",
    "amount":        500.00,
    "reason":        "30-day storage at Umm Qasr port",
    "penalty_date":  "2026-04-04"
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "id":              1,
      "container_id":    2,
      "container_name":  "GLS15152",
      "penalty_type":    "storage",
      "amount":          500.00,
      "currency_id":     null,
      "currency_name":   "",
      "reason":          "30-day storage at Umm Qasr port",
      "penalty_date":    "2026-04-04",
      "created_by_name": "Admin",
      "created_at":      "2026-04-04T14:30:00"
    }
  }
}
```

---

### 21. List Container Penalties

```
POST /api/crm/supply/containers/{id}/penalties/list
```

Retrieve all penalties for a container, ordered by date descending.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {}
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "container_id":   2,
      "container_name": "GLS15152",
      "total":          2,
      "total_amount":   700.00,
      "items": [
        {
          "id":              2,
          "penalty_type":    "damage",
          "amount":          200.00,
          "currency_id":     null,
          "currency_name":   "",
          "reason":          "Water damage on arrival",
          "penalty_date":    "2026-04-04",
          "created_by_name": "Admin",
          "created_at":      "2026-04-04T14:35:00"
        },
        {
          "id":              1,
          "penalty_type":    "storage",
          "amount":          500.00,
          "currency_id":     null,
          "currency_name":   "",
          "reason":          "30-day storage at Umm Qasr port",
          "penalty_date":    "2026-04-04",
          "created_by_name": "Admin",
          "created_at":      "2026-04-04T14:30:00"
        }
      ]
    }
  }
}
```

---

### 22. Delete Container Penalty

```
POST /api/crm/supply/containers/{container_id}/penalties/{penalty_id}/delete
```

Permanently remove a penalty record.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {}
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "deleted_id":   1,
      "container_id": 2
    }
  }
}
```

---

### 23. Assign Container Driver

```
POST /api/crm/supply/containers/{id}/assign_driver
```

Assign a driver to deliver the container. Accepts **two modes**:

**Mode A — By existing partner ID:**

| Field | Type | Required | Description |
|---|---|---|---|
| `driver_id` | int | Yes | `res.partner` ID |

**Mode B — By name/phone (find or create):**

| Field | Type | Required | Description |
|---|---|---|---|
| `driver_name` | string | Yes | Full name of the driver |
| `driver_phone` | string | No | Phone number |

**Request (Mode B):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {
    "driver_name":  "Mukesh Dandia",
    "driver_phone": "7006818907"
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "container_id":       2,
      "container_name":     "GLS15152",
      "driver_id":          1917,
      "driver_name":        "Mukesh Dandia",
      "driver_phone":       "7006818907",
      "driver_mobile":      "",
      "driver_assigned_at": "2026-04-04T14:27:52",
      "driver_assigned_by": "Admin"
    }
  }
}
```

---

### 24. Unassign Container Driver

```
POST /api/crm/supply/containers/{id}/unassign_driver
```

Remove the driver assignment from a container.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {}
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "container_id":   2,
      "container_name": "GLS15152",
      "driver_cleared": true
    }
  }
}
```

---

## Object Schemas

### Purchase Order Object

```json
{
  "id":                    18,
  "name":                  "PO-2026-001",
  "vendor_customer_id":    1913,
  "vendor_customer_name":  "Armani Beauty EU",
  "vendor_customer_phone": "+39-02-1234",
  "vendor_id":             null,
  "vendor_name":           "Armani Beauty EU",
  "division":              "europe",
  "currency_id":           null,
  "currency_name":         "",
  "container_id":          null,
  "container_name":        "",
  "branch_id":             null,
  "branch_name":           "",
  "status":                "draft",
  "status_label":          "Draft / مسودة",
  "is_suggested":          false,
  "line_count":            2,
  "total_amount":          2250.00,
  "created_by_id":         2,
  "created_by_name":       "Admin",
  "created_at":            "2026-04-04T13:45:29",
  "updated_at":            "2026-04-04T13:45:29",
  "lines":                 [ ...PO Line objects... ]
}
```

### PO Line Object

```json
{
  "id":                  101,
  "sequence":            10,
  "product_name":        "Acqua di Gio 100ml",
  "item_code":           "ADG-100",
  "uom":                 "pcs",
  "quantity":            50,
  "unit_price":          20.00,
  "total_price":         1000.00,
  "currency_id":         null,
  "currency_name":       "",
  "last_purchase_price": 0,
  "last_purchase_date":  null,
  "min_qty":             0,
  "max_qty":             0
}
```

### Attachment Object

```json
{
  "id":               55,
  "name":             "invoice.pdf",
  "mimetype":         "application/pdf",
  "size":             204800,
  "url":              "/web/content/55?download=true",
  "uploaded_by_name": "Admin",
  "created_at":       "2026-04-04T14:30:00"
}
```

### Comment Object

```json
{
  "id":          201,
  "body":        "Vendor confirmed shipment.",
  "type":        "comment",
  "author_id":   2,
  "author_name": "Admin",
  "created_at":  "2026-04-04T12:00:00"
}
```

### Penalty Object

```json
{
  "id":              1,
  "container_id":    2,
  "container_name":  "GLS15152",
  "penalty_type":    "storage",
  "amount":          500.00,
  "currency_id":     null,
  "currency_name":   "",
  "reason":          "30-day storage at Umm Qasr port",
  "penalty_date":    "2026-04-04",
  "created_by_name": "Admin",
  "created_at":      "2026-04-04T14:30:00"
}
```

---

## Enums

### PO Status

| Value | Label | Description |
|---|---|---|
| `draft` | Draft / مسودة | Initial state, editable |
| `confirmed` | Confirmed / مؤكد | Locked for changes |
| `shipped` | Shipped / تم الشحن | In transit |
| `received` | Received / تم الاستلام | Goods received, lines locked |
| `cancelled` | Cancelled / ملغي | Cancelled, can be reopened |

### Division

| Value | Label |
|---|---|
| `europe` | Europe / أوروبا |
| `china` | China / الصين |

### Penalty Types

| Value | Label |
|---|---|
| `storage` | Storage Fee / رسوم التخزين |
| `damage` | Damage / ضرر |
| `late` | Late Delivery / تأخير التسليم |
| `customs` | Customs / جمارك |
| `demurrage` | Demurrage / غرامة توقف السفينة |
| `other` | Other / أخرى |

### Comment Types

| Value | Description |
|---|---|
| `comment` | Regular public comment (visible in chatter) |
| `note` | Internal note (highlighted, team-only) |

---

## Error Reference

| Code | HTTP | Description | Resolution |
|---|---|---|---|
| `401` | — | Unauthorized | Token missing, expired, or invalid — re-login |
| `400` | — | Bad Request | Missing required param or invalid value |
| `404` | — | Not Found | Resource does not exist |
| `405` | 405 | Method Not Allowed | Request was sent as GET — must be POST |
| `415` | 415 | Unsupported Media Type | Missing `Content-Type: application/json` |

### Common API-Level Errors

```json
{ "success": false, "error": "Unauthorized",             "code": 401 }
{ "success": false, "error": "PO not found",             "code": 404 }
{ "success": false, "error": "PO must have at least one line to confirm", "code": 400 }
{ "success": false, "error": "Cannot delete a PO with status 'confirmed'. Cancel it first.", "code": 400 }
{ "success": false, "error": "Cannot add lines to a received PO", "code": 400 }
{ "success": false, "error": "Provide either driver_id or driver_name", "code": 400 }
{ "success": false, "error": "Invalid penalty_type. Must be one of: customs, damage, demurrage, late, other, storage", "code": 400 }
```

---

## Quick Reference — All Endpoints

| # | Method | Endpoint | Description |
|---|---|---|---|
| 1 | POST | `/api/crm/supply/po/list` | List POs with filters |
| 2 | POST | `/api/crm/supply/po/{id}/get` | Get single PO |
| 3 | POST | `/api/crm/supply/po/create` | Create PO + lines |
| 4 | POST | `/api/crm/supply/po/{id}/update` | Update PO header |
| 5 | POST | `/api/crm/supply/po/{id}/delete` | Delete PO (draft/cancelled only) |
| 6 | POST | `/api/crm/supply/po/{id}/confirm` | draft → confirmed |
| 7 | POST | `/api/crm/supply/po/{id}/ship` | confirmed → shipped |
| 8 | POST | `/api/crm/supply/po/{id}/receive` | shipped → received |
| 9 | POST | `/api/crm/supply/po/{id}/cancel` | any → cancelled |
| 10 | POST | `/api/crm/supply/po/{id}/reopen` | cancelled → draft |
| 11 | POST | `/api/crm/supply/po/{id}/lines/add` | Add line to PO |
| 12 | POST | `/api/crm/supply/po/{po_id}/lines/{line_id}/update` | Update line |
| 13 | POST | `/api/crm/supply/po/{po_id}/lines/{line_id}/delete` | Delete line |
| 14 | POST | `/api/crm/supply/po/{id}/attachments/upload` | Upload file (multipart) |
| 15 | POST | `/api/crm/supply/po/{id}/attachments/list` | List attachments |
| 16 | POST | `/api/crm/supply/po/{po_id}/attachments/{att_id}/delete` | Delete attachment |
| 17 | POST | `/api/crm/supply/po/{id}/comments/list` | List comments |
| 18 | POST | `/api/crm/supply/po/{id}/comments/add` | Add comment/note |
| 19 | POST | `/api/crm/supply/po/{po_id}/comments/{msg_id}/delete` | Delete comment |
| 20 | POST | `/api/crm/supply/containers/{id}/add_penalty` | Add penalty |
| 21 | POST | `/api/crm/supply/containers/{id}/penalties/list` | List penalties |
| 22 | POST | `/api/crm/supply/containers/{container_id}/penalties/{penalty_id}/delete` | Delete penalty |
| 23 | POST | `/api/crm/supply/containers/{id}/assign_driver` | Assign driver |
| 24 | POST | `/api/crm/supply/containers/{id}/unassign_driver` | Remove driver |
