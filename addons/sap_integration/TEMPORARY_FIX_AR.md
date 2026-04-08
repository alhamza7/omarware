# 🔧 حل مؤقت - تعطيل الواجهة المعقدة

## المشكلة

Odoo يحاول التحقق من الـ views قبل تحميل جميع الموديلات، مما يسبب:
```
Field "technical_name" does not exist in model "custom.report.template"
```

## الحل المؤقت

تم إنشاء واجهة بسيطة مؤقتة بدون التفاصيل المعقدة:
- `custom_report_template_views_simple.xml` - واجهة بسيطة (فقط Action + Menu)
- تعطيل `custom_report_template_views.xml` مؤقتاً

## الخطوات

### 1. التحديث بالواجهة البسيطة

```bash
cd /home/lugalai/Lugal-ai
./venv/bin/python3 odoo-bin -c odoo.conf -d nbs_lugalai -u sap_integration --stop-after-init
```

### 2. التحقق من الموديلات

بعد نجاح التحديث، تحقق من:
```python
# من Odoo shell
env['custom.report.template'].search([])
env['custom.report.column'].search([])
env['custom.report.total'].search([])
env['custom.report.section'].search([])
```

### 3. تفعيل الواجهة الكاملة

بعد التأكد أن الموديلات تعمل:
1. افتح `__manifest__.py`
2. احذف علامة التعليق من `custom_report_template_views.xml`
3. علق على `custom_report_template_views_simple.xml`
4. حدّث المودل مرة أخرى

## البديل

إذا استمرت المشكلة، سننشئ views منفصلة لكل موديل بدلاً من inline trees.

---

**التاريخ:** 23 ديسمبر 2025  
**الحالة:** 🔄 حل مؤقت - قيد الاختبار

