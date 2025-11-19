#!/bin/bash
# سكريبت سريع لتحديث الوحدات ومسح الكاش لقاعدة بيانات lugal_nbs
# قاعدة البيانات موجودة بالفعل

echo "=========================================="
echo "تحديث سريع - قاعدة بيانات lugal_nbs"
echo "=========================================="
echo ""

cd ~/Lugal-ai || cd /home/lugalai/Lugal-ai || {
    echo "❌ خطأ: لم يتم العثور على مجلد المشروع"
    exit 1
}

# معلومات قاعدة البيانات
DB_NAME="lugal_nbs"
DB_USER="odoo_user1"
DB_PASSWORD="rooto"

# تحديد Python
if [ -f "venv/bin/python" ]; then
    PYTHON_CMD="venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python3"
fi

echo "✅ قاعدة البيانات: $DB_NAME"
echo "✅ استخدام: $PYTHON_CMD"
echo ""

# 1. إيقاف Odoo
echo "1. إيقاف Odoo..."
pkill -f "odoo-bin.*$DB_NAME" || pkill -f odoo-bin || true
sleep 2
echo "   ✅ تم إيقاف Odoo"
echo ""

# 2. مسح الكاش
echo "2. مسح الكاش..."
rm -rf ~/.local/share/Odoo/filestore/$DB_NAME/* 2>/dev/null || true
rm -rf /tmp/odoo_* 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "   ✅ تم مسح الكاش"
echo ""

# 3. تحديث الوحدات
echo "3. تحديث الوحدات..."
echo "   جاري تحديث pos_perfume_custom و sap_integration..."
$PYTHON_CMD odoo-bin -c odoo.conf -d "$DB_NAME" \
    -u pos_perfume_custom,sap_integration \
    --stop-after-init \
    --log-level=warn 2>&1 | tail -30
echo "   ✅ تم تحديث الوحدات"
echo ""

# 4. مسح الكاش من قاعدة البيانات
echo "4. مسح الكاش من قاعدة البيانات..."
if [ -f "clear_cache_from_db.py" ]; then
    $PYTHON_CMD clear_cache_from_db.py 2>&1 | tail -20
else
    echo "   ⚠️  ملف clear_cache_from_db.py غير موجود، تخطي..."
fi
echo ""

# 5. إعادة تشغيل Odoo
echo "5. إعادة تشغيل Odoo..."
echo "   استخدم الأمر التالي:"
echo ""
echo "   nohup $PYTHON_CMD odoo-bin -c odoo.conf -d $DB_NAME --http-port=8069 > odoo.log 2>&1 &"
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

