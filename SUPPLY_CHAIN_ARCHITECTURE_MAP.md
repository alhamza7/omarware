# 🗺️ Supply Chain — Complete Architecture Diagram
# خارطة سلسلة التوريد الكاملة

---

## 📊 SYSTEM OVERVIEW — نظرة عامة

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                        LUGAL SUPPLY CHAIN SYSTEM                                    ║
║                        نظام سلسلة التوريد — لوغال                                  ║
╠══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                      ║
║   FRONTEND ──────► POST /lugal/auth/login ──► JWT Token ──► All API calls           ║
║                    Authorization: Bearer <token>                                     ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 🔷 DATA MODEL DIAGRAM — مخطط البيانات

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           CORE ENTITIES                                           │
│                           الكيانات الأساسية                                      │
└──────────────────────────────────────────────────────────────────────────────────┘

 ┌─────────────────────────────────┐          ┌──────────────────────────────────┐
 │   lugal.supply.clearance.company│◄─────────│    lugal.supply.container        │
 │   ─────────────────────────────│          │   ──────────────────────────────│
 │   • id, name                   │          │   • id, name                     │
 │   • contact_name               │          │   • container_number             │
 │   • phone, email               │          │   • bl_number                    │
 │   • whatsapp, telegram         │          │   • status:                      │
 │   • country_id                 │          │     waiting│active│at_port│      │
 │   • city, address              │          │     completed                    │
 │   • license_number             │          │   • division: europe│china        │
 │   • license_expiry             │          │   • origin_location              │
 │   • is_active, is_deleted      │          │   • destination_port             │
 └─────────────────────────────────┘          │   • departure_date, eta         │
              ▲ clearance_company_id           │   • arrived_at                  │
              │                               │   • tracking_url                │
              │                               │   • total_weight_kg, total_cbm  │
              │                               │   • clearance_info_delivered ───►│──►action_mark_clearance_delivered()
              │                               │   • assigned_user_id ──────────►│──► res.users
              │                               │   • driver_id ─────────────────►│──► res.partner
              │                               │   • driver_assigned_at          │
              │                               │   • attachment_ids (M2M) ──────►│──► ir.attachment
              │                               │   • notes, is_deleted           │
              │                               └──────────────────────────────────┘
              │                                        ▲              ▲
              │                                   container_id    linked_container_id
              │                                        │              │
              │                          ┌─────────────┘    ┌─────────┘
              │                          │                   │
 ┌────────────┴───────────────────┐      │     ┌─────────────────────────────────┐
 │   lugal.crm.supply.po          │◄─────┘     │   lugal.email.message           │
 │   ─────────────────────────── │            │   (inherits mail.message)        │
 │   • id, name (required)       │            │   • linked_container_id          │
 │   • vendor_id ────────────────┼────────►   │   • linked_negotiation_id        │
 │   • division: europe│china    │            └─────────────────────────────────┘
 │   • currency_id               │
 │   • container_id              │             ╔══════════════════════════════╗
 │   • branch_id                 │             ║  PO STATUS FLOW              ║
 │   • status:                   │             ║  ─────────────────────────── ║
 │     draft → confirmed         │             ║  draft → confirmed           ║
 │     → shipped → received      │             ║       → shipped              ║
 │     → cancelled               │             ║       → received             ║
 │   • line_ids (O2M)            │             ║       → cancelled            ║
 │   • total_amount (computed)   │             ╚══════════════════════════════╝
 │   • is_suggested              │
 │   • is_deleted                │
 └────────────────────────────────┘
          │ (One2many)
          ▼
 ┌────────────────────────────────┐
 │   lugal.crm.supply.po.line     │
 │   ─────────────────────────── │
 │   • po_id (cascade delete)    │
 │   • sequence                  │
 │   • product_name, item_code   │
 │   • uom, quantity             │
 │   • unit_price, currency_id   │
 │   • last_purchase_price/date  │
 │   • total_price (computed)    │
 │   • min_qty, max_qty          │
 └────────────────────────────────┘


 ┌─────────────────────────────────┐         ┌──────────────────────────────────┐
 │   lugal.supply.vendor           │         │   lugal.supply.negotiation       │
 │   ─────────────────────────────│         │   ──────────────────────────────│
 │   • id, name, name_ar          │◄────────│   • supply_vendor_id             │
 │   • partner_id ───────────────►│res.partner  • vendor_id ──────────────►res.partner
 │   • division: europe│china│    │         │   • product_id ─────────────►product
 │     other                      │         │   • title (required)            │
 │   • country_id, city, address  │         │   • description, quantity       │
 │   • contact_name, phone        │         │   • currency_id                 │
 │   • email, website             │         │   • expected_price              │
 │   • whatsapp, wechat, telegram │         │   • agreed_price                │
 │   • payment_terms              │         │   • status:                     │
 │   • currency_id                │         │     open│pending│closed         │
 │   • lead_time_days             │         │   • due_date, notes             │
 │   • min_order_value            │         │   • linked_email (O2M)          │
 │   • active, is_deleted         │         │   • is_deleted                  │
 └─────────────────────────────────┘         └──────────────────────────────────┘
          ▲
          │  Also unified with:
          │
 ┌─────────────────────────────────┐
 │   lugal.crm.customer            │
 │   (VENDORS API uses this)       │
 │   ─────────────────────────────│
 │   • contact_type:               │
 │     customer│vendor│both        │
 │   • name, name_ar               │
 │   • phone_1, email, city        │
 │   • whatsapp, wechat, telegram  │
 │   • division, payment_terms_vendor│
 │   • lead_time_days              │
 │   • min_order_value             │
 └─────────────────────────────────┘


 ┌─────────────────────────────────┐         ┌──────────────────────────────────┐
 │   lugal.supply.item.request     │         │   lugal.supply.minmax            │
 │   ─────────────────────────────│         │   ──────────────────────────────│
 │   • product_id ───────────►product        │   • product_id ────────────►product
 │   • quantity, uom              │         │   • branch_id (integer)         │
 │   • branch_id (integer)        │         │   • min_qty, max_qty            │
 │   • requested_by_id ──────►res.users      │   UNIQUE (product_id, branch_id)│
 │   • status:                    │         └──────────────────────────────────┘
 │     pending→approved│rejected  │
 │     →fulfilled                 │
 │   • note, is_deleted           │
 └─────────────────────────────────┘


 ┌─────────────────────────────────┐         ┌──────────────────────────────────┐
 │   lugal.supply.conversation     │         │   lugal.supply.internal.message  │
 │   ─────────────────────────────│         │   ──────────────────────────────│
 │   • type: team│dm│group        │◄────────│   • conversation_id (cascade)   │
 │   • name                       │         │   • sender_id ──────────────►res.users
 │   • participant_ids (M2M) ───►res.users   │   • recipient_ids (M2M) ───►res.users
 │   • created_by ────────────►res.users     │   • content (required)          │
 │   • last_activity              │         │   • attachments_json            │
 │   • message_count (computed)   │         │   • is_deleted                  │
 │   • is_archived                │         └──────────────────────────────────┘
 │   • message_ids (O2M)          │
 └─────────────────────────────────┘


 ┌─────────────────────────────────┐
 │   lugal.supply.notification     │
 │   ─────────────────────────────│
 │   • user_id ───────────────►res.users
 │   • notif_type:                 │
 │     po_created                  │
 │     container_arrived           │
 │     clearance_done              │
 │     low_stock                   │
 │     negotiation_update          │
 │   • title (required), body      │
 │   • related_id + related_type   │
 │     (polymorphic reference)     │
 │   • is_read, is_deleted         │
 └─────────────────────────────────┘
```

---

## 🔗 RELATIONSHIPS MAP — خارطة العلاقات

```
                            ┌─────────────────────────────────┐
                            │         res.partner              │
                            │         res.users                │
                            │         res.country              │
                            │         product.product          │
                            │         res.currency             │
                            │         ir.attachment            │
                            │         lugal.crm.branch         │
                            └──────────────────┬──────────────┘
                                               │ Referenced by all models
                    ┌──────────────────────────┼──────────────────────┐
                    │                          │                       │
                    ▼                          ▼                       ▼
       lugal.supply.clearance.company    lugal.supply.vendor    lugal.crm.customer
                    │                          │                 (vendor API)
                    │ clearance_company_id      │ vendor_id / supply_vendor_id
                    ▼                          │
       lugal.supply.container ◄───────────────┤
                    │                          │
                    │ container_id             │
                    ▼                          ▼
       lugal.crm.supply.po ◄──────────────────┘
                    │
                    │ po_id (cascade)
                    ▼
       lugal.crm.supply.po.line


       lugal.supply.negotiation
              │ linked via email
              ▼
       lugal.email.message (extends mail.message)


       lugal.supply.conversation
              │ One2many
              ▼
       lugal.supply.internal.message


       lugal.supply.item.request ──► triggers ──► lugal.supply.notification
       lugal.supply.minmax       (inventory levels)
```

---

## 🌐 API ENDPOINTS MAP — خارطة الـ API

```
BASE URL: http://localhost:8070
AUTH:     Authorization: Bearer <token>
FORMAT:   POST, Content-Type: application/json
          { "jsonrpc": "2.0", "method": "call", "params": {...} }


╔════════════════════════════════════════════════════════════════════════════════╗
║  📦 CONTAINERS — /api/crm/supply/containers/                                   ║
╠═══════════════════════════════╦════════════════════════════════════════════════╣
║  /containers/list             ║ List + filter (status, division, search)       ║
║  /containers/create           ║ Create new container                          ║
║  /containers/<id>/get         ║ Get container + attachments                   ║
║  /containers/<id>/update      ║ Update fields                                 ║
║  /containers/<id>/delete      ║ Soft delete (is_deleted=true)                 ║
╠═══════════════════════════════╬════════════════════════════════════════════════╣
║  STATUS TRANSITIONS:          ║                                                ║
║  /containers/<id>/mark_arrived║ status → at_port + arrived_at = now()         ║
║  /containers/<id>/clearance_  ║ clearance_info_delivered = true               ║
║    delivered                  ║                                                ║
╠═══════════════════════════════╬════════════════════════════════════════════════╣
║  DRIVER ASSIGNMENT:           ║                                                ║
║  /containers/<id>/assign_     ║ driver_id + driver_assigned_at/by             ║
║    driver                     ║                                                ║
║  /containers/<id>/unassign_   ║ Clear driver fields                           ║
║    driver                     ║                                                ║
╠═══════════════════════════════╬════════════════════════════════════════════════╣
║  ATTACHMENTS (multipart):     ║                                                ║
║  /containers/<id>/attachments/║ Upload file (multipart/form-data)             ║
║    upload                     ║ field: file or files[]                         ║
║  /containers/<id>/attachments/║ List all attachments                          ║
║    list                       ║                                                ║
║  /containers/<id>/attachments/║ Delete attachment                             ║
║    <att_id>/delete            ║                                                ║
╠═══════════════════════════════╬════════════════════════════════════════════════╣
║  COMMENTS (mail.message):     ║                                                ║
║  /containers/<id>/comments/   ║ List comments/notes (paginated)               ║
║    list                       ║                                                ║
║  /containers/<id>/comments/   ║ Add comment { body, is_note }                 ║
║    add                        ║                                                ║
║  /containers/<id>/comments/   ║ Delete comment (author/admin only)            ║
║    <msg_id>/delete            ║                                                ║
╚═══════════════════════════════╩════════════════════════════════════════════════╝


╔════════════════════════════════════════════════════════════════════════════════╗
║  🧾 PURCHASE ORDERS — /api/crm/supply/po/                                      ║
╠═══════════════════════════════╦════════════════════════════════════════════════╣
║  /po/list                     ║ List POs + filter                              ║
║  /po/create                   ║ Create PO { name, vendor_id, ... }            ║
║  /po/<id>/get                 ║ PO + all lines                                ║
║  /po/<id>/update              ║ Update PO header                              ║
║  /po/<id>/delete              ║ Soft delete                                   ║
║  /po/suggested                ║ List suggested POs (is_suggested=true)        ║
╠═══════════════════════════════╬════════════════════════════════════════════════╣
║  PO LINES:                    ║                                                ║
║  /po/<id>/lines               ║ List lines only                               ║
║  /po/<id>/lines/add           ║ Add line { product_name, quantity, ... }      ║
║  /po/<id>/lines/<lid>/update  ║ Update line                                   ║
║  /po/<id>/lines/<lid>/delete  ║ Hard delete line                              ║
╠═══════════════════════════════╬════════════════════════════════════════════════╣
║  COMMENTS:                    ║                                                ║
║  /po/<id>/comments/list       ║ List comments                                 ║
║  /po/<id>/comments/add        ║ Add comment                                   ║
║  /po/<id>/comments/<mid>/     ║ Delete comment                                ║
║    delete                     ║                                                ║
╚═══════════════════════════════╩════════════════════════════════════════════════╝


╔════════════════════════════════════════════════════════════════════════════════╗
║  🏢 VENDORS / CONTACTS — /api/crm/supply/vendors/                              ║
╠═══════════════════════════════╦════════════════════════════════════════════════╣
║  /vendors/list                ║ List ALL contacts (lugal.crm.customer)        ║
║                               ║ Optional filter: contact_type=vendor│customer ║
║  /vendors/create              ║ Create vendor { name, phone_1, ... }         ║
║  /vendors/<id>/get            ║ Get vendor detail                             ║
║  /vendors/<id>/update         ║ Update vendor                                 ║
║  /vendors/<id>/delete         ║ Soft delete                                   ║
╚═══════════════════════════════╩════════════════════════════════════════════════╝


╔════════════════════════════════════════════════════════════════════════════════╗
║  🤝 NEGOTIATIONS — /api/crm/supply/negotiations/                               ║
╠═══════════════════════════════╦════════════════════════════════════════════════╣
║  /negotiations/list           ║ List negotiations                             ║
║  /negotiations/create         ║ Create { title, vendor_id, ... }             ║
║  /negotiations/<id>/get       ║ Get detail                                    ║
║  /negotiations/<id>/update    ║ Update + status change                        ║
║  /negotiations/<id>/delete    ║ Soft delete                                   ║
╠═══════════════════════════════╬════════════════════════════════════════════════╣
║  COMMENTS:                    ║                                                ║
║  /negotiations/<id>/comments/ ║ List / Add / Delete comments                 ║
║    list │ add │ <id>/delete   ║                                                ║
╚═══════════════════════════════╩════════════════════════════════════════════════╝


╔════════════════════════════════════════════════════════════════════════════════╗
║  📋 ITEM REQUESTS — /api/crm/supply/item_requests/                             ║
╠═══════════════════════════════╦════════════════════════════════════════════════╣
║  /item_requests/list          ║ List requests                                 ║
║  /item_requests/create        ║ Create { product_id, quantity, ... }         ║
║  /item_requests/<id>/get      ║ Get detail                                    ║
║  /item_requests/<id>/update   ║ Update                                        ║
║  /item_requests/<id>/         ║ Change status only → triggers notification    ║
║    update_status              ║ pending→approved│rejected→fulfilled           ║
║  /item_requests/<id>/delete   ║ Soft delete                                   ║
╚═══════════════════════════════╩════════════════════════════════════════════════╝


╔════════════════════════════════════════════════════════════════════════════════╗
║  🏭 CLEARANCE COMPANIES — /api/crm/supply/clearance_companies/                ║
╠═══════════════════════════════╦════════════════════════════════════════════════╣
║  /clearance_companies/list    ║ List companies                                ║
║  /clearance_companies/create  ║ Create { name, phone, ... }                  ║
║  /clearance_companies/<id>/get║ Get detail                                    ║
║  /clearance_companies/<id>/   ║ Update                                        ║
║    update                     ║                                                ║
║  /clearance_companies/<id>/   ║ Soft delete                                   ║
║    delete                     ║                                                ║
╚═══════════════════════════════╩════════════════════════════════════════════════╝


╔════════════════════════════════════════════════════════════════════════════════╗
║  📊 INVENTORY MIN/MAX — /api/crm/supply/inventory/                             ║
╠═══════════════════════════════╦════════════════════════════════════════════════╣
║  /inventory/minmax            ║ List min/max rules                            ║
║  /inventory/minmax/update     ║ Upsert { product_id, min_qty, max_qty }       ║
║  /inventory/minmax/delete     ║ Delete rule by product_id (+ branch_id)       ║
╚═══════════════════════════════╩════════════════════════════════════════════════╝


╔════════════════════════════════════════════════════════════════════════════════╗
║  💬 MESSAGING — /api/crm/supply/conversations/ & messages/                    ║
╠═══════════════════════════════╦════════════════════════════════════════════════╣
║  /conversations/list          ║ Conversations for current user                ║
║  /conversations/<id>/get      ║ Get conversation + messages                   ║
║  /conversations/<id>/archive  ║ Archive DM/group (not team)                  ║
║  /conversations/<id>/rename   ║ Rename group conversation                     ║
║  ─────────────────────────────╫──────────────────────────────────────────────║
║  /messages/list               ║ Messages by thread_id (0=team channel)        ║
║  /messages/create             ║ Send message { thread_id, content }           ║
║  /messages/<id>/delete        ║ Soft-delete (sender only)                     ║
║  ─────────────────────────────╫──────────────────────────────────────────────║
║  /users                       ║ List res.users for participant selection       ║
╚═══════════════════════════════╩════════════════════════════════════════════════╝


╔════════════════════════════════════════════════════════════════════════════════╗
║  🔔 NOTIFICATIONS — /api/crm/supply/notifications/                             ║
╠═══════════════════════════════╦════════════════════════════════════════════════╣
║  /notifications/list          ║ Current user's notifications                  ║
║  /notifications/create        ║ Create notification for a user                ║
║  /notifications/<id>/mark_read║ Mark one as read                              ║
║  /notifications/mark_all_read ║ Mark all read                                 ║
║  /notifications/<id>/delete   ║ Delete notification                           ║
╚═══════════════════════════════╩════════════════════════════════════════════════╝
```

---

## 🔄 BUSINESS FLOW DIAGRAM — تدفق العمل

```
                    ┌─────────────────────────────────────────────────────┐
                    │              SUPPLY CHAIN FLOW                      │
                    │              تدفق سلسلة التوريد                    │
                    └─────────────────────────────────────────────────────┘

  1️⃣ VENDOR                  2️⃣ NEGOTIATION              3️⃣ PURCHASE ORDER
  ─────────                  ───────────                  ───────────────
  /vendors/list              /negotiations/create         /po/create
  /vendors/create     ──►    { vendor_id, product_id, ──► { vendor_id,
  contact_type=vendor          expected_price }             container_id,
                                    │                        line_ids }
                              status flow:                     │
                              open → pending                   │
                              → closed                     status flow:
                                                           draft → confirmed
                                                           → shipped
                                                           → received
                                                           → cancelled

  4️⃣ CONTAINER               5️⃣ DRIVER                   6️⃣ CLEARANCE
  ───────────                ─────────                    ──────────
  /containers/create         /containers/<id>/            /clearance_companies
  { bl_number,       ──►      assign_driver       ──►    /containers/<id>/
    departure_date,           { driver_id }                clearance_delivered
    eta }
       │
  status flow:
  waiting → active
  → at_port ──► /mark_arrived
  → completed


  7️⃣ ITEM REQUEST             8️⃣ INVENTORY MONITORING
  ───────────────             ──────────────────────
  /item_requests/create       /inventory/minmax
  { product_id,               { product_id,
    quantity, branch }          min_qty, max_qty }
       │                              │
  /update_status                 AUTO triggers notification
  pending→approved                when stock < min_qty
  →rejected
  →fulfilled                   notification types:
                                po_created │ container_arrived
                                clearance_done │ low_stock
                                negotiation_update


  9️⃣ COMMUNICATION LAYER
  ──────────────────────
  ┌──────────────────────────────────────────────────────┐
  │  CHATTER (mail.message) on:                          │
  │  • containers → /containers/<id>/comments/           │
  │  • POs        → /po/<id>/comments/                   │
  │  • negotiations → /negotiations/<id>/comments/       │
  ├──────────────────────────────────────────────────────┤
  │  INTERNAL MESSAGING (lugal.supply.internal.message)  │
  │  • team channel (thread_id=0)                        │
  │  • DM between two users                              │
  │  • group conversations                               │
  └──────────────────────────────────────────────────────┘
```

---

## 📌 ENUMS CHEAT SHEET — قيم الـ Enum

```
┌──────────────────────────────────────────────────────────────────────────┐
│ MODEL                         │ FIELD         │ ALLOWED VALUES            │
├───────────────────────────────┼───────────────┼───────────────────────────┤
│ lugal.supply.container        │ status        │ waiting │ active           │
│                               │               │ at_port │ completed        │
│                               ├───────────────┼───────────────────────────┤
│                               │ division      │ europe │ china             │
├───────────────────────────────┼───────────────┼───────────────────────────┤
│ lugal.crm.supply.po           │ status        │ draft │ confirmed          │
│                               │               │ shipped │ received         │
│                               │               │ cancelled                  │
│                               ├───────────────┼───────────────────────────┤
│                               │ division      │ europe │ china             │
├───────────────────────────────┼───────────────┼───────────────────────────┤
│ lugal.supply.negotiation      │ status        │ open │ pending │ closed    │
├───────────────────────────────┼───────────────┼───────────────────────────┤
│ lugal.supply.item.request     │ status        │ pending │ approved         │
│                               │               │ rejected │ fulfilled        │
├───────────────────────────────┼───────────────┼───────────────────────────┤
│ lugal.supply.vendor           │ division      │ europe │ china │ other     │
├───────────────────────────────┼───────────────┼───────────────────────────┤
│ lugal.crm.customer            │ contact_type  │ customer │ vendor │ both   │
├───────────────────────────────┼───────────────┼───────────────────────────┤
│ lugal.supply.conversation     │ type          │ team │ dm │ group          │
├───────────────────────────────┼───────────────┼───────────────────────────┤
│ lugal.supply.notification     │ notif_type    │ po_created                 │
│                               │               │ container_arrived          │
│                               │               │ clearance_done             │
│                               │               │ low_stock                  │
│                               │               │ negotiation_update         │
└───────────────────────────────┴───────────────┴───────────────────────────┘
```

---

## 📊 ENDPOINTS COUNT — إجمالي الـ Endpoints

```
  📦 Containers (+ Attachments + Comments + Driver)  ........  13 endpoints
  🧾 Purchase Orders (+ Lines + Comments)            ........  13 endpoints
  🏢 Vendors / Contacts                              ........   5 endpoints
  🤝 Negotiations (+ Comments)                       ........   8 endpoints
  📋 Item Requests                                   ........   6 endpoints
  🏭 Clearance Companies                             ........   5 endpoints
  📊 Inventory Min/Max                               ........   3 endpoints
  💬 Conversations + Messages + Users                ........  10 endpoints
  🔔 Notifications                                   ........   5 endpoints
                                                     ─────────────────────
  TOTAL                                              ........  68 endpoints
```
