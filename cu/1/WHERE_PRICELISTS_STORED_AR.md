# أين يتم تخزين الأسعار في النظام؟
## Where are Pricelists Stored?

---

## 📍 أماكن تخزين بيانات الأسعار

يتم تخزين بيانات قوائم الأسعار في **3 أماكن رئيسية** في قاعدة بيانات Odoo:

### 1️⃣ جدول `sap_product_pricelist_sync`
**الوظيفة:** تتبع مزامنة الأسعار من SAP إلى Odoo

**المحتويات:**
- معلومات المنتج (`product_id`, `product_code`)
- رقم قائمة الأسعار في SAP (`sap_pricelist_num`)
- السعر (`price`)
- العملة (`currency_id`)
- حالة المزامنة (`sync_status`)
- رابط إلى قائمة الأسعار في Odoo (`odoo_pricelist_id`)
- رابط إلى عنصر السعر (`odoo_pricelist_item_id`)

**الوصول من Odoo:**
- Menu: SAP Integration > Pricelists > Product Pricelist Sync
- Model: `sap.product.pricelist.sync`

---

### 2️⃣ جدول `product_pricelist`
**الوظيفة:** قوائم الأسعار الرئيسية (Headers)

**المحتويات:**
- اسم قائمة الأسعار (مثل: `SAP Price List 1`, `SAP Price List 2`)
- العملة
- حالة التفعيل
- الشركة

**الوصول من Odoo:**
- Menu: Sales > Products > Pricelists
- Model: `product.pricelist`
- Filter: البحث عن قوائم الأسعار التي تحتوي على "SAP" في الاسم

---

### 3️⃣ جدول `product_pricelist_item`
**الوظيفة:** عناصر الأسعار الفردية لكل منتج

**المحتويات:**
- رابط قائمة الأسعار (`pricelist_id`)
- رابط المنتج (`product_id`)
- السعر الثابت (`fixed_price`)
- طريقة الحساب (`compute_price`)
- الحد الأدنى للكمية (`min_quantity`)
- تواريخ الصلاحية (`date_start`, `date_end`)

**الوصول من Odoo:**
- Menu: Sales > Products > Pricelists > (فتح قائمة أسعار) > Price Rules Tab
- Model: `product.pricelist.item`

**هذا الجدول هو الذي يستخدمه:**
- ✅ نقاط البيع (POS)
- ✅ المبيعات (Sales)
- ✅ الموقع الإلكتروني (eCommerce)

---

## 🔄 كيف تعمل المزامنة؟

```
SAP ItemPrices
     ↓
     ↓ (Migration Wizard)
     ↓
1. sap_product_pricelist_sync ← يخزن بيانات المزامنة
     ↓
     ↓ (Auto-create)
     ↓
2. product_pricelist ← ينشئ قوائم الأسعار
     ↓
     ↓ (Auto-create)
     ↓
3. product_pricelist_item ← ينشئ عناصر الأسعار للمنتجات
```

---

## 🔍 كيفية التحقق من البيانات

### من واجهة Odoo:
1. **SAP Integration Menu:**
   - SAP Integration > Pricelists > Product Pricelist Sync

2. **Sales Menu:**
   - Sales > Products > Pricelists
   - ابحث عن: "SAP Price List"

3. **Product Form:**
   - فتح أي منتج
   - Sales Tab > Extra Prices

### من قاعدة البيانات:
```sql
-- عدد سجلات المزامنة
SELECT COUNT(*) FROM sap_product_pricelist_sync;

-- قوائم الأسعار من SAP
SELECT id, name, currency_id, active 
FROM product_pricelist 
WHERE name LIKE '%SAP%';

-- عناصر الأسعار
SELECT COUNT(*) FROM product_pricelist_item;
```

### باستخدام سكريبت Python:
```bash
# استخدم السكريبت الذي أنشأناه
python check_pl.py | python odoo-bin shell -c odoo.conf -d lugal --no-http
```

---

## ⚠️ الوضع الحالي

**النتائج الحالية:**
- ✗ `sap_product_pricelist_sync`: **0 سجلات**
- ✗ `product_pricelist_item`: **0 عناصر**
- ✗ SAP Pricelists: **0 قوائم**

**السبب:**
عملية الـ Migration فشلت بسبب خطأ في الكود (تم إصلاحه الآن).

**الحل:**
يجب إعادة تشغيل عملية الـ Migration بعد إصلاح الخطأ.

---

## ▶️ خطوات إعادة تشغيل Migration

### 1. تشغيل خادم Odoo:
```bash
python odoo-bin -c odoo.conf
```

### 2. الوصول إلى Wizard:
1. افتح متصفح: http://localhost:8069
2. اذهب إلى: **SAP Integration > Migration > Complete Product Migration**

### 3. ضبط الإعدادات:
- ☑ Stage 1: Import UoM Groups
- ☑ Stage 2: Import Products  
- ☑ Stage 3: Import Pricelists ← **هنا يتم إنشاء الأسعار**
- ☑ Stage 4: Import Warehouse Info
- Product Limit: 50 (للاختبار)
- Batch Size: 100

### 4. تشغيل Migration:
- اضغط "Run Complete Migration"
- انتظر حتى تكتمل العملية

### 5. التحقق من النتائج:
```bash
# شغل السكريبت للتحقق
Get-Content check_pl.py | python odoo-bin shell -c odoo.conf -d lugal --no-http
```

---

## 📊 ما سيحدث بعد نجاح Migration:

سترى بيانات مثل:
```
1. Price sync records: 500+
   (Table: sap_product_pricelist_sync)

2. Pricelist items: 500+
   (Table: product_pricelist_item)

3. SAP Pricelists: 2-10
   (Table: product_pricelist)
   
SAP Pricelist Names:
  - SAP Price List 1 (ID: X, Items: 100)
  - SAP Price List 2 (ID: Y, Items: 100)
  ...
```

---

## 🎯 الخلاصة

**الأسعار تُخزن في 3 جداول:**
1. `sap_product_pricelist_sync` - للمزامنة
2. `product_pricelist` - قوائم الأسعار
3. `product_pricelist_item` - الأسعار الفعلية (هذا هو المهم!)

**حالياً:**
- ❌ لا توجد بيانات (Migration لم يكتمل)

**الحل:**
- ✅ تشغيل Odoo
- ✅ تشغيل Migration Wizard
- ✅ اختيار Stage 3: Import Pricelists
- ✅ انتظار الإكمال
- ✅ التحقق من النتائج

---

تم إنشاء هذا الملف: `2025-10-26`






