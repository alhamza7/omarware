# تنظيف بقايا SAP Integration من قاعدة البيانات المحلية

## المشكلة

بعد محاولة تثبيت `sap_integration`، بقيت بعض السجلات في قاعدة البيانات:
- قوائم (menus)
- إجراءات (actions)
- بيانات الوحدة (module metadata)

هذا يسبب خطأ 404 عند محاولة فتح قوائم SAP:
```
KeyError: 'sap.product.complete.migration'
404: Not Found
```

## الحل

تنظيف جميع السجلات المتعلقة بـ SAP من قاعدة البيانات المحلية.

## الأوامر المستخدمة

```sql
-- حذف جميع إجراءات SAP
DELETE FROM ir_act_window WHERE model LIKE 'sap%';

-- حذف جميع قوائم SAP  
DELETE FROM ir_ui_menu WHERE name LIKE '%SAP%' OR name LIKE '%sap%';

-- حذف بيانات الوحدة
DELETE FROM ir_model_data WHERE module = 'sap_integration';

-- حذف سجل الوحدة
DELETE FROM ir_module_module WHERE name = 'sap_integration';
```

## كيفية التنفيذ

### الطريقة 1: من Terminal

```bash
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai

psql lugal_local << 'EOF'
DELETE FROM ir_act_window WHERE model LIKE 'sap%';
DELETE FROM ir_ui_menu WHERE name LIKE '%SAP%' OR name LIKE '%sap%';
DELETE FROM ir_model_data WHERE module = 'sap_integration';
DELETE FROM ir_module_module WHERE name = 'sap_integration';
EOF

# إعادة تشغيل Odoo
pkill -f "odoo-bin"
./start_local.sh
```

### الطريقة 2: سكريبت جاهز

```bash
# إنشاء سكريبت التنظيف
cat > cleanup_sap.sh << 'SCRIPT'
#!/bin/bash
echo "🧹 تنظيف بقايا SAP Integration..."

psql lugal_local << 'EOF'
DELETE FROM ir_act_window WHERE model LIKE 'sap%';
DELETE FROM ir_ui_menu WHERE name LIKE '%SAP%' OR name LIKE '%sap%';
DELETE FROM ir_model_data WHERE module = 'sap_integration';
DELETE FROM ir_module_module WHERE name = 'sap_integration';
SELECT 'تم التنظيف بنجاح' as status;
EOF

echo "✅ تم التنظيف"
echo "🔄 إعادة تشغيل Odoo..."

pkill -f "odoo-bin"
sleep 2
nohup ./venv/bin/python odoo-bin -c odoo_local.conf --dev=all > /dev/null 2>&1 &

sleep 5
echo "✅ تم إعادة التشغيل"
echo "🌐 افتح: http://localhost:8070"
SCRIPT

chmod +x cleanup_sap.sh
./cleanup_sap.sh
```

## التحقق

بعد التنظيف، تحقق من:

```sql
-- يجب أن تكون النتيجة فارغة
SELECT * FROM ir_act_window WHERE model LIKE 'sap%';
SELECT * FROM ir_ui_menu WHERE name LIKE '%SAP%';
SELECT * FROM ir_module_module WHERE name = 'sap_integration';
```

## النتيجة

✅ لا مزيد من أخطاء 404
✅ القوائم نظيفة (لا قوائم SAP)
✅ النظام يعمل بدون مشاكل
✅ جاهز للتطوير على الوحدات الأخرى

## متى تحتاج هذا التنظيف؟

- ✅ بعد محاولة تثبيت فاشلة لوحدة
- ✅ عند الحصول على خطأ 404 لـ model غير موجود
- ✅ عند رؤية قوائم لوحدات غير مثبتة
- ✅ عند تنظيف قاعدة البيانات المحلية

## الوقاية

لتجنب هذه المشاكل مستقبلاً:

```bash
# عند تثبيت وحدة جديدة، تأكد من نجاح التثبيت أولاً
./venv/bin/python odoo-bin -c odoo_local.conf \
  -d lugal_local \
  --init=module_name \
  --stop-after-init

# تحقق من السجلات
tail -100 odoo_local.log | grep ERROR

# إذا فشل التثبيت، نظف فوراً قبل إعادة المحاولة
psql lugal_local -c "DELETE FROM ir_module_module WHERE name = 'module_name';"
```

## ملاحظات

- ⚠️  هذا التنظيف آمن للبيئة المحلية فقط
- ⚠️  لا تنفذ هذا على قاعدة بيانات الإنتاج
- ⚠️  تأكد من أخذ نسخة احتياطية قبل التنظيف إذا كانت لديك بيانات مهمة

## الخلاصة

بقايا الوحدات الفاشلة يمكن أن تسبب أخطاء. نظفها بانتظام للحفاظ على قاعدة بيانات نظيفة.

---

**تم التنظيف:** 2026-02-01  
**الحالة:** ✅ قاعدة البيانات نظيفة
