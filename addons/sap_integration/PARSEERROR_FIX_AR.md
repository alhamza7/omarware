# 🔧 إصلاح ParseError في Views - Custom Report Designer

## ❌ المشكلة

```
ParseError: Field "technical_name" does not exist in model "custom.report.template"
File: custom_report_template_views.xml, line 125
```

## 🔍 السبب

عند استخدام `One2many` في Odoo مع `tree editable`, يجب إضافة حقل `template_id` (أو المرجع الأساسي) كحقل مخفي في الـ tree view، وإلا لن يستطيع Odoo ربط السجلات بشكل صحيح.

## ✅ الإصلاح

تم إضافة `<field name="template_id" invisible="1"/>` في جميع tree views للموديلات الفرعية:

### 1. في `table_columns` (أعمدة الجدول)
```xml
<field name="table_columns">
    <tree editable="bottom">
        <field name="template_id" invisible="1"/>  ✅ تمت الإضافة
        <field name="sequence" widget="handle"/>
        <field name="name"/>
        <field name="technical_name"/>
        ...
    </tree>
</field>
```

### 2. في `totals_fields` (حقول المجاميع)
```xml
<field name="totals_fields">
    <tree editable="bottom">
        <field name="template_id" invisible="1"/>  ✅ تمت الإضافة
        <field name="sequence" widget="handle"/>
        ...
    </tree>
</field>
```

### 3. في `sections` (الأقسام الإضافية)
```xml
<field name="sections">
    <tree>
        <field name="template_id" invisible="1"/>  ✅ تمت الإضافة
        <field name="sequence" widget="handle"/>
        ...
    </tree>
    <form>
        <group>
            <group>
                <field name="template_id" invisible="1"/>  ✅ تمت الإضافة
                ...
            </group>
        </group>
    </form>
</field>
```

## 📚 معلومة مهمة

**قاعدة Odoo:**
- عند استخدام `One2many` في form view مع inline tree
- يجب **دائماً** إضافة الحقل المرجعي (مثل `template_id`) كحقل مخفي
- هذا يساعد Odoo في تتبع العلاقة وحفظ البيانات بشكل صحيح

## 🚀 التحديث (على السيرفر)

الآن يجب تحديث المودل من جديد:

```bash
cd /home/lugalai/Lugal-ai
./venv/bin/python3 odoo-bin -c odoo.conf -d nbs_lugalai -u sap_integration --stop-after-init
./venv/bin/python3 odoo-bin -c odoo.conf -d nbs_lugalai
```

أو من واجهة Odoo:
1. اذهب إلى **Apps**
2. ابحث عن **SAP Integration**
3. اضغط **Upgrade**

## ✅ النتيجة المتوقعة

بعد التحديث، ستعمل الواجهات بشكل صحيح وستتمكن من:
- ✅ إضافة أعمدة للجدول
- ✅ إضافة حقول للمجاميع
- ✅ إضافة أقسام إضافية
- ✅ حفظ جميع التغييرات بدون أخطاء

---

**التاريخ:** 23 ديسمبر 2025  
**الحالة:** ✅ تم الإصلاح

