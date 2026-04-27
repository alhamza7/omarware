# حل مشكلة عدم ظهور "حذف التكرارات" في القوائم

## 📋 المشكلة
تم إضافة ميزة حذف المنتجات المتكررة (`sap.duplicate.cleaner`) ولكنها لا تظهر في قائمة SAP Integration.

## 🔍 السبب
كانت **صلاحيات الوصول مفقودة** في ملف `security/ir.model.access.csv`، مما منع Odoo من إظهار القائمة للمستخدمين.

## ✅ الحل المطبق

### 1. إضافة الصلاحيات المفقودة
تم إضافة السطور التالية إلى `addons/sap_integration/security/ir.model.access.csv`:

```csv
access_sap_duplicate_cleaner_manager,sap.duplicate.cleaner manager,model_sap_duplicate_cleaner,sap_integration.group_sap_manager,1,1,1,1
access_sap_duplicate_cleaner_user,sap.duplicate.cleaner user,model_sap_duplicate_cleaner,sap_integration.group_sap_user,1,1,1,1
```

### 2. التحقق من الملفات الموجودة
- ✅ `wizard/sap_duplicate_cleaner.py` - موجود وصحيح
- ✅ `wizard/sap_duplicate_cleaner_views.xml` - موجود وصحيح
- ✅ `wizard/__init__.py` - يحتوي على `from . import sap_duplicate_cleaner`
- ✅ `__manifest__.py` - يحتوي على `'wizard/sap_duplicate_cleaner_views.xml'`
- ✅ `views/sap_menus_minimal.xml` - يحتوي على `menu_sap_tools`
- ⚠️ `security/ir.model.access.csv` - كان ناقصاً (تم إصلاحه الآن)

## 🚀 خطوات تفعيل الميزة

### الطريقة 1: تحديث المودل من واجهة Odoo (الأسهل)

1. **افتح Odoo في المتصفح**
   ```
   http://localhost:8070
   ```

2. **فعّل وضع المطور (Developer Mode)**
   - اذهب إلى: Settings → General Settings
   - في الأسفل: Activate the developer mode
   - أو مباشرة من URL:
     ```
     http://localhost:8070/web?debug=1
     ```

3. **اذهب إلى قائمة التطبيقات**
   ```
   Apps → Remove "Apps" filter → Search for "SAP Integration"
   ```

4. **حدّث المودل**
   - اضغط على زر **Upgrade** (تحديث) بجانب SAP Integration
   - انتظر حتى ينتهي التحديث

5. **أعد تحميل الصفحة**
   - اضغط F5 أو Ctrl+R

6. **تحقق من القائمة**
   - اذهب إلى: **SAP Integration → 🛠️ Management Tools → حذف التكرارات**

---

### الطريقة 2: تحديث المودل من Terminal (للمطورين)

#### أ) إذا كان Odoo يعمل حالياً:
```powershell
# 1. أوقف Odoo (Ctrl+C في Terminal حيث يعمل)

# 2. شغّل Odoo مع تحديث المودل
cd D:\capo_dev\Lugal-ai
.\venv\Scripts\python.exe odoo-bin -c odoo_simple.conf -d lugal -u sap_integration

# 3. بعد انتهاء التحديث، شغّل Odoo عادياً
.\venv\Scripts\python.exe odoo-bin -c odoo_simple.conf -d lugal
```

#### ب) إذا لم يكن Odoo يعمل:
```powershell
# تحديث مباشر
cd D:\capo_dev\Lugal-ai
.\venv\Scripts\python.exe odoo-bin -c odoo_simple.conf -d lugal -u sap_integration --stop-after-init

# ثم شغّل Odoo
.\venv\Scripts\python.exe odoo-bin -c odoo_simple.conf -d lugal
```

---

## 📍 مكان القائمة الجديدة

بعد التحديث، ستجد الميزة في:

```
SAP Integration
  └── 🛠️ Management Tools (أدوات الإدارة)
       ├── Sync Management
       ├── UoM Management
       ├── ...
       └── حذف التكرارات  ← هنا! (Sequence: 100)
```

---

## 🎯 استخدام الميزة

### 1. فتح الأداة
```
SAP Integration → Management Tools → حذف التكرارات
```

### 2. خيارات الحذف المتاحة
- ✅ **حذف تكرار المنتجات** - بناءً على `default_code`
- ✅ **حذف تكرار قوائم الأسعار** - بناءً على `name + currency_id`
- ✅ **حذف تكرار بنود قوائم الأسعار** - من `sap.product.pricelist.sync`
- ✅ **حذف تكرار وحدات القياس** - بناءً على `name`
- ✅ **حذف تكرار معلومات المخازن** - من `sap.product.warehouse.info`

### 3. خطوات الاستخدام
```
1. افتح النافذة (Wizard)
2. اختر الخيارات التي تريدها (افتراضياً كلها مفعّلة)
3. اضغط "فحص التكرارات" لمعاينة التكرارات قبل الحذف
4. اضغط "حذف التكرارات" لتنفيذ الحذف
5. راجع النتائج في "سجل النتائج"
```

### 4. ملاحظات هامة
⚠️ **احذر:**
- الحذف **لا يمكن التراجع عنه**
- يتم الاحتفاظ بأحدث سجل (أعلى ID) وحذف الباقي
- يُفضل عمل **Backup** للقاعدة قبل الحذف

---

## 🧪 اختبار الميزة

### 1. فحص التكرارات فقط
```python
# في Odoo Shell أو من الواجهة
wizard = env['sap.duplicate.cleaner'].create({})
wizard.action_check_duplicates()
# راجع wizard.result_log
```

### 2. حذف تكرار المنتجات فقط
```python
wizard = env['sap.duplicate.cleaner'].create({
    'clean_products': True,
    'clean_pricelists': False,
    'clean_pricelist_items': False,
    'clean_uom': False,
    'clean_warehouse_info': False,
})
wizard.action_clean_duplicates()
```

---

## 🔧 استكشاف الأخطاء

### المشكلة: لا تزال القائمة غير ظاهرة بعد التحديث

#### الحل 1: تحقق من صلاحيات المستخدم
```python
# في Odoo Shell
user = env.user
print(user.groups_id.mapped('name'))
# يجب أن تحتوي على: 'SAP Manager' أو 'SAP User'
```

#### الحل 2: تحقق من تحميل الملفات
```python
# في Odoo Shell
menu = env['ir.ui.menu'].search([('name', '=', 'حذف التكرارات')])
print(f"Menu found: {menu}")
print(f"Menu ID: {menu.id}")
print(f"Action: {menu.action}")
```

#### الحل 3: تحقق من الصلاحيات
```python
# في Odoo Shell
access = env['ir.model.access'].search([
    ('model_id.model', '=', 'sap.duplicate.cleaner')
])
print(f"Access rules found: {len(access)}")
for a in access:
    print(f"  - {a.name}: read={a.perm_read}, write={a.perm_write}, create={a.perm_create}, unlink={a.perm_unlink}")
```

### المشكلة: خطأ "Access Denied" عند فتح القائمة

#### الحل: إضافة المستخدم إلى المجموعة الصحيحة
```python
# في Odoo Shell
user = env.user
group = env.ref('sap_integration.group_sap_manager')
user.write({'groups_id': [(4, group.id)]})
```

---

## 📊 الملفات المُحدَّثة

| الملف | التغيير |
|-------|----------|
| `security/ir.model.access.csv` | ✅ إضافة صلاحيات `sap.duplicate.cleaner` |
| `wizard/sap_duplicate_cleaner.py` | ✅ موجود مسبقاً |
| `wizard/sap_duplicate_cleaner_views.xml` | ✅ موجود مسبقاً |
| `wizard/__init__.py` | ✅ يحتوي على الـ import |
| `__manifest__.py` | ✅ يحتوي على ملف الـ views |

---

## ✨ الخلاصة

تم حل المشكلة بإضافة الصلاحيات المفقودة. الآن فقط:

1. **حدّث المودل** من Apps → SAP Integration → Upgrade
2. **أعد تحميل الصفحة** (F5)
3. **افتح القائمة**: SAP Integration → Management Tools → حذف التكرارات

---

## 📞 المساعدة

إذا واجهت أي مشاكل:
1. تحقق من الـ logs: `odoo-bin` output أو `addons/sap_integration/logs/`
2. فعّل Developer Mode وتحقق من القوائم
3. راجع ملف `security/ir.model.access.csv` للتأكد من الصلاحيات

---

**تاريخ التحديث:** 23 ديسمبر 2025
**الإصدار:** SAP Integration v2.0

