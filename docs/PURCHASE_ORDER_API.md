# Purchase Order API — دليل كامل
# سلسلة التوريد — أوامر الشراء

**Base URL:** `http://localhost:8070`  
**Auth:** `Authorization: Bearer <token>`  
**Format:** `POST`, `Content-Type: application/json`

---

## 🔐 الحصول على التوكن

```http
POST /lugal/auth/login
```
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
```json
{
  "result": {
    "success": true,
    "data": { "access_token": "eyJhbGci..." }
  }
}
```

---

## 📊 دورة حياة أمر الشراء (Status Flow)

```
                 /confirm              /ship              /receive
[ draft ] ──────────────► [ confirmed ] ──────────► [ shipped ] ──────────► [ received ]
مسودة                        مؤكد                     مشحون                   مستلم
   ▲                           │                          │
   │         /cancel           │         /cancel          │
   │         ◄─────────────────┴──────────────────────────┘
   │
   │         /reopen
   └─────────────────── [ cancelled ] ──► ملغي
```

| الحالة | الاسم | يمكن التعديل؟ | يمكن إضافة بنود؟ |
|--------|--------|--------------|-----------------|
| `draft` | مسودة | ✅ | ✅ |
| `confirmed` | مؤكد | ✅ | ✅ |
| `shipped` | مشحون | ✅ | ✅ |
| `received` | مستلم | ❌ | ❌ |
| `cancelled` | ملغي | ❌ | ❌ |

---

## 📋 جميع الـ Endpoints

| # | Endpoint | الوصف |
|---|----------|-------|
| 1 | `POST /api/crm/supply/po/list` | قائمة الـ POs |
| 2 | `POST /api/crm/supply/po/create` | ⭐ إنشاء PO مع بنود |
| 3 | `POST /api/crm/supply/po/<id>/get` | تفاصيل PO |
| 4 | `POST /api/crm/supply/po/<id>/update` | تعديل الرأسية |
| 5 | `POST /api/crm/supply/po/<id>/delete` | حذف ناعم |
| 6 | `POST /api/crm/supply/po/<id>/confirm` | draft → confirmed |
| 7 | `POST /api/crm/supply/po/<id>/ship` | confirmed → shipped |
| 8 | `POST /api/crm/supply/po/<id>/receive` | shipped → received |
| 9 | `POST /api/crm/supply/po/<id>/cancel` | → cancelled |
| 10 | `POST /api/crm/supply/po/<id>/reopen` | cancelled → draft |
| 11 | `POST /api/crm/supply/po/<id>/lines` | قائمة البنود |
| 12 | `POST /api/crm/supply/po/<id>/lines/add` | إضافة بند |
| 13 | `POST /api/crm/supply/po/<id>/lines/<lid>/update` | تعديل بند |
| 14 | `POST /api/crm/supply/po/<id>/lines/<lid>/delete` | حذف بند |
| 15 | `POST /api/crm/supply/po/suggested` | POs المقترحة |
| 16 | `POST /api/crm/supply/po/<id>/attachments/upload` | رفع ملف (multipart) |
| 17 | `POST /api/crm/supply/po/<id>/attachments/list` | قائمة المرفقات |
| 18 | `POST /api/crm/supply/po/<id>/attachments/<aid>/delete` | حذف مرفق |
| 19 | `POST /api/crm/supply/po/<id>/comments/list` | قائمة التعليقات |
| 20 | `POST /api/crm/supply/po/<id>/comments/add` | إضافة تعليق |
| 21 | `POST /api/crm/supply/po/<id>/comments/<mid>/delete` | حذف تعليق |

---

## 1. قائمة أوامر الشراء

```http
POST /api/crm/supply/po/list
Authorization: Bearer <token>
```

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "page": 1,
    "per_page": 20,
    "status": "draft",
    "vendor_customer_id": 5,
    "container_id": 2,
    "branch_id": 1,
    "division": "europe",
    "search": "PO-2026"
  }
}
```

**الفلاتر المتاحة:**

| الباراميتر | النوع | الوصف |
|------------|-------|-------|
| `page` | int | رقم الصفحة (default: 1) |
| `per_page` | int | عدد النتائج (default: 50) |
| `status` | string/array | `draft` \| `confirmed` \| `shipped` \| `received` \| `cancelled` |
| `vendor_customer_id` | int | فلتر بمعرّف الكونتاكت |
| `vendor_id` | int | فلتر بـ vendor قديم (legacy) |
| `container_id` | int | فلتر بالحاوية |
| `branch_id` | int | فلتر بالفرع |
| `division` | string | `europe` \| `china` |
| `search` | string | بحث بالاسم أو المورد |

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 47,
      "page": 1,
      "per_page": 20,
      "items": [
        {
          "id": 16,
          "name": "PO-2026-001",
          "vendor_customer_id": 5,
          "vendor_customer_name": "شركة النور للعطور",
          "vendor_customer_phone": "07701234567",
          "vendor_id": null,
          "vendor_name": "شركة النور للعطور",
          "division": "europe",
          "currency_id": 1,
          "currency_name": "IQD",
          "container_id": null,
          "container_name": "",
          "branch_id": null,
          "branch_name": "",
          "status": "draft",
          "status_label": "Draft / مسودة",
          "is_suggested": false,
          "line_count": 2,
          "total_amount": 16300.0,
          "created_by_name": "Admin",
          "created_at": "2026-04-04T12:00:00",
          "updated_at": "2026-04-04T12:00:00"
        }
      ]
    }
  }
}
```

---

## 2. ⭐ إنشاء أمر شراء مع بنود (في طلب واحد)

```http
POST /api/crm/supply/po/create
Authorization: Bearer <token>
```

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "name": "PO-2026-001",
    "vendor_customer_id": 5,
    "division": "europe",
    "container_id": 2,
    "branch_id": 1,
    "currency_id": 1,
    "lines": [
      {
        "product_name": "Armani Code 100ml",
        "item_code": "ARM-CODE-100",
        "uom": "Bottle",
        "quantity": 200,
        "unit_price": 45.50,
        "min_qty": 50,
        "max_qty": 500
      },
      {
        "product_name": "Chanel N5 50ml",
        "item_code": "CH-N5-50",
        "uom": "Bottle",
        "quantity": 100,
        "unit_price": 72.00
      }
    ]
  }
}
```

**الحقول الإلزامية:**

| الحقل | الوصف |
|-------|-------|
| `name` | اسم/رقم أمر الشراء |
| `vendor_customer_id` **أو** `vendor_id` | معرّف المورد (أحدهما إلزامي) |

**الحقول الاختيارية:**

| الحقل | الوصف |
|-------|-------|
| `vendor_customer_id` | ⭐ معرّف من `/api/crm/supply/vendors/list` (lugal.crm.customer) |
| `vendor_id` | معرّف من النموذج القديم lugal.supply.vendor (legacy) |
| `division` | `europe` \| `china` |
| `container_id` | ربط بحاوية شحن |
| `branch_id` | ربط بفرع |
| `currency_id` | معرّف العملة |
| `lines` | مصفوفة البنود (اختياري، يمكن إضافتها لاحقاً) |

**حقول كل بند (`lines[]`):**

| الحقل | إلزامي | الوصف |
|-------|--------|-------|
| `product_name` | أحدهما | اسم المنتج |
| `item_code` | أحدهما | رمز الصنف |
| `uom` | لا | وحدة القياس (Bottle, Box, KG...) |
| `quantity` | لا | الكمية (default: 1) |
| `unit_price` | لا | سعر الوحدة (default: 0) |
| `currency_id` | لا | عملة البند |
| `min_qty` | لا | الحد الأدنى |
| `max_qty` | لا | الحد الأقصى |

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "id": 16,
      "name": "PO-2026-001",
      "vendor_customer_id": 5,
      "vendor_customer_name": "شركة النور للعطور",
      "vendor_customer_phone": "07701234567",
      "division": "europe",
      "status": "draft",
      "status_label": "Draft / مسودة",
      "total_amount": 16300.0,
      "line_count": 2,
      "created_by_name": "Admin",
      "created_at": "2026-04-04T12:00:00",
      "lines": [
        {
          "id": 31,
          "sequence": 10,
          "product_name": "Armani Code 100ml",
          "item_code": "ARM-CODE-100",
          "uom": "Bottle",
          "quantity": 200.0,
          "unit_price": 45.5,
          "total_price": 9100.0,
          "currency_id": null,
          "currency_name": "",
          "last_purchase_price": 0.0,
          "last_purchase_date": null,
          "min_qty": 50.0,
          "max_qty": 500.0
        },
        {
          "id": 32,
          "sequence": 10,
          "product_name": "Chanel N5 50ml",
          "item_code": "CH-N5-50",
          "uom": "Bottle",
          "quantity": 100.0,
          "unit_price": 72.0,
          "total_price": 7200.0,
          "currency_id": null,
          "currency_name": "",
          "last_purchase_price": 0.0,
          "last_purchase_date": null,
          "min_qty": 0.0,
          "max_qty": 0.0
        }
      ]
    }
  }
}
```

---

## 3. تفاصيل أمر شراء

```http
POST /api/crm/supply/po/16/get
Authorization: Bearer <token>
```
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```
الرد: نفس response الـ create أعلاه.

---

## 4. تعديل رأسية الـ PO

```http
POST /api/crm/supply/po/16/update
Authorization: Bearer <token>
```
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "container_id": 3,
    "branch_id": 2,
    "division": "china",
    "currency_id": 2,
    "is_suggested": false
  }
}
```

> ⚠️ لتغيير الحالة استخدم الـ endpoints المخصصة (confirm / ship / receive / cancel).
> التعديل مسموح في جميع الحالات ما عدا `received`.

---

## 5. تدفق الحالات — Status Transitions

### تأكيد الطلب — draft → confirmed

```http
POST /api/crm/supply/po/16/confirm
Authorization: Bearer <token>
```
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

**Response:**
```json
{
  "result": {
    "success": true,
    "message": "PO PO-2026-001 status changed to: confirmed",
    "data": {
      "id": 16,
      "status": "confirmed",
      "status_label": "Confirmed / مؤكد"
    }
  }
}
```

**خطأ — لا توجد بنود:**
```json
{
  "result": {
    "success": false,
    "error": "Cannot confirm a PO with no lines",
    "code": 422
  }
}
```

---

### شحن الطلب — confirmed → shipped

```http
POST /api/crm/supply/po/16/ship
Authorization: Bearer <token>
```
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

**Response:**
```json
{
  "result": {
    "success": true,
    "message": "PO PO-2026-001 status changed to: shipped",
    "data": { "id": 16, "status": "shipped", "status_label": "Shipped / مشحون" }
  }
}
```

---

### استلام الطلب — shipped → received

```http
POST /api/crm/supply/po/16/receive
Authorization: Bearer <token>
```
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

> ✅ عند الاستلام يُرسَل إشعار `container_arrived` تلقائياً إذا كان الـ PO مرتبطاً بحاوية.

---

### إلغاء الطلب

```http
POST /api/crm/supply/po/16/cancel
Authorization: Bearer <token>
```
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

> ✅ يعمل من: `draft`, `confirmed`, `shipped`
> ❌ لا يعمل من: `received`

---

### إعادة فتح الطلب الملغي — cancelled → draft

```http
POST /api/crm/supply/po/16/reopen
Authorization: Bearer <token>
```
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

---

### أخطاء الحالات — State Errors

```json
{
  "result": {
    "success": false,
    "error": "Cannot move to \"confirmed\" from \"received\". PO must be in status: \"draft\"",
    "code": 409
  }
}
```

---

## 6. حذف أمر الشراء

```http
POST /api/crm/supply/po/16/delete
Authorization: Bearer <token>
```
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

> ⚠️ الحذف مسموح فقط من `draft` أو `cancelled`. يجب إلغاء الطلب أولاً.

**Response:**
```json
{
  "result": {
    "success": true,
    "data": { "id": 16, "deleted": true }
  }
}
```

---

## 7. إدارة البنود (PO Lines)

### قائمة البنود

```http
POST /api/crm/supply/po/16/lines
Authorization: Bearer <token>
```
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "po_id": 16,
      "po_name": "PO-2026-001",
      "total_amount": 16300.0,
      "items": [
        {
          "id": 31,
          "sequence": 10,
          "product_name": "Armani Code 100ml",
          "item_code": "ARM-CODE-100",
          "uom": "Bottle",
          "quantity": 200.0,
          "unit_price": 45.5,
          "total_price": 9100.0,
          "currency_id": null,
          "currency_name": "",
          "last_purchase_price": 0.0,
          "last_purchase_date": null,
          "min_qty": 50.0,
          "max_qty": 500.0
        }
      ]
    }
  }
}
```

---

### إضافة بند

```http
POST /api/crm/supply/po/16/lines/add
Authorization: Bearer <token>
```
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "product_name": "Dior Sauvage 100ml",
    "item_code": "DIOR-SAU-100",
    "uom": "Bottle",
    "quantity": 150,
    "unit_price": 60.00,
    "min_qty": 30,
    "max_qty": 300
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "id": 33,
      "product_name": "Dior Sauvage 100ml",
      "item_code": "DIOR-SAU-100",
      "quantity": 150.0,
      "unit_price": 60.0,
      "total_price": 9000.0
    }
  }
}
```

---

### تعديل بند

```http
POST /api/crm/supply/po/16/lines/31/update
Authorization: Bearer <token>
```
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "quantity": 250,
    "unit_price": 43.00,
    "last_purchase_price": 44.50,
    "last_purchase_date": "2026-01-15"
  }
}
```

---

### حذف بند

```http
POST /api/crm/supply/po/16/lines/33/delete
Authorization: Bearer <token>
```
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

**Response:**
```json
{ "result": { "success": true, "data": { "id": 33, "deleted": true } } }
```

---

## 8. رفع المرفقات

```http
POST /api/crm/supply/po/16/attachments/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `file` أو `files[]` | File | الملف المرفوع (إلزامي) |
| `label` | string | اسم مخصص للملف (اختياري) |

**الأنواع المسموحة:** PDF, JPEG, PNG, WEBP, GIF, DOC, DOCX, XLS, XLSX  
**الحجم الأقصى:** 25 MB

**مثال cURL:**
```bash
curl -X POST http://localhost:8070/api/crm/supply/po/16/attachments/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@invoice.pdf" \
  -F "label=Supplier Invoice"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "po_id": 16,
    "attachments": [
      {
        "id": 88,
        "name": "Supplier Invoice",
        "mimetype": "application/pdf",
        "size": 102400,
        "url": "http://localhost:8070/web/content/88?access_token=abc123...",
        "uploaded_by_name": "Admin",
        "created_at": "2026-04-04T12:30:00"
      }
    ]
  }
}
```

---

### قائمة المرفقات

```http
POST /api/crm/supply/po/16/attachments/list
Authorization: Bearer <token>
```
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "po_id": 16,
      "po_name": "PO-2026-001",
      "total": 2,
      "attachments": [
        {
          "id": 88,
          "name": "Supplier Invoice",
          "mimetype": "application/pdf",
          "size": 102400,
          "url": "http://localhost:8070/web/content/88?access_token=abc123...",
          "uploaded_by_name": "Admin",
          "created_at": "2026-04-04T12:30:00"
        }
      ]
    }
  }
}
```

---

### حذف مرفق

```http
POST /api/crm/supply/po/16/attachments/88/delete
Authorization: Bearer <token>
```
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

---

## 9. التعليقات والملاحظات (Comments)

### قائمة التعليقات

```http
POST /api/crm/supply/po/16/comments/list
Authorization: Bearer <token>
```
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": { "page": 1, "per_page": 50 }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 3,
      "page": 1,
      "items": [
        {
          "id": 201,
          "body": "تم التواصل مع المورد وتأكيد الأسعار",
          "type": "comment",
          "author_id": 2,
          "author_name": "Admin",
          "created_at": "2026-04-04T13:00:00"
        },
        {
          "id": 202,
          "body": "ملاحظة داخلية: الشحن يتأخر أسبوعاً",
          "type": "note",
          "author_id": 2,
          "author_name": "Admin",
          "created_at": "2026-04-04T14:00:00"
        }
      ]
    }
  }
}
```

---

### إضافة تعليق

```http
POST /api/crm/supply/po/16/comments/add
Authorization: Bearer <token>
```
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "body": "تم التواصل مع المورد وتأكيد الأسعار",
    "is_note": false
  }
}
```

| الحقل | الوصف |
|-------|-------|
| `body` | نص التعليق (إلزامي) |
| `is_note` | `false` = تعليق عام / `true` = ملاحظة داخلية |

---

### حذف تعليق

```http
POST /api/crm/supply/po/16/comments/201/delete
Authorization: Bearer <token>
```
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

> ⚠️ يمكن الحذف فقط من صاحب التعليق أو المدير (admin).

---

## 10. POs المقترحة

```http
POST /api/crm/supply/po/suggested
Authorization: Bearer <token>
```
```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

---

## 🔄 السيناريو الكامل — End-to-End Flow

```
1️⃣  تسجيل دخول
    POST /lugal/auth/login → token

2️⃣  اختيار مورد
    POST /api/crm/supply/vendors/list → { items: [{id: 5, name: "..."}] }

3️⃣  إنشاء PO مع البنود
    POST /api/crm/supply/po/create
    { name, vendor_customer_id: 5, lines: [...] }
    → { id: 16, status: "draft" }

4️⃣  رفع فاتورة المورد
    POST /api/crm/supply/po/16/attachments/upload
    multipart: file=invoice.pdf

5️⃣  إضافة تعليق
    POST /api/crm/supply/po/16/comments/add
    { body: "تم التحقق من الأسعار" }

6️⃣  تأكيد الطلب
    POST /api/crm/supply/po/16/confirm → status: "confirmed"

7️⃣  ربط بحاوية شحن (اختياري)
    POST /api/crm/supply/po/16/update
    { container_id: 2 }

8️⃣  تحديث حالة الشحن
    POST /api/crm/supply/po/16/ship → status: "shipped"

9️⃣  استلام البضاعة
    POST /api/crm/supply/po/16/receive → status: "received"
    ✅ إشعار container_arrived يُرسَل تلقائياً
```

---

## ⚠️ جدول الأخطاء الشائعة

| الخطأ | السبب | الحل |
|-------|-------|------|
| `name is required` | نسيت `name` في create | أضف `"name": "PO-..."` |
| `vendor_customer_id or vendor_id is required` | لم تحدد المورد | أضف `vendor_customer_id` |
| `Vendor contact X not found` | معرّف مورد خاطئ | تحقق من `/vendors/list` |
| `Cannot confirm a PO with no lines` | PO بدون بنود | أضف بنداً واحداً على الأقل |
| `Cannot move to "confirmed" from "received"` | خطأ في تسلسل الحالات | راجع دورة الحياة أعلاه |
| `Cannot delete a PO in status "confirmed"` | الـ PO مؤكد | استخدم `/cancel` أولاً |
| `Cannot add lines to a received PO` | الـ PO مستلم | لا يمكن التعديل بعد الاستلام |
| `Unauthorized` | التوكن منتهي | أعد تسجيل الدخول |

---

## 📊 حقول الـ PO Object الكاملة

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `id` | int | المعرف الداخلي |
| `name` | string | رقم أمر الشراء |
| `vendor_customer_id` | int | معرّف المورد (lugal.crm.customer) |
| `vendor_customer_name` | string | اسم المورد |
| `vendor_customer_phone` | string | هاتف المورد |
| `vendor_id` | int | معرّف المورد القديم (legacy) |
| `vendor_name` | string | اسم المورد (من أي مصدر) |
| `division` | string | `europe` \| `china` |
| `currency_id` | int | معرّف العملة |
| `currency_name` | string | اسم العملة (IQD, USD...) |
| `container_id` | int | معرّف الحاوية المرتبطة |
| `container_name` | string | اسم الحاوية |
| `branch_id` | int | معرّف الفرع |
| `branch_name` | string | اسم الفرع |
| `status` | string | الحالة الحالية |
| `status_label` | string | الحالة بالعربي والإنجليزي |
| `is_suggested` | bool | هل هو PO مقترح؟ |
| `line_count` | int | عدد البنود |
| `total_amount` | float | الإجمالي (محسوب من البنود) |
| `created_by_id` | int | معرّف من أنشأ الطلب |
| `created_by_name` | string | اسم من أنشأ الطلب |
| `created_at` | datetime | تاريخ الإنشاء |
| `updated_at` | datetime | تاريخ آخر تعديل |
| `lines` | array | بنود الطلب (عند include_lines) |

---

## 📊 حقول بند الـ PO Line Object

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `id` | int | معرّف البند |
| `sequence` | int | ترتيب العرض |
| `product_name` | string | اسم المنتج |
| `item_code` | string | رمز الصنف |
| `uom` | string | وحدة القياس |
| `quantity` | float | الكمية |
| `unit_price` | float | سعر الوحدة |
| `total_price` | float | الإجمالي (quantity × unit_price) |
| `currency_id` | int | معرّف العملة |
| `currency_name` | string | اسم العملة |
| `last_purchase_price` | float | آخر سعر شراء (للمرجعية) |
| `last_purchase_date` | date | تاريخ آخر شراء |
| `min_qty` | float | الحد الأدنى للمخزون |
| `max_qty` | float | الحد الأقصى للمخزون |
