#!/bin/bash
# سكريبت شامل لتحديث الوحدات ومسح الكاش وإعادة التشغيل
# للاستخدام على سطح المكتب البعيد (Linux/Ubuntu)

echo "=========================================="
echo "تحديث الوحدات ومسح الكاش - سطح المكتب البعيد"
echo "=========================================="
echo ""

# الانتقال إلى مجلد المشروع
cd ~/Lugal-ai || cd /home/lugalai/Lugal-ai || {
    echo "❌ خطأ: لم يتم العثور على مجلد المشروع"
    exit 1
}

# قراءة اسم قاعدة البيانات من odoo.conf
DB_NAME=$(grep "^dbfilter" odoo.conf 2>/dev/null | sed 's/.*= *\^\([^.*]*\).*/\1/' || echo "lugal")
if [ -z "$DB_NAME" ] || [ "$DB_NAME" = "lugal.*" ]; then
    DB_NAME="lugal"
fi
echo "قاعدة البيانات: $DB_NAME"

echo "✅ تم العثور على مجلد المشروع: $(pwd)"
echo ""

# 1. إيقاف Odoo إذا كان يعمل
echo "1. إيقاف Odoo..."
pkill -f "odoo-bin.*$DB_NAME" || pkill -f "odoo-bin" || true
sleep 3
echo "   ✅ تم إيقاف Odoo"
echo ""

# 2. تحديد مسار Python
if [ -f "venv/bin/python" ]; then
    PYTHON_CMD="venv/bin/python"
    echo "✅ استخدام venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
    echo "✅ استخدام .venv/bin/python"
else
    PYTHON_CMD="python3"
    echo "⚠️  استخدام python3 النظام"
fi
echo ""

# 3. مسح الكاش من النظام
echo "2. مسح الكاش من النظام..."
rm -rf ~/.local/share/Odoo/filestore/$DB_NAME/* 2>/dev/null || true
rm -rf /tmp/odoo_* 2>/dev/null || true
rm -rf /tmp/odoo 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "   ✅ تم مسح الكاش من النظام"
echo ""

# 4. تحديث الوحدات
echo "3. تحديث الوحدات (pos_perfume_custom و sap_integration)..."
$PYTHON_CMD odoo-bin -c odoo.conf -d "$DB_NAME" \
    -u pos_perfume_custom,sap_integration \
    --stop-after-init \
    --log-level=warn 2>&1 | tail -20
echo "   ✅ تم تحديث الوحدات"
echo ""

# 5. مسح الكاش من قاعدة البيانات
echo "4. مسح الكاش من قاعدة البيانات..."
$PYTHON_CMD odoo-bin shell -c odoo.conf -d "$DB_NAME" << 'PYTHON_SCRIPT'
import odoo
from odoo.orm.registry import Registry
odoo.tools.config.parse_config(['--config=odoo.conf'])
db_name = odoo.tools.config.get('db_name') or '$DB_NAME'
registry = Registry(db_name)
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    
    # مسح الكاش من ir_ui_view
    try:
        env['ir.ui.view'].invalidate_model()
        print("   ✅ تم مسح ir.ui.view cache")
    except:
        pass
    
    # مسح الكاش من ir_qweb
    try:
        env['ir.qweb'].invalidate_model()
        print("   ✅ تم مسح ir.qweb cache")
    except:
        pass
    
    # مسح الكاش من ir_http
    try:
        env['ir.http'].invalidate_model()
        print("   ✅ تم مسح ir.http cache")
    except:
        pass
    
    # مسح الكاش من ir_actions
    try:
        env['ir.actions.actions'].invalidate_model()
        print("   ✅ تم مسح ir.actions cache")
    except:
        pass
    
    # حذف assets القديمة
    try:
        assets = env['ir.attachment'].search([
            '|',
            ('name', 'like', 'web.assets_%'),
            ('url', 'like', '/web/assets/%')
        ])
        if assets:
            assets.unlink()
            print(f"   ✅ تم حذف {len(assets)} ملف assets")
    except:
        pass
    
    # مسح registry cache
    try:
        registry.clear_cache()
        print("   ✅ تم مسح registry cache")
    except:
        pass
    
    cr.commit()
    print("   ✅ تم مسح الكاش من قاعدة البيانات")
PYTHON_SCRIPT
echo ""

# 6. إعادة تشغيل Odoo
echo "5. إعادة تشغيل Odoo..."
echo "   استخدم الأمر التالي لتشغيل Odoo:"
echo ""
echo "   $PYTHON_CMD odoo-bin -c odoo.conf -d $DB_NAME --http-port=8069"
echo ""
echo "   أو في الخلفية:"
echo "   nohup $PYTHON_CMD odoo-bin -c odoo.conf -d $DB_NAME --http-port=8069 > odoo.log 2>&1 &"
echo ""

echo "=========================================="
echo "✅ تم الانتهاء!"
echo "=========================================="
echo ""
echo "الخطوات التالية:"
echo "1. أعد تشغيل Odoo"
echo "2. امسح كاش المتصفح (Ctrl+Shift+Delete)"
echo "3. أعد تحميل الصفحة (Ctrl+F5 أو Ctrl+Shift+R)"
echo "4. جرّب إنشاء quotation جديدة"
echo ""

