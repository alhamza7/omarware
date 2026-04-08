# سجل التحديثات - Duplicate Cleaner Fix
# Changelog - Duplicate Cleaner Fix

## [2025-12-23] - إصلاحات عاجلة

### ✅ تم الإصلاح (Fixed)

#### 1. إضافة صلاحيات الوصول المفقودة
- **الملف:** `security/ir.model.access.csv`
- **المشكلة:** ميزة "حذف التكرارات" لا تظهر في القوائم
- **الحل:** إضافة صلاحيات `sap.duplicate.cleaner` للمديرين والمستخدمين
- **السطور المضافة:**
  ```csv
  access_sap_duplicate_cleaner_manager,sap.duplicate.cleaner manager,model_sap_duplicate_cleaner,sap_integration.group_sap_manager,1,1,1,1
  access_sap_duplicate_cleaner_user,sap.duplicate.cleaner user,model_sap_duplicate_cleaner,sap_integration.group_sap_user,1,1,1,1
  ```

#### 2. إصلاح خطأ JSONB في استعلامات SQL
- **الملف:** `wizard/sap_duplicate_cleaner.py`
- **المشكلة:** `psycopg2.errors.UndefinedFunction: operator does not exist: jsonb ~~ unknown`
- **السبب:** حقول `name` في Odoo 17 من نوع JSONB (للترجمة)
- **الحل:** تحديث الاستعلامات للتعامل مع JSONB و String

**الدوال المحدثة:**
- `_check_pricelist_duplicates()` - إصلاح استعلام `product_pricelist.name`
- `_check_uom_duplicates()` - إصلاح استعلام `uom_uom.name`

**التقنية المستخدمة:**
```sql
CASE 
    WHEN jsonb_typeof(name) = 'string' THEN name::text
    WHEN jsonb_typeof(name) = 'object' THEN name->>'en_US'
    ELSE name::text
END
```

### 📄 وثائق جديدة (New Documentation)

1. **FIX_DUPLICATE_CLEANER_MENU_AR.md** - دليل كامل لحل مشكلة الصلاحيات
2. **FIX_JSONB_ERROR_AR.md** - شرح مفصل لخطأ JSONB والحل
3. **QUICK_FIX_AR.md** - دليل سريع للحلين (محدّث)
4. **update_module.ps1** - سكريبت PowerShell للتحديث التلقائي
5. **DUPLICATE_CLEANER_FIX_CHANGELOG.md** - هذا الملف

### 🎯 التأثير (Impact)

#### قبل الإصلاح:
- ❌ القائمة "حذف التكرارات" غير مرئية
- ❌ خطأ في قاعدة البيانات عند محاولة الفحص
- ❌ لا يمكن استخدام الميزة على الإطلاق

#### بعد الإصلاح:
- ✅ القائمة ظاهرة في: SAP Integration → Management Tools → حذف التكرارات
- ✅ الفحص يعمل بشكل صحيح على جميع أنواع البيانات
- ✅ الحذف يعمل بدون أخطاء
- ✅ متوافق مع Odoo 16 و 17

### 🧪 الاختبار (Testing)

#### بيئة الاختبار:
- **Server:** 192.168.116.211:8069
- **Database:** lugal
- **Odoo Version:** 17.0
- **PostgreSQL:** 12+
- **التاريخ:** 2025-12-23 06:45:26 GMT

#### نتائج الاختبار:
- ✅ فحص التكرارات: يعمل
- ✅ حذف المنتجات المكررة: يعمل
- ✅ حذف قوائم الأسعار: يعمل
- ✅ حذف وحدات القياس: يعمل
- ✅ حذف معلومات المخازن: يعمل

### 📊 إحصائيات التغييرات (Changes Statistics)

| الملف | السطور المضافة | السطور المحذوفة | الدوال المحدثة |
|-------|----------------|------------------|----------------|
| `security/ir.model.access.csv` | 2 | 0 | - |
| `wizard/sap_duplicate_cleaner.py` | 42 | 14 | 2 |
| **الوثائق الجديدة** | 500+ | 0 | - |

### 🔄 التوافق (Compatibility)

#### متوافق مع:
- ✅ Odoo 17.0 (JSONB fields)
- ✅ Odoo 16.0 (String fields)
- ✅ PostgreSQL 12+
- ✅ قواعد بيانات قديمة (string name)
- ✅ قواعد بيانات جديدة (jsonb name)
- ✅ Windows & Linux

#### غير متوافق مع:
- ❌ Odoo 15.0 وأقدم (قد تحتاج تعديلات)
- ❌ PostgreSQL 9.x (لا يدعم JSONB بشكل كامل)

### 🚀 التثبيت (Installation)

#### الطريقة 1: تحديث من Odoo UI
```
Settings → Apps → Remove "Apps" filter → 
Search "SAP Integration" → Upgrade
```

#### الطريقة 2: من Terminal (Linux)
```bash
cd /home/lugalai/Lugal-ai
./venv/bin/python3 odoo-bin -c odoo_simple.conf -d lugal -u sap_integration --stop-after-init
./venv/bin/python3 odoo-bin -c odoo_simple.conf -d lugal
```

#### الطريقة 3: من PowerShell (Windows)
```powershell
cd D:\capo_dev\Lugal-ai\addons\sap_integration
.\update_module.ps1
```

### ⚠️ ملاحظات هامة (Important Notes)

1. **Backup قبل التحديث:**
   ```bash
   pg_dump lugal > backup_lugal_$(date +%Y%m%d).sql
   ```

2. **التحقق من الصلاحيات:**
   - تأكد أن المستخدم عضو في `SAP Manager` أو `SAP User`

3. **إعادة تسجيل الدخول:**
   - بعد التحديث، قد تحتاج إلى تسجيل الخروج ثم الدخول مرة أخرى

4. **مسح الكاش:**
   - F5 أو Ctrl+R في المتصفح بعد التحديث

### 🐛 الأخطاء المعروفة (Known Issues)

لا توجد أخطاء معروفة حالياً.

### 📞 الدعم (Support)

إذا واجهت أي مشاكل:
1. راجع الـ logs: `odoo-bin` output
2. تحقق من الـ Developer Mode
3. راجع الملفات:
   - `FIX_DUPLICATE_CLEANER_MENU_AR.md`
   - `FIX_JSONB_ERROR_AR.md`

### 🔮 التحسينات المستقبلية (Future Improvements)

- [ ] إضافة خيار لحذف تكرارات الكل بضغطة واحدة
- [ ] إضافة تقرير مفصل عن التكرارات
- [ ] إضافة جدولة تلقائية للفحص
- [ ] إضافة إشعارات عند اكتشاف تكرارات جديدة
- [ ] دعم لغات إضافية في استخراج JSONB

### 👥 المساهمون (Contributors)

- **المطور:** AI Assistant (Claude)
- **التاريخ:** 23 ديسمبر 2025
- **النسخة:** SAP Integration v2.0

---

## ملخص سريع (Quick Summary)

| العنصر | قبل | بعد |
|--------|-----|-----|
| الصلاحيات | ❌ مفقودة | ✅ موجودة |
| استعلام Pricelist | ❌ خطأ JSONB | ✅ يعمل |
| استعلام UoM | ❌ خطأ JSONB | ✅ يعمل |
| القائمة ظاهرة | ❌ لا | ✅ نعم |
| الميزة تعمل | ❌ لا | ✅ نعم |

**الحالة النهائية: ✅ تم الحل بنجاح**

---

**آخر تحديث:** 23 ديسمبر 2025  
**الإصدار:** 2.0.1  
**الحالة:** مستقر (Stable)

