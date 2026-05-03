# 🔗 دليل التكامل مع SAP Business One Service Layer

## 📋 نظرة عامة

تم تطوير نظام الجرد ليتكامل مع **SAP Business One Service Layer** لجلب الكميات الموجودة فعلياً في SAP عند القيام بالجرد. هذا التكامل يتيح للمستخدمين:

✅ **مشاهدة الكميات الموجودة في SAP لحظياً** عند مسح الباركود  
✅ **مطابقة الكمية المجرودة مع كمية SAP** للتحقق من الدقة  
✅ **عرض الكميات المحجوزة والمتاحة** من SAP  
✅ **دعم البحث بالباركود وكود الصنف** من SAP مباشرة  

---

## 🚀 المتطلبات

### البنية التحتية
- **SAP Business One** مع تفعيل Service Layer
- **Service Layer URL** قابل للوصول من السيرفر
- **بيانات دخول SAP** (اسم المستخدم وكلمة المرور)
- **Node.js** إصدار 14 أو أحدث على السيرفر

### الحزم المطلوبة (مثبتة مسبقاً)
```json
{
  "axios": "^1.x.x",
  "https": "مدمج في Node.js"
}
```

---

## ⚙️ التكوين

### 1. إعداد ملف التكوين

قم بتحرير ملف **`src/sap_config.js`**:

```javascript
module.exports = {
  // عنوان Service Layer الخاص بك
  SAP_SERVICE_LAYER_URL: process.env.SAP_SERVICE_LAYER_URL || 'https://sap-server:50000/b1s/v1',
  
  // بيانات الشركة والدخول
  SAP_COMPANY_DB: process.env.SAP_COMPANY_DB || 'COMPANY_DB_NAME',
  SAP_USERNAME: process.env.SAP_USERNAME || 'manager',
  SAP_PASSWORD: process.env.SAP_PASSWORD || 'your_password',
  
  // تمكين/تعطيل التكامل
  SAP_ENABLED: process.env.SAP_ENABLED === 'true' || false,
  
  // مطابقة المخازن
  WAREHOUSE_MAPPING: {
    1: 'WH01',  // المخزن 1 في النظام = WH01 في SAP
    2: 'WH02',  // المخزن 2 في النظام = WH02 في SAP
    // ... إلخ
  },
};
```

### 2. استخدام متغيرات البيئة (مُوصى به)

أنشئ ملف **`.env`** في المجلد الرئيسي:

```env
# تفعيل التكامل مع SAP
SAP_ENABLED=true

# عنوان Service Layer
SAP_SERVICE_LAYER_URL=https://192.168.1.100:50000/b1s/v1

# بيانات الدخول
SAP_COMPANY_DB=SBODEMOUS
SAP_USERNAME=manager
SAP_PASSWORD=your_secure_password

# مطابقة المخازن (اختياري)
SAP_WH_01=WH01
SAP_WH_02=WH02
SAP_WH_03=WH03
```

ثم قم بتثبيت وتحميل `dotenv`:

```bash
npm install dotenv
```

وأضف في بداية `server.js`:

```javascript
require('dotenv').config();
```

---

## 🔧 الملفات المضافة/المعدلة

### الملفات الجديدة:
1. **`src/sap_config.js`** - ملف التكوين الرئيسي
2. **`src/sap_client.js`** - إدارة الاتصال مع SAP
3. **`دليل_التكامل_مع_SAP.md`** - هذا الملف

### الملفات المعدلة:
1. **`src/server.js`** - إضافة endpoints جديدة لـ SAP
2. **`mobile_app_runner/lib/api.dart`** - إضافة دوال جلب كميات SAP
3. **`mobile_app_runner/lib/screens/inventory_screen.dart`** - عرض كميات SAP في الواجهة

---

## 📡 الـ APIs المتاحة

### 1. جلب كمية صنف بكود الصنف

**Endpoint:**
```
GET /api/sap/item-quantity/:itemCode
```

**Header:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "itemCode": "ITEM001",
    "itemName": "اسم الصنف",
    "warehouseCode": "WH01",
    "quantity": 150,
    "committed": 20,
    "available": 130
  }
}
```

### 2. جلب كمية صنف بالباركود

**Endpoint:**
```
GET /api/sap/item-by-barcode/:barcode
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "itemCode": "ITEM001",
    "itemName": "اسم الصنف",
    "barcode": "6281234567890",
    "warehouseCode": "WH01",
    "quantity": 150,
    "committed": 20,
    "available": 130
  }
}
```

### 3. حالة الاتصال بـ SAP

**Endpoint:**
```
GET /api/sap/status
```

**Response:**
```json
{
  "enabled": true,
  "connected": true,
  "serviceLayerUrl": "https://sap-server:50000/b1s/v1"
}
```

### 4. تحديث API الجرد الحالي

**Endpoint:**
```
GET /api/items/by-code/:code
```

**Response (مع كمية SAP):**
```json
{
  "item": {
    "id": 123,
    "item_code": "ITEM001",
    "item_name": "اسم الصنف",
    "barcode": "6281234567890",
    "uom": "PCS"
  },
  "lastCount": {
    "qty": 145,
    "username": "أحمد",
    "created_at": "2025-12-21 10:30:00"
  },
  "sapQuantity": {
    "itemCode": "ITEM001",
    "warehouseCode": "WH01",
    "quantity": 150,
    "committed": 20,
    "available": 130
  }
}
```

---

## 💡 كيفية الاستخدام

### في تطبيق الموبايل:

1. **عند مسح الباركود:**
   - يتم جلب معلومات الصنف من قاعدة البيانات المحلية
   - يتم جلب الكمية من SAP تلقائياً (إن كان مفعلاً)
   - يظهر صندوق حوار يعرض:
     - معلومات الصنف
     - آخر جرد (إن وجد)
     - **كمية SAP:** الكمية الموجودة، المحجوزة، والمتاحة

2. **عند البحث اليدوي:**
   - نفس السلوك - يتم جلب كمية SAP عند اختيار الصنف

3. **مثال على الواجهة:**

```
╔═══════════════════════════════════╗
║     إضافة كمية                    ║
╠═══════════════════════════════════╣
║ ITEM001 — اسم الصنف (PCS)        ║
║ باركود: 6281234567890            ║
╠═══════════════════════════════════╣
║ 📊 كمية SAP:                     ║
║ ┌───────────────────────────────┐ ║
║ │ ☁️  الكمية الموجودة: 150     │ ║
║ │    الكمية المحجوزة: 20       │ ║
║ │ ✅  الكمية المتاحة: 130      │ ║
║ └───────────────────────────────┘ ║
╠═══════════════════════════════════╣
║ الكمية: [____]                   ║
╠═══════════════════════════════════╣
║  [إلغاء]         [حفظ]           ║
╚═══════════════════════════════════╝
```

---

## 🔒 الأمان

### شهادات SSL
⚠️ **تحذير:** الكود الحالي يتجاهل التحقق من شهادات SSL لأغراض التطوير.

**للإنتاج:** قم بتعديل `src/sap_client.js`:

```javascript
this.client = axios.create({
  baseURL: this.baseURL,
  httpsAgent: new https.Agent({
    rejectUnauthorized: true, // تفعيل التحقق من الشهادات
    ca: fs.readFileSync('path/to/ca-certificate.pem'), // شهادة CA
  }),
});
```

### كلمات المرور
🔐 **لا تضع كلمات المرور في الكود مباشرة!**

استخدم متغيرات البيئة:
```bash
SAP_PASSWORD=secure_password_here
```

### صلاحيات المستخدم
تأكد أن مستخدم SAP لديه صلاحيات:
- قراءة جداول الأصناف (Items)
- قراءة معلومات المخازن (Warehouses)
- قراءة ItemWarehouseInfo

---

## 🐛 استكشاف الأخطاء

### 1. SAP غير متصل

**الأعراض:**
```json
{
  "error": "sap_disabled",
  "message": "SAP integration is not enabled"
}
```

**الحل:**
- تأكد من `SAP_ENABLED=true` في `.env` أو `sap_config.js`

---

### 2. خطأ في تسجيل الدخول

**الأعراض:**
```
❌ Failed to login to SAP B1: Request failed with status code 401
```

**الحل:**
- تحقق من اسم المستخدم وكلمة المرور
- تأكد من اسم قاعدة البيانات صحيح (`SAP_COMPANY_DB`)
- تحقق من صلاحيات المستخدم في SAP

---

### 3. الصنف غير موجود في SAP

**Response:**
```json
{
  "error": "not_found_in_sap",
  "message": "Item not found in SAP"
}
```

**الأسباب المحتملة:**
- كود الصنف مختلف بين النظام و SAP
- الباركود غير مسجل في SAP
- الصنف غير نشط (Inactive) في SAP

**الحل:**
- تأكد من تطابق أكواد الأصناف
- سجل الباركودات في SAP

---

### 4. خطأ SSL Certificate

**الأعراض:**
```
Error: unable to verify the first certificate
```

**الحل:**
- للتطوير: الكود الحالي يتجاهل الشهادات
- للإنتاج: أضف شهادة CA الصحيحة

---

### 5. timeout أو بطء في الاستجابة

**الحل:**
```javascript
// في sap_client.js
this.client = axios.create({
  baseURL: this.baseURL,
  timeout: 10000, // 10 ثواني
  // ...
});
```

---

## 📊 مطابقة المخازن

يجب مطابقة أرقام المخازن في النظام مع أكواد المخازن في SAP:

| رقم المخزن في النظام | كود المخزن في SAP | ملاحظات |
|----------------------|-------------------|---------|
| 1                    | WH01              | المخزن الرئيسي |
| 2                    | WH02              | مخزن الفرع الأول |
| 3                    | WH03              | مخزن الفرع الثاني |
| ...                  | ...               | ... |
| 18                   | WH18              | المخزن 18 |

**تعديل المطابقة:**

في `src/sap_config.js`:
```javascript
WAREHOUSE_MAPPING: {
  1: 'MAIN',     // تغيير من WH01 إلى MAIN
  2: 'BRANCH1',  // تغيير من WH02 إلى BRANCH1
  // ... إلخ
}
```

---

## 🔄 إدارة الجلسة (Session Management)

### الجلسة التلقائية
- النظام يقوم بتسجيل الدخول تلقائياً عند الحاجة
- الجلسة تُجدد تلقائياً قبل انتهائها بـ 5 دقائق
- عند إيقاف السيرفر، يتم تسجيل الخروج تلقائياً

### إعادة تسجيل الدخول
في حالة انتهاء الجلسة، النظام يعيد المحاولة تلقائياً:

```javascript
// في sap_client.js - يتم تلقائياً
if (error.response && error.response.status === 401) {
  this.sessionId = null;
  await this.ensureLoggedIn();
  return this.getItemQuantity(itemCode, warehouseId);
}
```

---

## 🧪 الاختبار

### 1. اختبار حالة الاتصال

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:3000/api/sap/status
```

**النتيجة المتوقعة:**
```json
{
  "enabled": true,
  "connected": true,
  "serviceLayerUrl": "https://sap-server:50000/b1s/v1"
}
```

### 2. اختبار جلب كمية صنف

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:3000/api/sap/item-quantity/ITEM001
```

### 3. اختبار البحث بالباركود

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:3000/api/sap/item-by-barcode/6281234567890
```

---

## 📈 الأداء

### تحسينات مقترحة للإنتاج:

1. **Cache الاستعلامات:**
```javascript
// إضافة cache بسيط
const cache = new Map();
const CACHE_TTL = 60000; // دقيقة واحدة

async getItemQuantity(itemCode, warehouseId) {
  const key = `${itemCode}-${warehouseId}`;
  const cached = cache.get(key);
  
  if (cached && Date.now() - cached.time < CACHE_TTL) {
    return cached.data;
  }
  
  const data = await this._fetchFromSAP(itemCode, warehouseId);
  cache.set(key, { data, time: Date.now() });
  return data;
}
```

2. **Connection Pooling:**
استخدم `keep-alive` مع axios:
```javascript
const http = require('http');
const https = require('https');

this.client = axios.create({
  httpAgent: new http.Agent({ keepAlive: true }),
  httpsAgent: new https.Agent({ keepAlive: true }),
});
```

---

## 📱 التحديث المستقبلي

### ميزات مقترحة:

1. ✨ **مزامنة ثنائية الاتجاه:** رفع نتائج الجرد إلى SAP تلقائياً
2. 📊 **تقارير الفروقات:** مقارنة الجرد مع SAP وإنشاء تقارير الفروقات
3. 🔄 **استيراد الأصناف:** جلب الأصناف من SAP مباشرة
4. 🏷️ **دعم أسعار الأصناف:** عرض أسعار البيع من SAP
5. 📦 **دعم Serial Numbers/Batch Numbers:** تتبع الأرقام التسلسلية

---

## 🆘 الدعم

### سجلات الأخطاء

يتم تسجيل جميع العمليات في console:

```bash
# لعرض السجلات
node src/server.js

# ستشاهد رسائل مثل:
✅ Successfully logged in to SAP B1 Service Layer
❌ Failed to get item quantity from SAP: ...
```

### معلومات Debug

لتفعيل مزيد من التفاصيل، أضف في بداية `sap_client.js`:

```javascript
// تفعيل axios interceptors للـ logging
this.client.interceptors.request.use(request => {
  console.log('🔵 SAP Request:', request.method, request.url);
  return request;
});

this.client.interceptors.response.use(
  response => {
    console.log('🟢 SAP Response:', response.status, response.config.url);
    return response;
  },
  error => {
    console.log('🔴 SAP Error:', error.message);
    return Promise.reject(error);
  }
);
```

---

## 📝 الملاحظات النهائية

1. ✅ **التكامل اختياري:** النظام يعمل بشكل طبيعي حتى لو كان SAP معطل
2. 🔒 **الأمان أولاً:** استخدم HTTPS و شهادات صحيحة في الإنتاج
3. ⚡ **الأداء:** فكر في استخدام cache للاستعلامات المتكررة
4. 📊 **المراقبة:** راقب أداء SAP Service Layer وأوقات الاستجابة
5. 🔄 **النسخ الاحتياطي:** احتفظ بنسخة احتياطية من بيانات الجرد محلياً

---

## 📚 مراجع إضافية

- [SAP Business One Service Layer Documentation](https://help.sap.com/docs/SAP_BUSINESS_ONE/68a6c6eeab3a4ca5a72cbf3b4c537b5b/4d7a3c1e6c784aa79c6c3c59e8d5cebe.html)
- [SAP B1 Service Layer API Reference](https://api.sap.com/api/SAPB1/overview)

---

**تم بحمد الله ✨**

*آخر تحديث: 21 ديسمبر 2025*






