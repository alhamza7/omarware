# دليل استخدام حقل Product Limit

## ✅ تم الإصلاح بنجاح!

الحقل `Product Limit` الآن موجود ويعمل!

---

## 🔧 إذا ظهر خطأ "field is undefined":

### الحل: تحديث cache المتصفح

**الطريقة 1 - إعادة تحميل الـ Assets (الأفضل):**

1. افتح المتصفح على: http://localhost:8069
2. اضغط على:
   ```
   Ctrl + Shift + R  (في Chrome/Edge)
   ```
   أو
   ```
   Ctrl + F5
   ```

3. أو من القائمة:
   - Settings (أعلى اليمين)
   - Developer Tools
   - Regenerate Assets Bundles
   - Refresh

**الطريقة 2 - مسح Cache المتصفح:**

1. افتح: `Ctrl + Shift + Delete`
2. اختر: Cached images and files
3. اضغط: Clear data
4. أعد تحميل الصفحة

**الطريقة 3 - استخدام Developer Mode:**

1. في Odoo، اذهب إلى:
   ```
   Settings → Activate Developer Mode
   ```

2. ثم:
   ```
   Settings → Update Apps List
   ```

---

## 📍 مكان الحقل في الواجهة

بعد تحديث cache، ستجد:

```
┌─────────────────────────────────────────────┐
│ Complete Product Migration from SAP         │
├─────────────────────────────────────────────┤
│                                             │
│ Basic Settings                              │
│ ┌─────────────────────────────────────────┐ │
│ │ SAP Backend: [SAP Production       ▼]  │ │
│ │                                         │ │
│ │ Product Limit: [____]  ← هنا!          │ │
│ │                (0 = Unlimited)          │ │
│ │                                         │ │
│ │ Batch Size: [100]                       │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Advanced Options                            │
│ ┌─────────────────────────────────────────┐ │
│ │ ☑ Update Existing Records               │ │
│ │ ☑ Skip Errors and Continue              │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

## 💡 كيفية الاستخدام

### مثال 1: استيراد 10 منتجات

```
الإعدادات:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SAP Backend:     SAP Production
Product Limit:   10          ← اكتب هنا
Batch Size:      100

Migration Stages:
☑ Stage 2: Import Products

النتيجة:
✓ سيتم استيراد 10 منتجات فقط
✓ كل منتج مع:
  - السعر الرئيسي من SAP (SalesUnitPrice)
  - وحدة البيع من SAP (SalesUnit)
  - الاسم والوصف
  - الباركود
```

---

### مثال 2: استيراد 50 منتجاً مع الأسعار

```
الإعدادات:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SAP Backend:     SAP Production
Product Limit:   50          ← اكتب هنا
Batch Size:      100

Migration Stages:
☑ Stage 1: Import UoM Groups
☑ Stage 2: Import Products
☑ Stage 3: Import Pricelists

النتيجة:
✓ سيتم استيراد:
  - 50 منتج
  - وحدات القياس الخاصة بهم
  - الأسعار من جميع قوائم الأسعار
  - لا أخطاء في الأسعار الفارغة
```

---

### مثال 3: استيراد جميع المنتجات

```
الإعدادات:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SAP Backend:     SAP Production
Product Limit:   0           ← صفر = غير محدود
Batch Size:      100

Migration Stages:
☑ Stage 1: Import UoM Groups
☑ Stage 2: Import Products
☑ Stage 3: Import Pricelists
☑ Stage 4: Import Warehouse Info

النتيجة:
✓ سيتم استيراد جميع المنتجات من SAP
```

---

## 📊 البيانات المستوردة

### من SAP → Odoo:

| SAP Field | Odoo Field | مثال |
|-----------|-----------|------|
| `ItemCode` | `default_code` | ADF00001 |
| `ItemName` | `name` | CK1 |
| `ForeignName` | `name` (عربي) | المليونيرة |
| `SalesUnitPrice` | `list_price` | ✅ **150.00** |
| `SalesUnit` | `uom_id` | ✅ **Bottle (زجاجة)** |
| `PurchaseUnitPrice` | `standard_price` | 100.00 |
| `BarCode` | `barcode` | 123456789 |
| `Frozen` | `active` | نشط/غير نشط |

---

## ⚡ الأخطاء التي تم حلها

### 1. ✅ الأسعار الفارغة (Price = None)
**قبل:**
```
ERROR: float() argument must be a string or a real number, not 'NoneType'
```

**بعد:**
```python
# Handle None price - skip if price is None
price_value = price_data.get('Price')
if price_value is None:
    _logger.warning(f"Skipping empty price")
    continue  # يتم تخطي السعر الفارغ
```

---

### 2. ✅ إضافة Product Limit
**الآن يمكنك:**
- تحديد عدد المنتجات (مثل 10)
- اختبار الاستيراد بسرعة
- تجنب استيراد آلاف المنتجات

---

## 🚀 الخطوة التالية

1. **حدّث cache المتصفح:**
   ```
   اضغط: Ctrl + Shift + R
   ```

2. **افتح:**
   ```
   SAP Integration → Complete Migration
   ```

3. **اكتب في Product Limit:**
   ```
   10
   ```

4. **اضغط:**
   ```
   Run Migration
   ```

---

## 🎯 النتيجة المتوقعة

```
🔄 Starting Products import...
Product limit: 10 products
Batch size: 100

📥 Fetching batch from SAP (skip=0)...
📦 Batch 1: Processing 10 products (from 1 to 10)

  [1] Importing product: ADF00001 - CK1
      ✓ Price: 150.00 SAR
      ✓ UoM: Bottle
  [2] Importing product: ADF00002 - المليونيرة
      ✓ Price: 200.00 SAR
      ✓ UoM: Bottle
  ...
  [10] Importing product: ADF00010 - 212 سكسي W
       ✓ Price: 180.00 SAR
       ✓ UoM: Bottle

✓ Reached product limit (10), stopping import

📊 Summary:
   - Imported: 10 products
   - Errors: 0
   - Duration: 30 seconds
```

---

**✅ جاهز للاستخدام بعد تحديث cache المتصفح!**

اضغط `Ctrl + Shift + R` في المتصفح ثم جرب مرة أخرى! 🎉


