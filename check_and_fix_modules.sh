#!/bin/bash
# سكريبت شامل للتحقق من الوحدات وإصلاح المشاكل
# للاستخدام على سطح المكتب البعيد

echo "=========================================="
echo "فحص وإصلاح الوحدات - سطح المكتب البعيد"
echo "=========================================="
echo ""

cd ~/Lugal-ai || cd /home/lugalai/Lugal-ai || {
    echo "❌ خطأ: لم يتم العثور على مجلد المشروع"
    exit 1
}

# تحديد Python
if [ -f "venv/bin/python" ]; then
    PYTHON_CMD="venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python3"
fi

echo "✅ استخدام: $PYTHON_CMD"
echo ""

# 1. التحقق من وجود الكود الجديد
echo "1. التحقق من وجود الكود الجديد..."
if grep -q "sync_successful = False" addons/pos_perfume_custom/models/pos_perfume_order.py 2>/dev/null; then
    echo "   ✅ الكود الجديد موجود في pos_perfume_order.py"
else
    echo "   ❌ الكود الجديد غير موجود! يرجى التأكد من تحديث الملفات من GitHub"
    exit 1
fi

if grep -q "❌ Error sending quotation" addons/sap_integration/models/sale_order_sap.py 2>/dev/null; then
    echo "   ✅ الكود الجديد موجود في sale_order_sap.py"
else
    echo "   ❌ الكود الجديد غير موجود في sale_order_sap.py!"
    exit 1
fi
echo ""

# 2. إيقاف Odoo
echo "2. إيقاف Odoo..."
pkill -f "odoo-bin.*lugal" || pkill -f odoo-bin || true
sleep 3
echo "   ✅ تم إيقاف Odoo"
echo ""

# 3. مسح الكاش
echo "3. مسح الكاش..."
rm -rf ~/.local/share/Odoo/filestore/lugal/* 2>/dev/null || true
rm -rf /tmp/odoo_* 2>/dev/null || true
rm -rf /tmp/odoo 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "   ✅ تم مسح الكاش"
echo ""

# 4. تحديث الوحدات
echo "4. تحديث الوحدات..."
echo "   جاري تحديث pos_perfume_custom و sap_integration..."
$PYTHON_CMD odoo-bin -c odoo.conf -d lugal \
    -u pos_perfume_custom,sap_integration \
    --stop-after-init \
    --log-level=warn 2>&1 | tail -30
echo "   ✅ تم تحديث الوحدات"
echo ""

# 5. مسح الكاش من قاعدة البيانات
echo "5. مسح الكاش من قاعدة البيانات..."
$PYTHON_CMD clear_cache_from_db.py 2>&1 | tail -20
echo ""

# 6. التحقق من تحديث الوحدات
echo "6. التحقق من حالة الوحدات..."
$PYTHON_CMD odoo-bin shell -c odoo.conf -d lugal << 'PYTHON_SCRIPT'
import odoo
odoo.tools.config.parse_config(['--config=odoo.conf'])
registry = odoo.registry(odoo.tools.config['db_name'])
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    
    modules = ['pos_perfume_custom', 'sap_integration']
    for module_name in modules:
        module = env['ir.module.module'].search([('name', '=', module_name)], limit=1)
        if module:
            print(f"   {module_name:25} : {module.state:15} (v{module.installed_version or 'N/A'})")
        else:
            print(f"   {module_name:25} : ❌ NOT FOUND")
PYTHON_SCRIPT
echo ""

# 7. إعادة تشغيل Odoo
echo "7. إعادة تشغيل Odoo..."
echo "   استخدم الأمر التالي:"
echo ""
echo "   nohup $PYTHON_CMD odoo-bin -c odoo.conf -d lugal --http-port=8069 > odoo.log 2>&1 &"
echo ""

echo "=========================================="
echo "✅ تم الانتهاء!"
echo "=========================================="
echo ""
echo "الخطوات التالية:"
echo "1. أعد تشغيل Odoo باستخدام الأمر أعلاه"
echo "2. امسح كاش المتصفح (Ctrl+Shift+Delete)"
echo "3. أعد تحميل الصفحة (Ctrl+F5)"
echo "4. جرّب إنشاء quotation جديدة"
echo "5. راقب السجل: tail -f odoo.log | grep -E 'POS|SAP|action_confirm'"
echo ""

