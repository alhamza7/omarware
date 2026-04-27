# تحويل الكوتيشن إلى سيل أوردر — دليل API الكامل
# Quotation → Sale Order — Complete API Guide

**Base URL:** `http://localhost:8070`
**Auth:** `Authorization: Bearer <token>` — احصل على التوكن من `/lugal/auth/login`

---

## 📊 دورة حياة الطلب (State Machine)

```
                    ┌─────────────────────────────┐
                    │                             │
        /create     ▼          /mark_sent         │
   ──────────► [ draft ]  ──────────────► [ sent ] │
               (كوتيشن)      (كوتيشن مرسل)          │
                    │                    │         │
                    │    /confirm        │ /confirm │
                    ▼                    ▼         │
               [ sale ] ◄────────────────          │
             (أمر البيع)                            │
                    │                              │
                    │ /cancel         /reset_to_draft
                    ▼                              │
               [ cancel ] ─────────────────────────┘
               (ملغي)
                    
[ sale ] ──/lock──► [ sale + locked=true ]
         ◄─/unlock──
```

### الحالات

| الحالة (`state`) | الاسم | الوصف |
|---|---|---|
| `draft` | Quotation / كوتيشن | الطلب في مرحلة المسودة — قابل للتعديل |
| `sent` | Quotation Sent / مرسل | تم إرسال الكوتيشن للعميل — قابل للتعديل |
| `sale` | Sales Order / أمر بيع | **تم التأكيد** — لا يمكن التعديل إلا بعد unlock |
| `cancel` | Cancelled / ملغي | تم الإلغاء — يمكن إعادته لـ draft |

---

## 🔐 الحصول على التوكن (Authentication)

```http
POST /lugal/auth/login
Content-Type: application/json
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

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "access_token": "eyJhbGciOiJIUzI1NiIs...",
      "token_type": "bearer"
    }
  }
}
```

> استخدم `access_token` في كل طلب: `Authorization: Bearer eyJhbGci...`

---

## 📋 الخطوة 1 — إنشاء كوتيشن (Create Quotation)

```http
POST /api/crm/sale/orders/create
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "partner_id": 42,
    "client_order_ref": "REF-CUST-001",
    "commitment_date": "2026-05-01 00:00:00",
    "note": "يرجى التوصيل في الصباح",
    "pricelist_id": 1,
    "lines": [
      {
        "product_id": 101,
        "quantity": 10.0,
        "price_unit": 250.00,
        "discount": 5.0,
        "description": "عطر أرماني كود 100 مل"
      },
      {
        "product_id": 205,
        "quantity": 5.0,
        "price_unit": 180.00
      }
    ]
  }
}
```

| الحقل | إلزامي | الوصف |
|---|---|---|
| `partner_id` | ✅ نعم | معرّف العميل (`res.partner` أو `lugal.crm.customer.partner_id`) |
| `lines` | لا | قائمة المنتجات (يمكن إضافتها لاحقاً) |
| `pricelist_id` | لا | معرّف قائمة الأسعار |
| `client_order_ref` | لا | رقم مرجعي من العميل |
| `commitment_date` | لا | تاريخ التسليم المتعهد به |
| `note` | لا | ملاحظات داخلية |

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "id": 1055,
      "name": "S00042",
      "state": "draft",
      "state_label": "Quotation / كوتيشن",
      "locked": false,
      "partner_id": 42,
      "partner_name": "شركة النور للعطور",
      "pricelist_name": "Public Pricelist",
      "currency_name": "IQD",
      "date_order": "2026-04-04T10:30:00",
      "commitment_date": "2026-05-01T00:00:00",
      "client_order_ref": "REF-CUST-001",
      "amount_untaxed": 3250.00,
      "amount_tax": 0.00,
      "amount_total": 3250.00,
      "invoice_status": "nothing",
      "lines": [
        {
          "id": 2001,
          "sequence": 10,
          "product_id": 101,
          "product_name": "أرماني كود 100 مل",
          "product_sku": "ARM-CODE-100",
          "product_uom_qty": 10.0,
          "product_uom": "Units",
          "price_unit": 250.00,
          "discount": 5.0,
          "price_subtotal": 2375.00,
          "price_total": 2375.00
        }
      ]
    }
  }
}
```

> ✅ الطلب الآن في حالة `draft` — رقمه التلقائي `S00042`

---

## ✏️ الخطوة 2 — تعديل الكوتيشن (اختيارية)

### إضافة منتج

```http
POST /api/crm/sale/orders/1055/lines/add
Authorization: Bearer <token>
```

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "product_id": 310,
    "quantity": 3.0,
    "price_unit": 95.00,
    "discount": 0.0,
    "description": "عطر شانيل N5 50 مل"
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "id": 2002,
      "product_id": 310,
      "product_name": "شانيل N5 50 مل",
      "product_uom_qty": 3.0,
      "price_unit": 95.00,
      "price_subtotal": 285.00
    }
  }
}
```

---

### تعديل كمية منتج

```http
POST /api/crm/sale/orders/1055/lines/2001/update
Authorization: Bearer <token>
```

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "product_uom_qty": 15.0,
    "discount": 10.0
  }
}
```

---

### حذف منتج

```http
POST /api/crm/sale/orders/1055/lines/2002/delete
Authorization: Bearer <token>
```

```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

**Response:** `{ "result": { "success": true, "data": { "id": 2002, "deleted": true } } }`

---

## 📤 الخطوة 3 — إرسال الكوتيشن للعميل (اختيارية)

تحويل الحالة: `draft` ──► `sent`

```http
POST /api/crm/sale/orders/1055/mark_sent
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
      "id": 1055,
      "name": "S00042",
      "state": "sent",
      "state_label": "Quotation Sent / كوتيشن مرسل"
    }
  }
}
```

> 💡 هذه الخطوة اختيارية. يمكن التأكيد مباشرة من `draft` دون المرور بـ `sent`.

---

## ✅ الخطوة 4 — تأكيد الطلب (THE MAIN STEP)

### تحويل: `draft` أو `sent` ──► `sale`

```http
POST /api/crm/sale/orders/1055/confirm
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

**Response — نجاح:**
```json
{
  "result": {
    "success": true,
    "message": "Order S00042 confirmed successfully — state is now: sale",
    "data": {
      "id": 1055,
      "name": "S00042",
      "state": "sale",
      "state_label": "Sales Order / أمر بيع",
      "locked": false,
      "date_order": "2026-04-04T11:00:00",
      "amount_total": 3535.00,
      "invoice_status": "to invoice",
      "lines": [ /* ... */ ]
    }
  }
}
```

**Response — الطلب مؤكد مسبقاً:**
```json
{
  "result": {
    "success": false,
    "error": "Order is already confirmed",
    "code": 409
  }
}
```

**Response — الطلب ملغي:**
```json
{
  "result": {
    "success": false,
    "error": "Cannot confirm a cancelled order. Reset to draft first using /reset_to_draft",
    "code": 409
  }
}
```

> ✅ بعد التأكيد: الحالة = `sale`، تم إنشاء أوامر التسليم تلقائياً

---

## 🔒 الخطوة 5 — قفل الطلب (اختيارية)

بعد التأكيد يمكن قفل الطلب لمنع أي تعديل:

```http
POST /api/crm/sale/orders/1055/lock
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
    "data": { "id": 1055, "state": "sale", "locked": true }
  }
}
```

### فك القفل

```http
POST /api/crm/sale/orders/1055/unlock
Authorization: Bearer <token>
```

```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

---

## ❌ إلغاء الطلب

```http
POST /api/crm/sale/orders/1055/cancel
Authorization: Bearer <token>
```

```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

> ⚠️ الطلب المقفل يجب فك قفله أولاً قبل الإلغاء.

**Response:**
```json
{
  "result": {
    "success": true,
    "data": { "id": 1055, "state": "cancel" }
  }
}
```

---

## 🔄 إعادة الطلب لمرحلة المسودة

من `cancel` أو `sent` ──► `draft`

```http
POST /api/crm/sale/orders/1055/reset_to_draft
Authorization: Bearer <token>
```

```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

---

## 📄 استعلام الطلبات

### قائمة جميع الكوتيشنات

```http
POST /api/crm/sale/orders/list
Authorization: Bearer <token>
```

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "state": "draft",
    "page": 1,
    "per_page": 20
  }
}
```

> فلترة بالحالة: `state: "draft"` | `"sent"` | `"sale"` | `"cancel"`
> أو بدون `state` لإظهار الكل

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 12,
      "page": 1,
      "per_page": 20,
      "items": [
        {
          "id": 1055,
          "name": "S00042",
          "state": "draft",
          "state_label": "Quotation / كوتيشن",
          "partner_name": "شركة النور للعطور",
          "amount_total": 3250.00,
          "date_order": "2026-04-04T10:30:00",
          "invoice_status": "nothing"
        }
      ]
    }
  }
}
```

### تفاصيل طلب واحد

```http
POST /api/crm/sale/orders/1055/get
Authorization: Bearer <token>
```

```json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

---

## 📊 جدول جميع الـ Endpoints

| # | Endpoint | الوصف | الحالة المطلوبة |
|---|---|---|---|
| 1 | `POST /api/crm/sale/orders/list` | قائمة الطلبات | أي |
| 2 | `POST /api/crm/sale/orders/<id>/get` | تفاصيل طلب | أي |
| 3 | `POST /api/crm/sale/orders/create` | **إنشاء كوتيشن** | جديد |
| 4 | `POST /api/crm/sale/orders/<id>/update` | تعديل الرأسية | draft / sent |
| 5 | `POST /api/crm/sale/orders/<id>/lines/add` | إضافة منتج | draft / sent |
| 6 | `POST /api/crm/sale/orders/<id>/lines/<lid>/update` | تعديل منتج | draft / sent |
| 7 | `POST /api/crm/sale/orders/<id>/lines/<lid>/delete` | حذف منتج | draft / sent |
| 8 | `POST /api/crm/sale/orders/<id>/mark_sent` | **إرسال للعميل** | draft → sent |
| 9 | `POST /api/crm/sale/orders/<id>/confirm` | **⭐ تأكيد الطلب** | draft/sent → sale |
| 10 | `POST /api/crm/sale/orders/<id>/cancel` | إلغاء | أي (غير مقفل) |
| 11 | `POST /api/crm/sale/orders/<id>/reset_to_draft` | إعادة لمسودة | cancel / sent |
| 12 | `POST /api/crm/sale/orders/<id>/lock` | قفل الطلب | sale |
| 13 | `POST /api/crm/sale/orders/<id>/unlock` | فك القفل | sale + locked |

---

## 🚀 السيناريو الكامل — Flow من البداية للنهاية

```
1️⃣  POST /lugal/auth/login
     → احصل على access_token

2️⃣  POST /api/crm/sale/orders/create
     → params: { partner_id: 42, lines: [...] }
     → id = 1055, state = "draft"

3️⃣  [اختياري] POST /api/crm/sale/orders/1055/lines/add
     → أضف منتجات إضافية

4️⃣  [اختياري] POST /api/crm/sale/orders/1055/mark_sent
     → state: "draft" → "sent"

5️⃣  ⭐ POST /api/crm/sale/orders/1055/confirm
     → state: "draft"/"sent" → "sale"
     → أمر التسليم ينشأ تلقائياً

6️⃣  [اختياري] POST /api/crm/sale/orders/1055/lock
     → locked = true
```

---

## ⚠️ قواعد مهمة

| الحالة | يمكن تعديل البنود؟ | يمكن التأكيد؟ | يمكن الإلغاء؟ |
|---|---|---|---|
| `draft` | ✅ نعم | ✅ نعم | ✅ نعم |
| `sent` | ✅ نعم | ✅ نعم | ✅ نعم |
| `sale` (غير مقفل) | ✅ نعم | ❌ (مؤكد) | ✅ نعم |
| `sale` (مقفل) | ❌ لا | ❌ | ❌ (افك القفل أولاً) |
| `cancel` | ❌ لا | ❌ (reset أولاً) | ❌ (مؤكد) |

---

## 🔑 حقول الاستجابة الأساسية (Order Object)

| الحقل | النوع | الوصف |
|---|---|---|
| `id` | int | المعرف الداخلي |
| `name` | string | رقم الطلب مثل `S00042` |
| `state` | string | `draft` \| `sent` \| `sale` \| `cancel` |
| `state_label` | string | الاسم بالعربي والإنجليزي |
| `locked` | bool | هل الطلب مقفل؟ |
| `partner_id` | int | معرف العميل |
| `partner_name` | string | اسم العميل |
| `amount_untaxed` | float | المبلغ قبل الضريبة |
| `amount_tax` | float | قيمة الضريبة |
| `amount_total` | float | الإجمالي النهائي |
| `invoice_status` | string | `nothing` \| `to invoice` \| `invoiced` |
| `date_order` | datetime | تاريخ الطلب/التأكيد |
| `lines` | array | بنود الطلب (عند include_lines=true) |

---

## 🐛 أخطاء شائعة وحلولها

| الخطأ | السبب | الحل |
|---|---|---|
| `Order is already confirmed` | تحاول تأكيد طلب `state=sale` | لا حاجة للتأكيد مرة ثانية |
| `Cannot confirm a cancelled order` | الطلب ملغي | استخدم `/reset_to_draft` ثم `/confirm` |
| `Order is locked` | الطلب مقفل | استخدم `/unlock` أولاً |
| `Only draft orders can be marked as sent` | تحاول mark_sent على طلب غير draft | تأكد من الحالة الحالية |
| `partner_id is required` | نسيت partner_id في create | أضف `"partner_id": <id>` |
| `Product X not found` | معرف منتج خاطئ | تحقق من `product_id` |
| `Unauthorized` | التوكن غير موجود أو منتهي | أعد تسجيل الدخول من `/lugal/auth/login` |
