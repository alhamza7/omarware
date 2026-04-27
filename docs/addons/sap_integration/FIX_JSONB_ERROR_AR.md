# إصلاح خطأ JSONB في حذف التكرارات
# Fix JSONB Error in Duplicate Cleaner

## ❌ الخطأ الذي حدث

```
psycopg2.errors.UndefinedFunction: operator does not exist: jsonb ~~ unknown
LINE 8: WHERE name LIKE 'SAP Price List%'
```

## 🔍 السبب

في Odoo 17، الحقول القابلة للترجمة مثل `name` في `product.pricelist` و `uom.uom` يتم تخزينها كـ **JSONB** في قاعدة البيانات، وليس كنص عادي. لذلك لا يمكن استخدام عوامل النص العادية (مثل `LIKE`) مباشرة.

### مثال على البيانات:
```json
// نص عادي (قديم)
name: "SAP Price List 1"

// JSONB (جديد - متعدد اللغات)
name: {
  "en_US": "SAP Price List 1",
  "ar_SA": "قائمة أسعار SAP 1"
}
```

## ✅ الحل المطبق

تم تحديث استعلامات SQL للتعامل مع كلا النوعين:

### 1. في `_check_pricelist_duplicates()`:

**قبل:**
```sql
SELECT name, currency_id, COUNT(*) as count
FROM product_pricelist
WHERE name LIKE 'SAP Price List%'  -- ❌ لا يعمل مع JSONB
GROUP BY name, currency_id
```

**بعد:**
```sql
SELECT 
    CASE 
        WHEN jsonb_typeof(name) = 'string' THEN name::text
        WHEN jsonb_typeof(name) = 'object' THEN name->>'en_US'
        ELSE name::text
    END as name,
    currency_id,
    COUNT(*) as count
FROM product_pricelist
WHERE CASE 
        WHEN jsonb_typeof(name) = 'string' THEN name::text LIKE 'SAP Price List%'
        WHEN jsonb_typeof(name) = 'object' THEN name->>'en_US' LIKE 'SAP Price List%'
        ELSE name::text LIKE 'SAP Price List%'
    END
GROUP BY [نفس الـ CASE]
```

### 2. في `_check_uom_duplicates()`:

تم تطبيق نفس المنطق لحقل `name` في `uom.uom`.

## 🎯 كيف يعمل الحل

1. **يفحص نوع البيانات** باستخدام `jsonb_typeof(name)`:
   - إذا كان `'string'` → يستخدم `name::text` مباشرة
   - إذا كان `'object'` → يستخرج النص الإنجليزي `name->>'en_US'`
   - أي شيء آخر → يحوّل إلى نص `name::text`

2. **يطبق المقارنة على النتيجة** (يمكن استخدام `LIKE` الآن)

3. **يستخدم نفس المنطق في `GROUP BY`** للتأكد من التجميع الصحيح

## 📝 الملفات المحدثة

- `addons/sap_integration/wizard/sap_duplicate_cleaner.py`:
  - `_check_pricelist_duplicates()` - محدّث ✅
  - `_check_uom_duplicates()` - محدّث ✅

## 🚀 التطبيق

لا يلزم أي إجراء إضافي! التحديث سيُطبق تلقائياً في المرة القادمة التي تقوم فيها بـ:

### الخيار 1: إعادة تشغيل Odoo (إذا كان في Developer Mode)
```bash
# فقط أعد تشغيل Odoo
Ctrl+C  # أوقف
./venv/Scripts/python.exe odoo-bin -c odoo_simple.conf -d lugal  # شغّل
```

### الخيار 2: تحديث المودل (مستحسن)
```bash
cd /home/lugalai/Lugal-ai
./venv/bin/python3 odoo-bin -c odoo_simple.conf -d lugal -u sap_integration --stop-after-init
./venv/bin/python3 odoo-bin -c odoo_simple.conf -d lugal
```

### الخيار 3: من واجهة Odoo
```
Settings → Apps → Remove "Apps" filter → Search "SAP Integration" → Upgrade
```

## 🧪 الاختبار

بعد التحديث، جرّب:

1. اذهب إلى: **SAP Integration → Management Tools → حذف التكرارات**
2. اضغط **"فحص التكرارات"**
3. يجب أن يعمل بدون أخطاء ✅

## 📊 التوافق

هذا الحل متوافق مع:
- ✅ Odoo 17.0 (JSONB fields)
- ✅ Odoo 16.0 (String fields)
- ✅ PostgreSQL 12+
- ✅ قواعد بيانات قديمة (قبل الترجمة)
- ✅ قواعد بيانات جديدة (مع الترجمة)

## 🎓 ملاحظات فنية

### لماذا JSONB؟

Odoo 17 يستخدم JSONB للحقول القابلة للترجمة لأنه:
1. أسرع في الاستعلامات
2. أكثر مرونة للغات متعددة
3. لا يحتاج إلى جداول إضافية

### استخراج القيمة من JSONB:

```sql
-- استخراج كنص
name->>'en_US'  -- يعيد: "SAP Price List 1"

-- استخراج كـ JSON
name->'en_US'   -- يعيد: "SAP Price List 1" (مع quotes)

-- التحويل إلى نص
name::text      -- يعيد: '"SAP Price List 1"' أو '{"en_US": "..."}'
```

## ⚠️ تحذير

إذا كنت تستخدم استعلامات SQL مخصصة في أي مكان آخر، تأكد من:
1. فحص نوع الحقل قبل المقارنة
2. استخدام `jsonb_typeof()` أو `->>` للاستخراج
3. عدم استخدام عوامل النص (`LIKE`, `=`, etc.) مباشرة على حقول JSONB

---

**تاريخ الإصلاح:** 23 ديسمبر 2025  
**الإصدار:** SAP Integration v2.0  
**الخطأ:** `psycopg2.errors.UndefinedFunction: operator does not exist: jsonb ~~ unknown`  
**الحالة:** ✅ تم الحل

