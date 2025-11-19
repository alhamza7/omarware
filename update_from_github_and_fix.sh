#!/bin/bash
# سكريبت شامل لتحديث الملفات من GitHub ثم تحديث الوحدات
# للاستخدام على سطح المكتب البعيد

echo "=========================================="
echo "تحديث من GitHub وإصلاح الوحدات"
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

# 1. التحقق من Git
echo "1. التحقق من Git..."
if ! command -v git &> /dev/null; then
    echo "   ❌ Git غير مثبت!"
    exit 1
fi

# التحقق من أننا في repository
if [ ! -d ".git" ]; then
    echo "   ❌ هذا ليس Git repository!"
    echo "   💡 إذا كنت تستخدم طريقة أخرى للتحديث، تأكد من تحديث الملفات يدوياً"
    exit 1
fi

echo "   ✅ Git متوفر"
echo ""

# 2. عرض حالة Git
echo "2. حالة Git الحالية..."
git status --short | head -10
echo ""

# 3. جلب التحديثات من GitHub
echo "3. جلب التحديثات من GitHub..."
git fetch origin
if [ $? -ne 0 ]; then
    echo "   ⚠️  فشل جلب التحديثات. تأكد من الاتصال بالإنترنت"
    exit 1
fi
echo "   ✅ تم جلب التحديثات"
echo ""

# 4. عرض التغييرات
echo "4. التغييرات المتاحة..."
git log HEAD..origin/main --oneline 2>/dev/null || git log HEAD..origin/master --oneline 2>/dev/null || echo "   لا توجد تغييرات جديدة"
echo ""

# 5. دمج التحديثات
echo "5. دمج التحديثات..."
BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
echo "   الفرع الحالي: $BRANCH"

# محاولة merge
if git merge origin/$BRANCH --no-edit 2>&1 | tee /tmp/git_merge.log; then
    echo "   ✅ تم دمج التحديثات بنجاح"
else
    echo "   ⚠️  قد تكون هناك تعارضات. تحقق من /tmp/git_merge.log"
    echo "   💡 إذا كان هناك تعارضات، قم بحلها يدوياً ثم أعد تشغيل السكريبت"
    exit 1
fi
echo ""

# 6. التحقق من وجود الكود الجديد
echo "6. التحقق من وجود الكود الجديد..."
CODE_FOUND=0

# التحقق من pos_perfume_order.py
if grep -q "Manual SAP sync" addons/pos_perfume_custom/models/pos_perfume_order.py 2>/dev/null; then
    echo "   ✅ الكود الجديد موجود في pos_perfume_order.py (Manual SAP sync)"
    CODE_FOUND=$((CODE_FOUND + 1))
else
    echo "   ⚠️  الكود الجديد غير موجود في pos_perfume_order.py"
fi

# التحقق من sale_order_sap.py
if grep -q "❌ Error sending quotation" addons/sap_integration/models/sale_order_sap.py 2>/dev/null; then
    echo "   ✅ الكود الجديد موجود في sale_order_sap.py (رسائل خطأ محسّنة)"
    CODE_FOUND=$((CODE_FOUND + 1))
else
    echo "   ⚠️  الكود الجديد غير موجود في sale_order_sap.py"
fi

# التحقق من pos_perfume_screen.js
if grep -q "catch (rpcError)" addons/pos_perfume_custom/static/src/app/pos_perfume_screen.js 2>/dev/null; then
    echo "   ✅ الكود الجديد موجود في pos_perfume_screen.js (معالجة RPC errors)"
    CODE_FOUND=$((CODE_FOUND + 1))
else
    echo "   ⚠️  الكود الجديد غير موجود في pos_perfume_screen.js"
fi

echo ""
if [ $CODE_FOUND -lt 2 ]; then
    echo "   ⚠️  تحذير: بعض الملفات قد لا تكون محدثة"
    echo "   💡 إذا كانت الملفات محدثة من GitHub، يمكنك المتابعة"
    echo "   💡 أو قم بتحديث الملفات يدوياً من GitHub"
    read -p "   هل تريد المتابعة؟ (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "   ✅ الكود الجديد موجود في معظم الملفات"
fi
echo ""

# 7. إيقاف Odoo
echo "7. إيقاف Odoo..."
pkill -f "odoo-bin.*lugal" || pkill -f odoo-bin || true
sleep 3
echo "   ✅ تم إيقاف Odoo"
echo ""

# 8. مسح الكاش
echo "8. مسح الكاش..."
rm -rf ~/.local/share/Odoo/filestore/lugal/* 2>/dev/null || true
rm -rf /tmp/odoo_* 2>/dev/null || true
rm -rf /tmp/odoo 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "   ✅ تم مسح الكاش"
echo ""

# 9. تحديث الوحدات
echo "9. تحديث الوحدات..."
echo "   جاري تحديث pos_perfume_custom و sap_integration..."
$PYTHON_CMD odoo-bin -c odoo.conf -d lugal \
    -u pos_perfume_custom,sap_integration \
    --stop-after-init \
    --log-level=warn 2>&1 | tail -30
echo "   ✅ تم تحديث الوحدات"
echo ""

# 10. مسح الكاش من قاعدة البيانات
echo "10. مسح الكاش من قاعدة البيانات..."
if [ -f "clear_cache_from_db.py" ]; then
    $PYTHON_CMD clear_cache_from_db.py 2>&1 | tail -20
else
    echo "   ⚠️  ملف clear_cache_from_db.py غير موجود، تخطي..."
fi
echo ""

# 11. التحقق من حالة الوحدات
echo "11. التحقق من حالة الوحدات..."
$PYTHON_CMD odoo-bin shell -c odoo.conf -d lugal << 'PYTHON_SCRIPT'
import odoo
from odoo.orm.registry import Registry
odoo.tools.config.parse_config(['--config=odoo.conf'])
db_name = odoo.tools.config.get('db_name') or 'lugal'
registry = Registry(db_name)
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

# 12. إعادة تشغيل Odoo
echo "12. إعادة تشغيل Odoo..."
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
echo "5. راقب السجل: tail -f odoo.log | grep -E 'POS|SAP|action_confirm|❌'"
echo ""

