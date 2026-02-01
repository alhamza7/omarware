# حل مشكلة SAP Integration - Connector Dependency

## المشكلة

```
TypeError: Model 'sap.backend' inherits from non-existing model 'connector.backend'.
```

الوحدة `sap_integration` تحاول استخدام OCA Connector framework، لكن:
- OCA Connector غير متوافق مع Odoo 19 (كما ذُكر في __manifest__.py)
- الوحدة معطلة لكن الكود لا يزال يحاول استخدام connector

## الحلول المتاحة

### الحل 1: إزالة الاعتماد على Connector (موصى به)

تعديل الملفات لإزالة الوراثة من `connector.backend`:

**الملفات المطلوب تعديلها:**
1. `addons/sap_integration/models/sap_backend.py`
2. `addons/sap_integration/models/sap_uom.py`  
3. `addons/sap_integration/models/sap_pricelist.py`

**التعديلات:**
- إزالة: `_inherit = 'connector.backend'`
- استبدال بـ: `models.Model` عادي
- إضافة الحقول المطلوبة من connector يدوياً إذا لزم

### الحل 2: تثبيت OCA Connector (صعب)

تثبيت المكتبات:
```bash
pip install odoo-connector odoo-addon-component odoo-addon-queue_job
```

**لكن:**
- ❌ غير متوافق مع Odoo 19
- ❌ قد يسبب مشاكل أخرى
- ❌ غير موصى به

### الحل 3: استخدام نسخة مبسطة (أفضل حل مؤقت)

إنشاء model بسيط يستبدل connector.backend محلياً.

## التنفيذ الموصى به

سأنفذ الحل 3: إنشاء connector.backend مبسط محلياً.
