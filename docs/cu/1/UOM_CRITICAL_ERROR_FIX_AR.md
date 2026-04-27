# خطأ حرج - وحدات القياس الأساسية مفقودة ❌

## 🔴 **المشكلة الحالية:**

```
ValueError: No record found for unique ID uom.product_uom_hour. It may have been deleted.
```

**السبب:** عند حذف البيانات سابقاً، تم حذف وحدات القياس الأساسية (Hours, Days, etc.) التي يحتاجها النظام!

---

## ⚠️ **خطورة المشكلة:**

- ❌ لا يمكن فتح صفحات المنتجات
- ❌ لا يمكن إنشاء منتجات جديدة
- ❌ النظام معطّل بشكل كبير
- ❌ جداول UoM تالفة أو غير مكتملة

---

## ✅ **الحلول المقترحة:**

### **الحل 1: استعادة نسخة احتياطية (الأفضل)** ⭐

إذا كان لديك نسخة احتياطية من قاعدة البيانات:

```bash
# 1. أوقف Odoo
# 2. احذف قاعدة البيانات الحالية
dropdb lugal

# 3. استعد من النسخة الاحتياطية
pg_restore -U odoo_user -d lugal backup_file.dump

# 4. أعد تشغيل Odoo
python odoo-bin -c odoo.conf
```

---

### **الحل 2: إعادة تثبيت وحدة UoM** 🔧

```bash
# 1. أوقف Odoo الحالي

# 2. قم بحذف وإعادة تثبيت وحدة uom
python odoo-bin -c odoo.conf -d lugal -i uom --stop-after-init

# 3. أعد تشغيل Odoo
python odoo-bin -c odoo.conf
```

---

### **الحل 3: إنشاء قاعدة بيانات جديدة** 🆕

إذا لم تكن هناك بيانات مهمة:

```bash
# 1. أوقف Odoo

# 2. احذف قاعدة البيانات الحالية
dropdb lugal

# 3. أنشئ قاعدة بيانات جديدة
createdb -U odoo_user lugal

# 4. ابدأ Odoo (سينشئ قاعدة بيانات جديدة)
python odoo-bin -c odoo.conf -i base,stock,sale,point_of_sale,sap_integration
```

---

### **الحل 4: إصلاح يدوي عبر SQL** 🛠️

**تحذير:** متقدم ومعقد!

```sql
-- 1. الاتصال بقاعدة البيانات
psql -U odoo_user -d lugal

-- 2. التحقق من الجداول
SELECT table_name FROM information_schema.tables 
WHERE table_name LIKE '%uom%';

-- 3. إذا كانت الجداول موجودة، تحديث وحدة uom
-- من خلال Odoo:
python odoo-bin shell -c odoo.conf -d lugal

# ثم:
env['ir.module.module'].search([('name', '=', 'uom')]).button_immediate_upgrade()
```

---

## 🚨 **الحل السريع المؤقت:**

إذا كنت تريد حلاً سريعاً لمتابعة العمل:

### **خيار A: تعطيل sale_timesheet مؤقتاً**

```bash
python odoo-bin -c odoo.conf -d lugal --uninstall sale_timesheet
```

### **خيار B: إنشاء قاعدة بيانات تجريبية**

```bash
# 1. أنشئ قاعدة بيانات جديدة للتجربة
createdb -U odoo_user lugal_test

# 2. ابدأ Odoo على القاعدة الجديدة
python odoo-bin -c odoo.conf -d lugal_test
```

---

## 📋 **الخطوات التفصيلية (الحل 2):**

### **1. أوقف Odoo:**

```powershell
# في PowerShell، اضغط Ctrl+C لإيقاف Odoo
```

### **2. حذف cache Odoo:**

```powershell
Remove-Item -Recurse -Force "$env:APPDATA\Odoo" -ErrorAction SilentlyContinue
```

### **3. إعادة تثبيت وحدة base و uom:**

```bash
python odoo-bin -c odoo.conf -d lugal -i base -u uom --stop-after-init
```

### **4. إعادة تشغيل Odoo:**

```bash
python odoo-bin -c odoo.conf
```

### **5. التحقق:**

افتح المتصفح واذهب إلى:
```
http://localhost:8069
```

---

## 🔍 **التشخيص:**

لمعرفة حالة قاعدة البيانات:

```sql
-- الاتصال بقاعدة البيانات
psql -U odoo_user -d lugal

-- التحقق من وجود جدول uom_uom
SELECT COUNT(*) FROM uom_uom;

-- التحقق من وجود وحدة Hour
SELECT * FROM uom_uom WHERE name = 'Hours';

-- التحقق من XML IDs
SELECT * FROM ir_model_data 
WHERE module = 'uom' AND name = 'product_uom_hour';
```

---

## 💡 **نصائح هامة:**

1. **دائماً خذ نسخة احتياطية قبل حذف البيانات:**
   ```bash
   pg_dump -U odoo_user lugal > backup_$(date +%Y%m%d).sql
   ```

2. **لا تحذف وحدات القياس الأساسية:**
   - Units
   - Hours
   - Days
   - kg
   - m
   - L

3. **استخدم Odoo ORM لحذف البيانات** بدلاً من SQL المباشر

---

## 📞 **إذا استمرت المشكلة:**

### **الحل النهائي: بداية جديدة**

```bash
# 1. أوقف Odoo
# 2. احذف قاعدة البيانات
dropdb lugal

# 3. أنشئ قاعدة بيانات جديدة
createdb -U odoo_user lugal

# 4. ابدأ Odoo بتثبيت الوحدات
python odoo-bin -c odoo.conf -d lugal -i base,stock,sale,purchase,point_of_sale,sap_integration --stop-after-init

# 5. ابدأ Odoo عادياً
python odoo-bin -c odoo.conf
```

---

## ✅ **الحالة المطلوبة بعد الإصلاح:**

```sql
-- يجب أن تُرجع هذه الاستعلامات نتائج:

SELECT * FROM uom_category;  -- على الأقل 5 فئات
SELECT * FROM uom_uom;        -- على الأقل 10 وحدات
SELECT * FROM ir_model_data WHERE module = 'uom';  -- XML IDs
```

---

**📅 التاريخ:** 27 أكتوبر 2025  
**⚠️ الخطورة:** حرجة  
**🎯 الحل الموصى به:** الحل 2 (إعادة تثبيت UoM) أو الحل 1 (استعادة نسخة احتياطية)


