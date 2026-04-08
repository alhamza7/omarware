# 🚀 دليل التثبيت السريع - SAP Integration Module

## ✅ الحالة الحالية

**Module Status:** ✅ جاهز للتثبيت  
**Review Status:** ✅ تم الفحص والمراجعة  
**Errors:** ❌ لا توجد أخطاء  

---

## 📋 المتطلبات

### Python Packages (موجودة في venv):
- ✅ requests
- ✅ odoo dependencies

### Odoo Modules:
- ✅ connector (موجود)
- ✅ component (موجود)
- ✅ component_event (موجود)
- ⚠️ queue_job (اختياري - موصى به)

---

## 🔧 خطوات التثبيت

### 1. تفعيل البيئة الافتراضية
```powershell
cd L:\odoo
.\venv\Scripts\Activate.ps1
```

### 2. (اختياري) تثبيت queue_job
```bash
pip install odoo-addon-queue-job==17.0.*
```

### 3. ترقية/تثبيت المودل
```bash
# للترقية (إذا كان مثبت مسبقاً)
python odoo-bin -c odoo.conf -d lugal -u sap_integration

# للتثبيت الجديد
python odoo-bin -c odoo.conf -d lugal -i sap_integration
```

### 4. تشغيل النظام
```bash
python odoo-bin -c odoo.conf -d lugal
```

### 5. الوصول للنظام
```
URL: http://localhost:8069
Database: lugal
```

---

## 🎯 الخطوات بعد التثبيت

### 1. إعداد المجموعات الأمنية
```
Settings > Users & Companies > Users
```
- اختر المستخدم
- أضفه لمجموعة **SAP User** أو **SAP Manager**

### 2. إعداد Backend
```
SAP Integration > SAP Backends > Create
```
```
Name: SAP Production
Service Layer URL: https://your-sap:50000/b1s/v1
Username: your_username
Password: your_password
Company DB: YOUR_DB
```
اضغط **Test Connection**

### 3. فتح Dashboard
```
SAP Integration > 📊 Dashboard
```

### 4. استيراد بيانات
```
SAP Integration > Bulk Import
```
اختر:
- Backend
- Data Type (Partners/Products/Orders)
- Import Mode

---

## ✨ الميزات المتاحة

### 1. Dashboard
```
SAP Integration > 📊 Dashboard
```
- عرض الإحصائيات
- تتبع الأخطاء
- مراقبة الأداء

### 2. Bulk Import Wizard
```
SAP Integration > Bulk Import
```
- استيراد جماعي
- فلترة متقدمة
- تتبع التقدم

### 3. Auto Sync
```
Backend > Auto Sync / Export
```
- تفعيل Auto Export Partners
- تفعيل Auto Export Products
- تفعيل Auto Export Orders

### 4. Incremental Sync
```
Backend > Incremental Sync
```
- تفعيل Incremental Sync
- ضبط Sync Days
- عرض Last Sync Dates

---

## 🧪 الاختبار

### Test 1: Dashboard
```python
# من Odoo Shell
dashboard = env['sap.dashboard'].create({})
print(f"Backends: {dashboard.total_backends}")
print(f"Partners: {dashboard.total_partners}")
```

### Test 2: Backend Connection
```python
backend = env['sap.backend'].browse(1)
backend.test_connection()
```

### Test 3: Import Partners
```python
backend = env['sap.backend'].browse(1)
result = env['sap.res.partner'].import_batch(backend)
print(f"Imported: {result.get('imported', 0)}")
```

### Test 4: Auto Export
```python
# تفعيل auto-export
backend.write({'auto_export_partners': True})

# إنشاء partner جديد
partner = env['res.partner'].create({
    'name': 'Test Customer',
    'email': 'test@example.com'
})

# تحقق من إنشاء binding
binding = env['sap.res.partner'].search([
    ('odoo_id', '=', partner.id)
])
print(f"Binding created: {bool(binding)}")
```

---

## 📊 التحقق من التثبيت

### 1. تحقق من Models
```python
# Models المتوفرة
env['sap.backend'].search([])
env['sap.res.partner'].search([])
env['sap.product.product'].search([])
env['sap.dashboard'].create({})
env['sap.import.wizard'].create({})
```

### 2. تحقق من Views
- Dashboard يفتح بدون أخطاء
- Backend form يظهر جميع الحقول
- Wizard يفتح ويعمل

### 3. تحقق من Security
```python
# Groups
env['res.groups'].search([('name', 'like', 'SAP')])

# Access Rights
env['ir.model.access'].search([('name', 'like', 'sap')])
```

---

## ⚠️ استكشاف الأخطاء

### خطأ: Module not found
```bash
# تأكد من المسار
ls L:\odoo\addons\sap_integration

# تأكد من __manifest__.py موجود
cat L:\odoo\addons\sap_integration\__manifest__.py
```

### خطأ: Import Error
```python
# تحقق من dependencies
# connector, component, component_event
# يجب أن تكون مثبتة
```

### خطأ: Connection Failed
```python
# تحقق من:
1. SAP Service Layer URL صحيح
2. Username/Password صحيح
3. Company DB صحيح
4. SAP server accessible
5. Firewall لا يمنع الاتصال
```

### خطأ: Permission Denied
```python
# تأكد من:
1. المستخدم في group_sap_user أو group_sap_manager
2. Access rights configured correctly
```

---

## 📝 Notes

### Performance Tips:
1. ✅ فعّل Incremental Sync لتقليل الحمل
2. ✅ اضبط Batch Size حسب حجم البيانات
3. ✅ ثبّت queue_job للمعالجة في الخلفية
4. ✅ استخدم Filters في Bulk Import

### Security Tips:
1. ✅ لا تعطي group_sap_manager لجميع المستخدمين
2. ✅ راجع Access Rights بانتظام
3. ✅ فعّل logging للمراقبة

### Maintenance:
1. ✅ راجع Dashboard بانتظام
2. ✅ راقب Error statistics
3. ✅ نظف Old bindings إذا لزم الأمر
4. ✅ Backup قبل upgrades

---

## 🎉 النتيجة

إذا اتبعت الخطوات أعلاه:
- ✅ Module مثبت
- ✅ Backend configured
- ✅ Dashboard يعمل
- ✅ Import/Export جاهز
- ✅ Security configured

**مبروك! 🎊 Module جاهز للاستخدام**

---

## 📞 الدعم

لأي مشاكل:
1. راجع logs: `odoo.log`
2. راجع `REVIEW_REPORT.md`
3. راجع `IMPROVEMENTS_LOG.md`
4. راجع `README.md`

---

**آخر تحديث:** 16 أكتوبر 2024  
**الإصدار:** v2.1.0

