# POS Perfume — External REST API v1

> **Base URL:** `https://<your-odoo-host>/api/pos_perfume/v1`

---

## المصادقة / Authentication

يدعم الـ API **طريقتين** للمصادقة — اختر الأنسب لتطبيقك:

---

### الطريقة الأولى: API Key — Bearer Token ⭐ (الأفضل للتطبيقات الخارجية)

**مزايا:** Stateless — لا session — لا cookies — مثالي للـ mobile apps والـ backend services.

#### الخطوة 1 — توليد API Key من Odoo

1. افتح Odoo → **Settings** → **Users & Companies** → **Users**
2. اختر المستخدم المطلوب
3. اضغط تبويب **"API Keys"**
4. اضغط **"New API Key"** → أدخل وصفاً → احفظ المفتاح (يظهر مرة واحدة فقط)

#### الخطوة 2 — استخدام المفتاح في كل طلب

```http
GET /api/pos_perfume/v1/setup
Authorization: Bearer <your_api_key_here>
```

**مثال cURL:**
```bash
curl -X GET "https://your-odoo-host/api/pos_perfume/v1/setup" \
  -H "Authorization: Bearer abc123yourapikey456"
```

**مثال JavaScript (fetch):**
```javascript
const API_KEY = 'abc123yourapikey456';
const BASE = 'https://your-odoo-host';

const res = await fetch(`${BASE}/api/pos_perfume/v1/setup`, {
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  }
});
const data = await res.json();
```

**مثال Python (requests):**
```python
import requests

API_KEY = 'abc123yourapikey456'
BASE = 'https://your-odoo-host'

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

res = requests.get(f'{BASE}/api/pos_perfume/v1/setup', headers=headers)
print(res.json())
```

---

### الطريقة الثانية: Session Cookie (للـ Browser / SPA)

#### الخطوة 1 – تسجيل الدخول (مرة واحدة)

```http
POST /web/session/authenticate
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "db": "your_database_name",
    "login": "your_username",
    "password": "your_password"
  }
}
```

**الاستجابة:**
```json
{
  "result": {
    "uid": 2,
    "name": "Ahmed",
    "session_id": "abc123..."
  }
}
```

استخدم الـ **Cookie** المُرجعة في كل الطلبات اللاحقة.
في الـ **Postman**: أضف كوكي `session_id=<value>` في كل طلب.

```javascript
// مثال JavaScript مع session
const res = await fetch(`${BASE}/api/pos_perfume/v1/setup`, {
  credentials: 'include'   // ← مهم لإرسال الـ cookie
});
```

---

### مقارنة الطريقتين

| | API Key (Bearer) | Session Cookie |
|---|---|---|
| **الاستخدام الأفضل** | Mobile / Backend / Postman | Browser / SPA |
| **Stateless** | ✅ نعم | ❌ يحتاج session |
| **CSRF** | ✅ محمي تلقائياً | يحتاج عناية |
| **التوصية** | ⭐ للتطبيقات الخارجية | للواجهات الداخلية |

---

## نسق الاستجابة الموحّد / Response Format

كل endpoint يرجع:
```json
{
  "success": true,
  "message": "OK",
  "data": { ... }
}
```
أو في حالة خطأ:
```json
{
  "success": false,
  "error": "Error description"
}
```

---

## CORS

كل الـ endpoints تدعم CORS وترجع الهيدر:
```
Access-Control-Allow-Origin: *
```

---

---

# 1. الجلسة والإعدادات الأولية / Session & Setup

## GET /session
معلومات المستخدم الحالي وسعر الصرف.

```http
GET /api/pos_perfume/v1/session
```

**مثال استجابة:**
```json
{
  "success": true,
  "data": {
    "user_id": 2,
    "user_name": "Ahmed",
    "company_name": "NBS",
    "exchange_rate": 1470.0
  }
}
```

---

## GET /setup
جميع البيانات اللازمة لتشغيل الـ POS الخارجي في طلب واحد.

```http
GET /api/pos_perfume/v1/setup
```

**مثال استجابة:**
```json
{
  "success": true,
  "data": {
    "pricelists": [
      { "id": 1, "name": "Price list 1", "currency_id": 2 }
    ],
    "default_pricelist_id": 1,
    "warehouses": [
      { "id": 1, "name": "Main Warehouse", "code": "WH" }
    ],
    "users": [
      { "id": 2, "name": "Ahmed" }
    ],
    "invoice_types": [
      { "key": "1", "label": "زبون محل" },
      { "key": "2", "label": "شركات توصيل" }
    ],
    "exchange_rate": 1470.0,
    "currency": "USD",
    "secondary_currency": "IQD"
  }
}
```

---

# 2. الإعدادات / Settings

## GET /settings
```http
GET /api/pos_perfume/v1/settings
```

## PUT /settings
تحديث سعر الصرف الافتراضي.
```http
PUT /api/pos_perfume/v1/settings
Content-Type: application/json

{ "exchange_rate": 1490.0 }
```

---

# 3. العملاء / Customers

## GET /customers
بحث وقائمة العملاء.

```http
GET /api/pos_perfume/v1/customers?query=Ahmed&limit=50&offset=0
```

| Query Param | Type   | Description               |
|-------------|--------|---------------------------|
| `query`     | string | البحث بالاسم/هاتف/رمز     |
| `limit`     | int    | عدد النتائج (افتراضي 50)   |
| `offset`    | int    | بداية الصفحة              |

**مثال استجابة:**
```json
{
  "success": true,
  "data": {
    "total": 120,
    "offset": 0,
    "limit": 50,
    "items": [
      {
        "id": 10,
        "name": "Ahmed Ali",
        "phone": "07701234567",
        "mobile": "",
        "email": "ahmed@example.com"
      }
    ]
  }
}
```

---

## GET /customers/:id
```http
GET /api/pos_perfume/v1/customers/10
```

---

## POST /customers
إنشاء عميل جديد.

```http
POST /api/pos_perfume/v1/customers
Content-Type: application/json

{
  "name": "Ahmed Ali",
  "phone": "07701234567",
  "mobile": "07901234567",
  "email": "ahmed@example.com",
  "street": "Karada",
  "city": "Baghdad",
  "ref": "C001"
}
```

---

## PUT /customers/:id
تحديث بيانات عميل.

```http
PUT /api/pos_perfume/v1/customers/10
Content-Type: application/json

{ "phone": "07711111111" }
```

---

# 4. المنتجات / Products

## GET /products
بحث وقائمة المنتجات.

```http
GET /api/pos_perfume/v1/products?query=oud&limit=80&pricelist_id=1
```

**مثال استجابة:**
```json
{
  "success": true,
  "data": {
    "total": 500,
    "items": [
      {
        "id": 42,
        "name": "Oud Al Shams",
        "default_code": "P001",
        "foreign_name": "عود الشمس",
        "uom_id": { "id": 1, "name": "Units" },
        "list_price": 25.0,
        "qty_available": 100.0,
        "color_class": "green",
        "badge_text": "NBS"
      }
    ]
  }
}
```

---

## GET /products/:id
تفاصيل منتج واحد مع قائمة UoMs والمخازن.

```http
GET /api/pos_perfume/v1/products/42?pricelist_id=1
```

---

## POST /products/data
بيانات منتج كاملة (أسعار + UoMs + المخازن + المخزون).
مطابق لـ `/pos_perfume/get_product_data` الداخلي.

```http
POST /api/pos_perfume/v1/products/data
Content-Type: application/json

{
  "product_id": 42,
  "pricelist_id": 1,
  "uom_id": null,
  "warehouse_id": null
}
```

**مثال استجابة:**
```json
{
  "success": true,
  "data": {
    "product_id": 42,
    "product_name": "Oud Al Shams",
    "product_uom_id": 1,
    "product_uom_name": "Units",
    "price_unit": 25.0,
    "available_qty": 100.0,
    "available_uoms": [
      { "id": 1, "name": "Units", "price": 25.0 },
      { "id": 5, "name": "Box (12)", "price": 280.0 }
    ],
    "warehouses": [
      { "id": 1, "name": "Main WH", "code": "WH", "quantity": 100.0 },
      { "id": 2, "name": "Branch 1", "code": "BR1", "quantity": 25.0 }
    ],
    "default_code": "P001",
    "foreign_name": "عود الشمس",
    "color_class": "green",
    "badge_text": "NBS"
  }
}
```

---

## POST /products/uom_price
سعر المنتج عند تغيير وحدة القياس.

```http
POST /api/pos_perfume/v1/products/uom_price
Content-Type: application/json

{
  "product_id": 42,
  "pricelist_id": 1,
  "uom_id": 5
}
```

**مثال استجابة:**
```json
{ "success": true, "data": { "price_unit": 280.0 } }
```

---

# 5. الطلبيات / Orders

## GET /orders
قائمة الطلبيات مع فلاتر.

```http
GET /api/pos_perfume/v1/orders?state=sale&limit=20&offset=0
```

| Query Param   | Type   | Description                          |
|---------------|--------|--------------------------------------|
| `query`       | string | بحث برقم الطلبية                    |
| `state`       | string | draft / quotation / sale / done / cancel |
| `partner_id`  | int    | فلتر حسب العميل                      |
| `date_from`   | string | من تاريخ (YYYY-MM-DD)               |
| `date_to`     | string | إلى تاريخ (YYYY-MM-DD)              |
| `limit`       | int    | (افتراضي 50)                         |
| `offset`      | int    | بداية الصفحة                         |

---

## GET /orders/:id
تفاصيل طلبية كاملة مع جميع السطور.

```http
GET /api/pos_perfume/v1/orders/123
```

**مثال استجابة:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "name": "S00042",
    "date": "2026-02-23T10:30:00",
    "state": "sale",
    "partner_id": { "id": 10, "name": "Ahmed Ali", "phone": "07701234567" },
    "pricelist_id": { "id": 1, "name": "Price list 1" },
    "exchange_rate": 1470.0,
    "amount_subtotal": 100.0,
    "amount_discount": 5.0,
    "amount_tax": 0.0,
    "amount_total": 95.0,
    "amount_total_iqd": 139650.0,
    "invoice_type": "1",
    "note": "",
    "sale_order_id": { "id": 55, "name": "SO055", "state": "sale" },
    "sap_doc_num": "12345",
    "sap_doc_entry": 55,
    "sap_synced": true,
    "order_lines": [
      {
        "id": 301,
        "sequence": 10,
        "product_id": { "id": 42, "name": "Oud Al Shams", "default_code": "P001" },
        "product_uom_id": { "id": 1, "name": "Units" },
        "warehouse_id": { "id": 1, "name": "Main WH" },
        "quantity": 2.0,
        "unit_price": 25.0,
        "discount_percent": 0.0,
        "price_after_discount": 25.0,
        "line_subtotal": 50.0,
        "discount_amount": 0.0,
        "line_total": 50.0,
        "available_qty": 100.0,
        "custom_product_name": ""
      }
    ]
  }
}
```

---

## POST /orders
إنشاء طلبية جديدة.

```http
POST /api/pos_perfume/v1/orders
Content-Type: application/json

{
  "partner_id": 10,
  "pricelist_id": 1,
  "invoice_type": "1",
  "note": "ملاحظة",
  "exchange_rate": 1470.0,
  "order_lines": [
    {
      "product_id": 42,
      "product_uom_id": 1,
      "warehouse_id": 1,
      "quantity": 2.0,
      "unit_price": 25.0,
      "discount_percent": 0.0,
      "custom_product_name": ""
    }
  ]
}
```

> `order_lines` اختيارية — يمكن إضافة السطور لاحقاً.

---

## PUT /orders/:id
تحديث بيانات رأس الطلبية (بدون السطور).

```http
PUT /api/pos_perfume/v1/orders/123
Content-Type: application/json

{
  "partner_id": 11,
  "note": "ملاحظة معدّلة",
  "invoice_type": "3",
  "exchange_rate": 1490.0
}
```

---

## DELETE /orders/:id
إلغاء طلبية (تحويلها إلى حالة cancel).

```http
DELETE /api/pos_perfume/v1/orders/123
```

---

# 6. سطور الطلبية / Order Lines

## POST /orders/:id/lines
إضافة سطر جديد للطلبية.

```http
POST /api/pos_perfume/v1/orders/123/lines
Content-Type: application/json

{
  "product_id": 42,
  "product_uom_id": 1,
  "warehouse_id": 1,
  "quantity": 3.0,
  "unit_price": 25.0,
  "discount_percent": 5.0,
  "custom_product_name": ""
}
```

---

## PUT /orders/:id/lines/:line_id
تحديث سطر موجود.

```http
PUT /api/pos_perfume/v1/orders/123/lines/301
Content-Type: application/json

{
  "quantity": 5.0,
  "discount_percent": 10.0
}
```

---

## DELETE /orders/:id/lines/:line_id
حذف سطر من الطلبية.

```http
DELETE /api/pos_perfume/v1/orders/123/lines/301
```

---

# 7. إجراءات الطلبية / Order Actions

## POST /orders/:id/confirm
تأكيد الطلبية → ينشئ sale.order ويزامن مع SAP.

```http
POST /api/pos_perfume/v1/orders/123/confirm
```

**مثال استجابة:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "name": "S00042",
    "state": "sale",
    "sale_order_id": { "id": 55, "name": "SO055", "state": "sale" },
    "sap_synced": true,
    "sap_doc_num": "12345",
    "sap_doc_entry": 55
  }
}
```

---

## POST /orders/:id/quotation
تحويل الطلبية إلى عرض سعر.

```http
POST /api/pos_perfume/v1/orders/123/quotation
```

---

## POST /orders/:id/cancel
إلغاء الطلبية.

```http
POST /api/pos_perfume/v1/orders/123/cancel
```

---

## POST /orders/:id/draft
إعادة الطلبية الملغاة إلى حالة Draft.

```http
POST /api/pos_perfume/v1/orders/123/draft
```

---

# 8. واتساب / WhatsApp

## POST /orders/:id/send_whatsapp
إرسال الفاتورة كرسالة نصية عبر واتساب.

```http
POST /api/pos_perfume/v1/orders/123/send_whatsapp
```

---

## POST /orders/:id/send_whatsapp_image
إرسال الفاتورة كصورة عبر واتساب.

```http
POST /api/pos_perfume/v1/orders/123/send_whatsapp_image
```

---

# 9. التقارير / Reports

## GET /orders/:id/report
تحميل الفاتورة كـ PDF.

```http
GET /api/pos_perfume/v1/orders/123/report
GET /api/pos_perfume/v1/orders/123/report?download=false   ← inline
```

يرجع ملف PDF مباشرة (`Content-Type: application/pdf`).

---

# 10. SAP

## POST /orders/:id/sync_sap
إعادة مزامنة الطلبية مع SAP.

```http
POST /api/pos_perfume/v1/orders/123/sync_sap
```

---

# 11. سعر الصرف على الطلبية / Order Exchange Rate

## PUT /orders/:id/exchange_rate
تحديث سعر الصرف لطلبية معينة.

```http
PUT /api/pos_perfume/v1/orders/123/exchange_rate
Content-Type: application/json

{ "exchange_rate": 1490.0 }
```

> إذا أرسلت body فارغة يتم أخذ السعر الافتراضي من الإعدادات.

---

# 12. قوائم مساعدة / Convenience Lists

## GET /pricelists
```http
GET /api/pos_perfume/v1/pricelists
```

## GET /warehouses
```http
GET /api/pos_perfume/v1/warehouses
```

---

# سير العمل الكامل / Full POS Workflow

```
1. GET  /setup                              ← تحميل بيانات POS عند الفتح
2. GET  /customers?query=ahmed              ← بحث عميل
3. POST /customers                          ← إنشاء عميل جديد (اختياري)
4. GET  /products?query=oud                 ← بحث منتج
5. POST /products/data  { product_id, pricelist_id }   ← تفاصيل المنتج
6. POST /products/uom_price  { ... }        ← سعر UoM عند التغيير
7. POST /orders  { partner_id, order_lines }  ← إنشاء طلبية
8. POST /orders/:id/lines                   ← إضافة سطور
9. PUT  /orders/:id/lines/:line_id          ← تعديل سطر
10. PUT /orders/:id  { invoice_type, note } ← تحديث رأس الطلبية
11. POST /orders/:id/confirm                ← تأكيد وإرسال SAP
12. GET  /orders/:id/report                 ← طباعة الفاتورة PDF
13. POST /orders/:id/send_whatsapp          ← إرسال واتساب
```

---

# مثال كامل بـ JavaScript / Full JS Example (API Key)

```javascript
const BASE    = 'https://your-odoo-host';
const API_KEY = 'your_api_key_here';   // ← من Odoo → Settings → Users → API Keys

/** Headers ثابتة لكل الطلبات */
const HEADERS = {
  'Content-Type':  'application/json',
  'Authorization': `Bearer ${API_KEY}`,
};

/** مساعد عام لإرسال الطلبات */
async function apiCall(endpoint, method = 'GET', body = null) {
  const opts = { method, headers: HEADERS };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE}/api/pos_perfume/v1${endpoint}`, opts);
  return res.json();
}

// 1. Get setup data (on POS boot)
const setup = await apiCall('/setup');
console.log('Pricelists:', setup.data.pricelists);

// 2. Search customers
const customers = await apiCall('/customers?query=Ahmed');

// 3. Get product full data
const productData = await apiCall('/products/data', 'POST', {
  product_id: 42,
  pricelist_id: 1
});
console.log('UoMs:', productData.data.available_uoms);

// 4. Create order
const order = await apiCall('/orders', 'POST', {
  partner_id: 10,
  pricelist_id: 1,
  invoice_type: '1',
  order_lines: [
    { product_id: 42, product_uom_id: 1, warehouse_id: 1, quantity: 2, unit_price: 25 }
  ]
});
const orderId = order.data.id;

// 5. Add another line
await apiCall(`/orders/${orderId}/lines`, 'POST', {
  product_id: 55, product_uom_id: 1, warehouse_id: 1, quantity: 1, unit_price: 40
});

// 6. Confirm order → creates sale.order + SAP sync
const confirmed = await apiCall(`/orders/${orderId}/confirm`, 'POST');
console.log('SAP Doc:', confirmed.data.sap_doc_num);

// 7. Send WhatsApp
await apiCall(`/orders/${orderId}/send_whatsapp`, 'POST');

// 8. Download PDF report
const pdfUrl = `${BASE}/api/pos_perfume/v1/orders/${orderId}/report`;
window.open(pdfUrl + '?Authorization=' + API_KEY); // or use fetch with headers
```

---

# مثال Python كامل / Full Python Example (API Key)

```python
import requests

BASE    = 'https://your-odoo-host'
API_KEY = 'your_api_key_here'
HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type':  'application/json',
}

def api(endpoint, method='GET', body=None):
    url = f'{BASE}/api/pos_perfume/v1{endpoint}'
    return requests.request(method, url, headers=HEADERS, json=body).json()

# 1. Load setup
setup = api('/setup')

# 2. Search products
products = api('/products?query=oud')

# 3. Get product data
product = api('/products/data', 'POST', {'product_id': 42, 'pricelist_id': 1})

# 4. Create order
order = api('/orders', 'POST', {
    'partner_id': 10,
    'pricelist_id': 1,
    'order_lines': [
        {'product_id': 42, 'product_uom_id': 1, 'warehouse_id': 1,
         'quantity': 3, 'unit_price': 25.0}
    ]
})
order_id = order['data']['id']

# 5. Confirm
confirmed = api(f'/orders/{order_id}/confirm', 'POST')
print(f"SAP: {confirmed['data']['sap_doc_num']}")

# 6. Download PDF
pdf_res = requests.get(
    f'{BASE}/api/pos_perfume/v1/orders/{order_id}/report',
    headers=HEADERS
)
with open(f'order_{order_id}.pdf', 'wb') as f:
    f.write(pdf_res.content)
```

---

# ملاحظات مهمة / Important Notes

| الموضوع | التفصيل |
|---------|---------|
| **الكوكيز** | مطلوبة في كل طلب — استخدم `credentials: 'include'` في fetch |
| **CSRF** | معطّل في جميع endpoints الخارجية |
| **الحالات** | draft → quotation → sale → done / cancel |
| **SAP** | التزامن يحدث تلقائياً عند التأكيد |
| **IQD** | يُحسب بضرب `amount_total × exchange_rate` |
| **UoM** | وحدات القياس تأتي من SAP UoM Groups |
