# Supply Chain Module — Complete Workflow & API Reference

**Base URL:** `http://localhost:8070`
**Protocol:** JSON-RPC (`Content-Type: application/json`)
**Authentication:** `Authorization: Bearer <access_token>`

---

## Table of Contents

1. [User Login Credentials](#1-user-login-credentials)
2. [Authentication](#2-authentication)
3. [Permission Hierarchy](#3-permission-hierarchy)
4. [Purchase Order (PO) Workflow](#4-purchase-order-po-workflow)
5. [Item Request Workflow](#5-item-request-workflow)
6. [Container Management Workflow](#6-container-management-workflow)
7. [Vendor Management](#7-vendor-management)
8. [Negotiations](#8-negotiations)
9. [Clearance Companies](#9-clearance-companies)
10. [Min/Max Inventory](#10-minmax-inventory)
11. [Attachments](#11-attachments)
12. [Full API Endpoint Reference](#12-full-api-endpoint-reference)
13. [PO Response Fields Reference](#13-po-response-fields-reference)
14. [Response Codes](#14-response-codes)

---

## 1. User Login Credentials

All users below are active and have Supply Chain module access.

| Role | Username | Password | Full Name |
|------|----------|----------|-----------|
| General Manager | `crm_gm` | `Pass@1234` | المدير العام - CRM |
| Manager | `crm_manager` | `Pass@1234` | مدير CRM |
| Supervisor | `crm_supervisor` | `Pass@1234` | مشرف CRM |
| Agent (1) | `crm_agent1` | `Pass@1234` | موظف CRM - أول |
| Agent (2) | `crm_agent2` | `Pass@1234` | موظف CRM - ثاني |
| QA Supervisor | `crm_qa_sup` | `Pass@1234` | مشرف مدققي CRM |
| QA Auditor | `crm_qa` | `Pass@1234` | مدقق CRM |
| System Admin | `admin` | `admin` | Admin (Full Access) |

> **Note:** QA Supervisor and QA Auditor have read-only access to supply chain data.
> Write operations require Agent role or above.

---

## 2. Authentication

### Login

```http
POST /lugal/auth/login
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "username": "crm_agent1",
    "password": "Pass@1234"
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "user": {
        "id": 24,
        "name": "موظف CRM - أول",
        "username": "crm_agent1",
        "email": null
      }
    }
  }
}
```

### Refresh Token

```http
POST /lugal/auth/refresh
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "refresh_token": "eyJ..."
  }
}
```

### Logout

```http
POST /lugal/auth/logout
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {}
}
```

---

## 3. Permission Hierarchy

### Role Hierarchy (each level inherits all permissions below it)

```
General Manager  ──  Full access: delete any record, all operations
       ↑ inherits
    Manager      ──  Final PO approval, ship/receive, vendors, clearance co., penalties
       ↑ inherits
  Supervisor     ──  1st PO approval, item request approve/reject, container management
       ↑ inherits
    Agent        ──  Create PO, submit for approval, item requests, view all data
```

### Supply Chain Permission Matrix

| Action | Agent | Supervisor | Manager | GM |
|--------|:-----:|:----------:|:-------:|:--:|
| List / View all supply data | ✅ | ✅ | ✅ | ✅ |
| Create PO (draft) | ✅ | ✅ | ✅ | ✅ |
| Edit PO lines | ✅ | ✅ | ✅ | ✅ |
| Submit PO for approval | ✅ | ✅ | ✅ | ✅ |
| Create Item Request | ✅ | ✅ | ✅ | ✅ |
| Upload PO / Container attachments | ✅ | ✅ | ✅ | ✅ |
| **Approve / Reject Item Request** | ❌ | ✅ | ✅ | ✅ |
| **Supervisor-Approve PO (1st level)** | ❌ | ✅ | ✅ | ✅ |
| Create / Update containers | ❌ | ✅ | ✅ | ✅ |
| Mark clearance delivered | ❌ | ✅ | ✅ | ✅ |
| Mark container arrived at port | ❌ | ✅ | ✅ | ✅ |
| Assign / Unassign driver | ❌ | ✅ | ✅ | ✅ |
| Set container reminder | ❌ | ✅ | ✅ | ✅ |
| Create / Update negotiations | ❌ | ✅ | ✅ | ✅ |
| Delete attachment | ❌ | ✅ | ✅ | ✅ |
| **Manager-Confirm PO (final approval)** | ❌ | ❌ | ✅ | ✅ |
| Ship PO | ❌ | ❌ | ✅ | ✅ |
| Receive PO | ❌ | ❌ | ✅ | ✅ |
| Cancel / Reopen PO | ❌ | ❌ | ✅ | ✅ |
| Create / Update vendors | ❌ | ❌ | ✅ | ✅ |
| Create / Update clearance companies | ❌ | ❌ | ✅ | ✅ |
| Set Min/Max inventory | ❌ | ❌ | ✅ | ✅ |
| Add / Delete penalties | ❌ | ❌ | ✅ | ✅ |
| Mark item request as fulfilled | ❌ | ❌ | ✅ | ✅ |
| Delete item request / negotiation | ❌ | ❌ | ✅ | ✅ |
| **Delete any record** (PO, Container, Vendor…) | ❌ | ❌ | ❌ | ✅ |

---

## 4. Purchase Order (PO) Workflow

### PO Status Values

| Status | Label | Description |
|--------|-------|-------------|
| `draft` | Draft | Created by Agent, not yet submitted |
| `pending_approval` | Pending Approval | Submitted, waiting for Supervisor |
| `supervisor_approved` | Supervisor Approved | 1st approval done, waiting for Manager |
| `confirmed` | Confirmed | Manager final approval — ready for shipment |
| `shipped` | Shipped | Goods dispatched |
| `received` | Received | Goods delivered to warehouse |
| `cancelled` | Cancelled | Cancelled by Manager |

### State Machine Diagram

```
                    ┌──────────────────────────────────────────────────────┐
                    │              PO APPROVAL WORKFLOW                    │
                    │                                                      │
  [AGENT]          [SUPERVISOR]               [MANAGER]                   │
                                                                           │
  ┌───────┐  submit  ┌──────────────┐  sup_approve  ┌────────────────┐   │
  │ draft ├─────────►│ pending_     ├──────────────►│ supervisor_    │   │
  └───┬───┘          │ approval     │               │ approved       │   │
      │              └──────┬───────┘               └───────┬────────┘   │
      │               reject│                        reject │  confirm   │
      │◄────────────────────┘                               │    │       │
      │              (back to draft)                        │    ▼       │
      │                                               ┌─────┘  ┌──────┐ │
      │                                               └───────►│pend_ │ │
      │                                                        │apprvl│ │
      │                                                        └──────┘ │
      │                                                                  │
  ┌───▼──────────┐   ship   ┌─────────┐  receive  ┌──────────────┐     │
  │  confirmed   ├─────────►│ shipped ├──────────►│   received   │     │
  └──────┬───────┘          └─────────┘           └──────────────┘     │
         │ cancel (from any active state)                               │
         ▼                                                              │
    ┌──────────┐  reopen                                                │
    │cancelled ├──────────► draft                                       │
    └──────────┘                                                        │
                    └──────────────────────────────────────────────────────┘
```

### Step-by-Step PO Flow

---

#### Step 1 — Agent Creates PO

**Who:** `crm_agent1` / `crm_agent2`
**Endpoint:** `POST /api/crm/supply/po/create`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "name": "PO-2026-001",
    "vendor_customer_id": 10,
    "division": "china",
    "currency_id": 1,
    "branch_id": 2,
    "lines": [
      {
        "product_name": "Cotton T-Shirt",
        "item_code": "SKU-001",
        "uom": "piece",
        "quantity": 500,
        "unit_price": 5.50
      },
      {
        "product_name": "Denim Jeans",
        "item_code": "SKU-002",
        "uom": "piece",
        "quantity": 200,
        "unit_price": 12.00
      }
    ]
  }
}
```

**Result:** `status: "draft"` — PO created with lines

---

#### Step 2 — Agent Submits for Approval

**Who:** `crm_agent1` / `crm_agent2`
**Endpoint:** `POST /api/crm/supply/po/{po_id}/submit`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {}
}
```

**Result:** `status: "pending_approval"` — fields `submitted_by_id` and `submitted_at` are recorded

---

#### Step 3A — Supervisor Approves (1st Level)

**Who:** `crm_supervisor`
**Endpoint:** `POST /api/crm/supply/po/{po_id}/supervisor_approve`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "notes": "Quantities verified, prices acceptable. Forwarding to manager."
  }
}
```

**Result:** `status: "supervisor_approved"` — `supervisor_approved_by_id` and `supervisor_approved_at` recorded

---

#### Step 3B — Supervisor Rejects (back to draft)

**Who:** `crm_supervisor`
**Endpoint:** `POST /api/crm/supply/po/{po_id}/supervisor_reject`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "notes": "Prices are too high. Please renegotiate with vendor."
  }
}
```

**Result:** `status: "draft"` — returned to Agent for revision

---

#### Step 4A — Manager Final Approval

**Who:** `crm_manager`
**Endpoint:** `POST /api/crm/supply/po/{po_id}/confirm`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "notes": "Approved. Proceed with the order."
  }
}
```

**Result:** `status: "confirmed"` — `manager_approved_by_id` and `manager_approved_at` recorded

---

#### Step 4B — Manager Sends Back to Supervisor

**Who:** `crm_manager`
**Endpoint:** `POST /api/crm/supply/po/{po_id}/manager_reject`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "notes": "Line quantities need adjustment before I can approve."
  }
}
```

**Result:** `status: "pending_approval"` — returned to Supervisor for re-review

---

#### Step 5 — Manager Records Shipment

**Who:** `crm_manager`
**Endpoint:** `POST /api/crm/supply/po/{po_id}/ship`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {}
}
```

**Result:** `status: "shipped"`

---

#### Step 6 — Manager Records Receipt

**Who:** `crm_manager`
**Endpoint:** `POST /api/crm/supply/po/{po_id}/receive`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {}
}
```

**Result:** `status: "received"` — PO lifecycle complete

---

#### Cancel PO

**Who:** `crm_manager` (from any status except `received`)
**Endpoint:** `POST /api/crm/supply/po/{po_id}/cancel`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {}
}
```

---

#### Reopen Cancelled PO

**Who:** `crm_manager` (only from `cancelled` status)
**Endpoint:** `POST /api/crm/supply/po/{po_id}/reopen`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {}
}
```

**Result:** `status: "draft"`

---

#### Delete PO

**Who:** `crm_gm` only (only from `draft` or `cancelled` status)
**Endpoint:** `POST /api/crm/supply/po/{po_id}/delete`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {}
}
```

---

### PO Lines Management

#### List Lines

**Who:** Agent+
**Endpoint:** `POST /api/crm/supply/po/{po_id}/lines`

#### Add Line

**Who:** Agent+
**Endpoint:** `POST /api/crm/supply/po/{po_id}/lines/add`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "product_name": "Leather Belt",
    "item_code": "SKU-003",
    "uom": "piece",
    "quantity": 300,
    "unit_price": 8.00,
    "min_qty": 50,
    "max_qty": 500
  }
}
```

#### Update Line

**Who:** Agent+
**Endpoint:** `POST /api/crm/supply/po/{po_id}/lines/{line_id}/update`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "quantity": 350,
    "unit_price": 7.50
  }
}
```

#### Delete Line

**Who:** Supervisor+
**Endpoint:** `POST /api/crm/supply/po/{po_id}/lines/{line_id}/delete`

---

## 5. Item Request Workflow

### Item Request Status Values

| Status | Description |
|--------|-------------|
| `pending` | Created by Agent, awaiting Supervisor review |
| `approved` | Approved by Supervisor |
| `rejected` | Rejected by Supervisor |
| `fulfilled` | Marked as fulfilled by Manager |

### State Machine

```
[AGENT]          [SUPERVISOR]          [MANAGER]

  create ──►  pending ──approve──►  approved ──fulfilled──► fulfilled
                      ──reject───►  rejected
```

---

#### Step 1 — Agent Creates Item Request

**Who:** `crm_agent1` / `crm_agent2`
**Endpoint:** `POST /api/crm/supply/item_requests/create`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "product_id": 15,
    "quantity": 100,
    "uom": "piece",
    "branch_id": 2,
    "note": "Critical stock shortage — immediate restock needed"
  }
}
```

**Result:** `status: "pending"`

---

#### Step 2 — Supervisor Approves

**Who:** `crm_supervisor`
**Endpoint:** `POST /api/crm/supply/item_requests/{id}/update_status`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "status": "approved"
  }
}
```

> To reject: use `"status": "rejected"` instead.

---

#### Step 3 — Manager Marks as Fulfilled

**Who:** `crm_manager`
**Endpoint:** `POST /api/crm/supply/item_requests/{id}/update_status`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "status": "fulfilled"
  }
}
```

---

## 6. Container Management Workflow

### Container Status Values

| Status | Description |
|--------|-------------|
| `waiting` | Registered, not yet shipped |
| `active` | In transit |
| `at_port` | Arrived at destination port |
| `completed` | Cleared and delivered |

### Container Lifecycle

```
[SUPERVISOR]

  Create container ──► waiting
       │
       ▼
  Update tracking  ──► active (in transit)
       │
       ▼
  Mark arrived     ──► at_port
       │
       ▼
  Mark clearance   ──► clearance_info_delivered = true
  delivered
       │
  Assign driver    ──► driver_id assigned
       │
       ▼
  Manual update    ──► completed
```

---

#### Create Container

**Who:** `crm_supervisor` (Supervisor+)
**Endpoint:** `POST /api/crm/supply/containers/create`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "name": "CNT-2026-001",
    "container_number": "MSCU1234567",
    "bl_number": "BL-2026-001",
    "status": "active",
    "division": "china",
    "origin_location": "Shanghai",
    "destination_port": "Umm Qasr",
    "departure_date": "2026-04-01",
    "eta": "2026-04-25",
    "clearance_company_id": 1,
    "assigned_user_id": 22,
    "total_weight_kg": 15000,
    "total_cbm": 28.5,
    "tracking_url": "https://www.searates.com/tracking/?number=MSCU1234567"
  }
}
```

---

#### Link PO to Container

**Who:** `crm_agent1` (Agent+)
**Endpoint:** `POST /api/crm/supply/po/{po_id}/update`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "container_id": 5
  }
}
```

---

#### Assign Driver

**Who:** `crm_supervisor` (Supervisor+)
**Endpoint:** `POST /api/crm/supply/containers/{id}/assign_driver`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "driver_name": "Ahmed Mohammed",
    "driver_phone": "07801234567"
  }
}
```

> To assign by existing partner ID: use `"driver_id": 45` instead.

---

#### Mark Clearance Info Delivered

**Who:** `crm_supervisor` (Supervisor+)
**Endpoint:** `POST /api/crm/supply/containers/{id}/clearance_delivered`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {}
}
```

**Result:** `clearance_info_delivered: true` + timestamp recorded

---

#### Mark Container Arrived at Port

**Who:** `crm_supervisor` (Supervisor+)
**Endpoint:** `POST /api/crm/supply/containers/{id}/mark_arrived`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {}
}
```

**Result:** `status: "at_port"` + `arrived_at` timestamp recorded

---

#### Set Reminder

**Who:** `crm_supervisor` (Supervisor+)
**Endpoint:** `POST /api/crm/supply/containers/{id}/set_reminder`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "reminder_date": "2026-04-20T09:00:00",
    "reminder_note": "Follow up on customs clearance status"
  }
}
```

> To clear a reminder: `{ "clear_reminder": true }`

---

#### Add Penalty

**Who:** `crm_manager` (Manager+)
**Endpoint:** `POST /api/crm/supply/containers/{id}/add_penalty`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "penalty_type": "demurrage",
    "amount": 250.00,
    "reason": "Delay in container clearance — 5 extra days",
    "penalty_date": "2026-04-20",
    "currency_id": 1
  }
}
```

**Penalty types:** `storage` | `damage` | `late` | `customs` | `demurrage` | `other`

---

#### Delete Container

**Who:** `crm_gm` only (General Manager)
**Endpoint:** `POST /api/crm/supply/containers/{id}/delete`

---

## 7. Vendor Management

### Create Vendor

**Who:** `crm_manager` (Manager+)
**Endpoint:** `POST /api/crm/supply/vendors/create`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "name": "Shanghai Fashion Co.",
    "name_ar": "شركة شنغهاي للأزياء",
    "division": "china",
    "phone": "+86 21 12345678",
    "email": "info@shanghai-fashion.com",
    "whatsapp": "+86 21 12345678",
    "wechat": "shanghaifc",
    "country_id": 44,
    "city": "Shanghai",
    "address": "123 Fashion Street, Pudong",
    "payment_terms": "30 days net",
    "lead_time_days": 45,
    "min_order_value": 5000.00,
    "notes": "Reliable supplier. Always check for early shipping discounts."
  }
}
```

**Division values:** `europe` | `china`

### List Vendors

**Who:** `crm_agent1` (Agent+)
**Endpoint:** `POST /api/crm/supply/vendors/list`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "contact_type": "vendor",
    "division": "china",
    "search": "Shanghai",
    "page": 1,
    "per_page": 20
  }
}
```

**Contact type filter:** `vendor` | `customer` | `both` (or omit for all)

### Update Vendor

**Who:** `crm_manager` (Manager+)
**Endpoint:** `POST /api/crm/supply/vendors/{id}/update`

### Delete Vendor

**Who:** `crm_gm` only
**Endpoint:** `POST /api/crm/supply/vendors/{id}/delete`

---

## 8. Negotiations

### Negotiation Status Values

| Status | Description |
|--------|-------------|
| `open` | Negotiation in progress |
| `pending` | Waiting for vendor response |
| `closed` | Negotiation concluded |

### Create Negotiation

**Who:** `crm_supervisor` (Supervisor+)
**Endpoint:** `POST /api/crm/supply/negotiations/create`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "title": "Q2 Bulk Order Price Negotiation",
    "supply_vendor_id": 3,
    "product_id": 15,
    "quantity": 1000,
    "expected_price": 4.50,
    "currency_id": 1,
    "due_date": "2026-04-30",
    "description": "Targeting better bulk pricing for Q2 order"
  }
}
```

### Update Negotiation (close with agreed price)

**Who:** `crm_supervisor` (Supervisor+)
**Endpoint:** `POST /api/crm/supply/negotiations/{id}/update`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "agreed_price": 4.20,
    "status": "closed",
    "notes": "Vendor agreed to $4.20 per unit for orders above 800 pieces"
  }
}
```

### Delete Negotiation

**Who:** `crm_gm` only
**Endpoint:** `POST /api/crm/supply/negotiations/{id}/delete`

---

## 9. Clearance Companies

### Create Clearance Company

**Who:** `crm_manager` (Manager+)
**Endpoint:** `POST /api/crm/supply/clearance_companies/create`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "name": "Al-Ufuq Customs Clearance Co.",
    "contact_name": "Abdullah Al-Zubaidi",
    "phone": "07701234567",
    "whatsapp": "07701234567",
    "email": "info@alufuq-clearance.com",
    "city": "Basra",
    "address": "Port Road, Umm Qasr",
    "license_number": "CC-2024-0056",
    "license_expiry": "2027-12-31",
    "notes": "Specialized in fashion and textile imports"
  }
}
```

### List Clearance Companies

**Who:** `crm_agent1` (Agent+)
**Endpoint:** `POST /api/crm/supply/clearance_companies/list`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "is_active": true,
    "page": 1,
    "per_page": 20
  }
}
```

### Delete Clearance Company

**Who:** `crm_gm` only
**Endpoint:** `POST /api/crm/supply/clearance_companies/{id}/delete`

---

## 10. Min/Max Inventory

### Set Min/Max for a Product

**Who:** `crm_manager` (Manager+)
**Endpoint:** `POST /api/crm/supply/inventory/minmax/update`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "product_id": 15,
    "min_qty": 50,
    "max_qty": 500,
    "branch_id": 2
  }
}
```

> This is an upsert — creates a new record if none exists for the product/branch combination.

### List Products Needing Reorder

**Who:** `crm_agent1` (Agent+)
**Endpoint:** `POST /api/crm/supply/inventory/minmax`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "needs_reorder": true,
    "branch_id": 2,
    "page": 1,
    "per_page": 50
  }
}
```

**Response includes:** `current_stock`, `min_qty`, `max_qty`, `needs_reorder`

### Delete Min/Max Record

**Who:** `crm_manager` (Manager+)
**Endpoint:** `POST /api/crm/supply/inventory/minmax/delete`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "product_id": 15,
    "branch_id": 2
  }
}
```

---

## 11. Attachments

### Upload Attachment to Container

**Who:** `crm_supervisor` (Supervisor+)
**Endpoint:** `POST /api/crm/supply/containers/{id}/attachments/upload`

```http
Content-Type: multipart/form-data
Authorization: Bearer <token>

files[]: [PDF/image file]
label: "Bill of Lading"  (optional)
```

### Upload Attachment to PO

**Who:** `crm_agent1` (Agent+)
**Endpoint:** `POST /api/crm/supply/po/{id}/attachments/upload`

```http
Content-Type: multipart/form-data
Authorization: Bearer <token>

files[]: [PDF/image file]
```

**Allowed file types:** PDF, JPEG, PNG, WEBP, GIF, DOC, DOCX, XLS, XLSX
**Max file size:** 25 MB per file
**Multi-file upload:** use `files[]` field name for batch uploads

### List Attachments

**Endpoint:** `POST /api/crm/supply/containers/{id}/attachments/list`
**Endpoint:** `POST /api/crm/supply/po/{id}/attachments/list`
**Who:** Agent+

### Delete Attachment

**Endpoint:** `POST /api/crm/supply/containers/{id}/attachments/{att_id}/delete`
**Endpoint:** `POST /api/crm/supply/po/{id}/attachments/{att_id}/delete`
**Who:** Supervisor+

---

## 12. Full API Endpoint Reference

### Authentication

| Endpoint | Description | Permission |
|----------|-------------|------------|
| `POST /lugal/auth/login` | Login | Public |
| `POST /lugal/auth/refresh` | Refresh token | Public |
| `POST /lugal/auth/logout` | Logout | JWT |

### Purchase Orders

| Endpoint | Description | Min Role |
|----------|-------------|----------|
| `POST /api/crm/supply/po/list` | List POs | Agent |
| `POST /api/crm/supply/po/{id}/get` | Get PO detail | Agent |
| `POST /api/crm/supply/po/create` | Create PO | Agent |
| `POST /api/crm/supply/po/{id}/update` | Update PO header | Agent |
| `POST /api/crm/supply/po/{id}/lines` | List PO lines | Agent |
| `POST /api/crm/supply/po/{id}/lines/add` | Add line | Agent |
| `POST /api/crm/supply/po/{id}/lines/{lid}/update` | Update line | Agent |
| `POST /api/crm/supply/po/suggested` | List suggested POs | Agent |
| `POST /api/crm/supply/po/{id}/submit` | **Submit for approval** | Agent |
| `POST /api/crm/supply/po/{id}/lines/{lid}/delete` | Delete line | Supervisor |
| `POST /api/crm/supply/po/{id}/supervisor_approve` | **Supervisor approval (1st)** | Supervisor |
| `POST /api/crm/supply/po/{id}/supervisor_reject` | **Supervisor rejection** | Supervisor |
| `POST /api/crm/supply/po/{id}/confirm` | **Manager final approval** | Manager |
| `POST /api/crm/supply/po/{id}/manager_reject` | **Manager rejection** | Manager |
| `POST /api/crm/supply/po/{id}/ship` | Mark shipped | Manager |
| `POST /api/crm/supply/po/{id}/receive` | Mark received | Manager |
| `POST /api/crm/supply/po/{id}/cancel` | Cancel PO | Manager |
| `POST /api/crm/supply/po/{id}/reopen` | Reopen cancelled PO | Manager |
| `POST /api/crm/supply/po/{id}/attachments/upload` | Upload attachment | Agent |
| `POST /api/crm/supply/po/{id}/attachments/list` | List attachments | Agent |
| `POST /api/crm/supply/po/{id}/attachments/{aid}/delete` | Delete attachment | Supervisor |
| `POST /api/crm/supply/po/{id}/delete` | Delete PO | GM |

### Containers

| Endpoint | Description | Min Role |
|----------|-------------|----------|
| `POST /api/crm/supply/containers/list` | List containers | Agent |
| `POST /api/crm/supply/containers/{id}/get` | Get container detail | Agent |
| `POST /api/crm/supply/containers/{id}/penalties/list` | List penalties | Agent |
| `POST /api/crm/supply/containers/{id}/attachments/list` | List attachments | Agent |
| `POST /api/crm/supply/containers/create` | Create container | Supervisor |
| `POST /api/crm/supply/containers/{id}/update` | Update container | Supervisor |
| `POST /api/crm/supply/containers/{id}/clearance_delivered` | Mark clearance delivered | Supervisor |
| `POST /api/crm/supply/containers/{id}/mark_arrived` | Mark arrived at port | Supervisor |
| `POST /api/crm/supply/containers/{id}/set_reminder` | Set/clear reminder | Supervisor |
| `POST /api/crm/supply/containers/{id}/assign_driver` | Assign driver | Supervisor |
| `POST /api/crm/supply/containers/{id}/unassign_driver` | Remove driver | Supervisor |
| `POST /api/crm/supply/containers/{id}/attachments/upload` | Upload attachment | Supervisor |
| `POST /api/crm/supply/containers/{id}/attachments/{aid}/delete` | Delete attachment | Supervisor |
| `POST /api/crm/supply/containers/{id}/add_penalty` | Add penalty | Manager |
| `POST /api/crm/supply/containers/{id}/penalties/{pid}/delete` | Delete penalty | Manager |
| `POST /api/crm/supply/containers/{id}/delete` | Delete container | GM |

### Vendors

| Endpoint | Description | Min Role |
|----------|-------------|----------|
| `POST /api/crm/supply/vendors/list` | List vendors | Agent |
| `POST /api/crm/supply/vendors/{id}/get` | Get vendor detail | Agent |
| `POST /api/crm/supply/vendors/create` | Create vendor | Manager |
| `POST /api/crm/supply/vendors/{id}/update` | Update vendor | Manager |
| `POST /api/crm/supply/vendors/{id}/delete` | Delete vendor | GM |

### Item Requests

| Endpoint | Description | Min Role |
|----------|-------------|----------|
| `POST /api/crm/supply/item_requests/list` | List requests | Agent |
| `POST /api/crm/supply/item_requests/{id}/get` | Get request detail | Agent |
| `POST /api/crm/supply/item_requests/create` | Create request | Agent |
| `POST /api/crm/supply/item_requests/{id}/update` | Update fields | Agent |
| `POST /api/crm/supply/item_requests/{id}/update_status` | **Approve / Reject** | Supervisor (approve/reject) |
| `POST /api/crm/supply/item_requests/{id}/update_status` | **Mark Fulfilled** | Manager (fulfilled) |
| `POST /api/crm/supply/item_requests/{id}/delete` | Delete request | Manager |

### Negotiations

| Endpoint | Description | Min Role |
|----------|-------------|----------|
| `POST /api/crm/supply/negotiations/list` | List negotiations | Agent |
| `POST /api/crm/supply/negotiations/{id}/get` | Get negotiation detail | Agent |
| `POST /api/crm/supply/negotiations/create` | Create negotiation | Supervisor |
| `POST /api/crm/supply/negotiations/{id}/update` | Update negotiation | Supervisor |
| `POST /api/crm/supply/negotiations/{id}/delete` | Delete negotiation | GM |

### Clearance Companies

| Endpoint | Description | Min Role |
|----------|-------------|----------|
| `POST /api/crm/supply/clearance_companies/list` | List companies | Agent |
| `POST /api/crm/supply/clearance_companies/{id}/get` | Get company detail | Agent |
| `POST /api/crm/supply/clearance_companies/create` | Create company | Manager |
| `POST /api/crm/supply/clearance_companies/{id}/update` | Update company | Manager |
| `POST /api/crm/supply/clearance_companies/{id}/delete` | Delete company | GM |

### Min/Max Inventory

| Endpoint | Description | Min Role |
|----------|-------------|----------|
| `POST /api/crm/supply/inventory/minmax` | List min/max records | Agent |
| `POST /api/crm/supply/inventory/minmax/update` | Upsert min/max | Manager |
| `POST /api/crm/supply/inventory/minmax/delete` | Delete min/max record | Manager |

---

## 13. PO Response Fields Reference

After the approval workflow was implemented, every PO response includes audit trail fields:

```json
{
  "id": 22,
  "name": "PO-2026-001",
  "status": "confirmed",
  "status_label": "Confirmed / مؤكد",

  "vendor_customer_id": 10,
  "vendor_customer_name": "Shanghai Fashion Co.",
  "vendor_customer_phone": "+86 21 12345678",
  "vendor_id": null,
  "vendor_name": "Shanghai Fashion Co.",

  "division": "china",
  "currency_id": 1,
  "currency_name": "USD",
  "container_id": 5,
  "container_name": "CNT-2026-001",
  "branch_id": 2,
  "branch_name": "Baghdad Branch",

  "is_suggested": false,
  "line_count": 2,
  "total_amount": 5150.00,

  "submitted_by_id": 24,
  "submitted_by_name": "موظف CRM - أول",
  "submitted_at": "2026-04-06T09:30:00",

  "supervisor_approved_by_id": 23,
  "supervisor_approved_by_name": "مشرف CRM",
  "supervisor_approved_at": "2026-04-06T10:00:00",

  "manager_approved_by_id": 22,
  "manager_approved_by_name": "مدير CRM",
  "manager_approved_at": "2026-04-06T11:30:00",

  "approval_notes": "Approved. Proceed with the order.",

  "created_by_id": 24,
  "created_by_name": "موظف CRM - أول",
  "created_at": "2026-04-06T08:00:00",
  "updated_at": "2026-04-06T11:30:00",

  "lines": [
    {
      "id": 45,
      "sequence": 1,
      "product_name": "Cotton T-Shirt",
      "item_code": "SKU-001",
      "uom": "piece",
      "quantity": 500,
      "unit_price": 5.50,
      "total_price": 2750.00,
      "min_qty": 0,
      "max_qty": 0
    },
    {
      "id": 46,
      "sequence": 2,
      "product_name": "Denim Jeans",
      "item_code": "SKU-002",
      "uom": "piece",
      "quantity": 200,
      "unit_price": 12.00,
      "total_price": 2400.00,
      "min_qty": 0,
      "max_qty": 0
    }
  ]
}
```

---

## 14. Response Codes

| Code | Meaning | Example |
|------|---------|---------|
| `success: true` | Operation succeeded | — |
| `success: false, code: 401` | Unauthorized — missing or expired token | Token not sent or expired |
| `success: false, code: 403` | Forbidden — insufficient role permissions | Agent trying to confirm a PO |
| `success: false, code: 404` | Record not found | PO ID doesn't exist |
| `success: false, code: 409` | State conflict | Confirming a PO that is not in `supervisor_approved` status |
| `success: false, code: 422` | Invalid data | Confirming a PO with no lines |

### Error Response Example

```json
{
  "result": {
    "success": false,
    "code": 403,
    "error": "This action requires CRM Manager role or above"
  }
}
```

---

## 15. End-to-End Scenario

A complete real-world supply chain cycle:

```
Day 1 — Agent (crm_agent1 / Pass@1234):
  ├── Login → get access_token
  ├── Browse vendor list → select vendor
  ├── Create new PO with product lines
  └── Submit PO for approval

Day 2 — Supervisor (crm_supervisor / Pass@1234):
  ├── Login → get access_token
  ├── Review pending PO
  ├── Supervisor-approve (or reject with notes)
  └── Create container and link PO to it

Day 3 — Manager (crm_manager / Pass@1234):
  ├── Login → get access_token
  ├── Review supervisor-approved PO
  ├── Manager final confirm (or reject back to supervisor)
  └── Set up clearance company and min/max if needed

During Shipping — Supervisor (crm_supervisor / Pass@1234):
  ├── Mark clearance info delivered
  ├── Assign driver to container
  └── Mark container arrived at port

Delivery — Manager (crm_manager / Pass@1234):
  ├── Mark PO as shipped
  └── After warehouse confirmation → Mark PO as received

Audit — General Manager (crm_gm / Pass@1234):
  ├── Review full audit trail on any PO (submitted_by, approved_by, timestamps)
  ├── Delete records if needed
  └── Manage penalties on containers
```

---

*Auto-generated — Last updated: 2026-04-06*
