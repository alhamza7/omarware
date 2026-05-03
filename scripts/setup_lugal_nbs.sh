#!/bin/bash
# سكريبت شامل لإعداد قاعدة بيانات lugal_nbs على سطح المكتب البعيد

echo "=========================================="
echo "إعداد قاعدة بيانات lugal_nbs"
echo "=========================================="
echo ""

cd ~/Lugal-ai || cd /home/lugalai/Lugal-ai || {
    echo "❌ خطأ: لم يتم العثور على مجلد المشروع"
    exit 1
}

# معلومات قاعدة البيانات
DB_USER="odoo_user1"
DB_PASSWORD="rooto"
DB_NAME="lugal_nbs"

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

# 1. تحديث odoo.conf
echo "1. تحديث odoo.conf..."
if [ -f "update_remote_config.sh" ]; then
    bash update_remote_config.sh
else
    echo "   ⚠️  ملف update_remote_config.sh غير موجود"
    echo "   💡 قم بتحديث odoo.conf يدوياً:"
    echo "      db_user = $DB_USER"
    echo "      db_password = $DB_PASSWORD"
    echo "      dbfilter = ^${DB_NAME}.*$"
fi
echo ""

# 2. إنشاء قاعدة البيانات
echo "2. إنشاء قاعدة البيانات..."
if [ -f "create_lugal_nbs_database.sh" ]; then
    bash create_lugal_nbs_database.sh
else
    echo "   ⚠️  ملف create_lugal_nbs_database.sh غير موجود"
    echo "   💡 قم بإنشاء قاعدة البيانات يدوياً:"
    echo "      PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d postgres -c \"CREATE DATABASE $DB_NAME;\""
fi
echo ""

# 3. إيقاف Odoo إذا كان يعمل
echo "3. إيقاف Odoo..."
pkill -f "odoo-bin.*$DB_NAME" || pkill -f "odoo-bin" || true
sleep 2
echo "   ✅ تم إيقاف Odoo"
echo ""

# 4. تهيئة قاعدة البيانات
echo "4. تهيئة قاعدة البيانات..."
echo "   جاري تهيئة قاعدة البيانات (قد يستغرق بضع دقائق)..."
$PYTHON_CMD odoo-bin -c odoo.conf -d "$DB_NAME" \
    --init=base \
    --stop-after-init \
    --log-level=warn 2>&1 | tail -20
echo "   ✅ تم تهيئة قاعدة البيانات"
echo ""

# 5. تثبيت الوحدات المطلوبة
echo "5. تثبيت الوحدات المطلوبة..."
echo "   جاري تثبيت pos_perfume_custom و sap_integration..."
$PYTHON_CMD odoo-bin -c odoo.conf -d "$DB_NAME" \
    -i pos_perfume_custom,sap_integration \
    --stop-after-init \
    --log-level=warn 2>&1 | tail -30
echo "   ✅ تم تثبيت الوحدات"
echo ""

# 6. مسح الكاش
echo "6. مسح الكاش..."
rm -rf ~/.local/share/Odoo/filestore/$DB_NAME/* 2>/dev/null || true
rm -rf /tmp/odoo_* 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "   ✅ تم مسح الكاش"
echo ""

# 7. إعادة تشغيل Odoo
echo "7. إعادة تشغيل Odoo..."
echo "   استخدم الأمر التالي:"
echo ""
echo "   nohup $PYTHON_CMD odoo-bin -c odoo.conf -d $DB_NAME --http-port=8069 > odoo.log 2>&1 &"
echo ""

echo "=========================================="
echo "✅ تم الانتهاء!"
echo "=========================================="
echo ""
echo "معلومات قاعدة البيانات:"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   URL: http://localhost:8069"
echo ""
echo "الخطوات التالية:"
echo "1. أعد تشغيل Odoo باستخدام الأمر أعلاه"
echo "2. افتح المتصفح: http://localhost:8069"
echo "3. سجل الدخول (admin/admin)"
echo "4. جرّب إنشاء quotation جديدة"
echo "5. راقب السجل: tail -f odoo.log | grep -E 'POS|SAP|action_confirm|❌'"
echo ""

