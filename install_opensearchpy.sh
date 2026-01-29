#!/bin/bash
# تثبيت مكتبة opensearchpy المطلوبة لوحدة nbs_archive

echo "============================================================"
echo "تثبيت مكتبة opensearchpy"
echo "============================================================"
echo ""

# تحديد مسار المشروع
PROJECT_DIR="/home/lugalai/Lugal-ai"
cd "$PROJECT_DIR" || {
    echo "❌ خطأ: لم يتم العثور على مجلد المشروع"
    exit 1
}

echo "✅ مجلد المشروع: $(pwd)"
echo ""

# إيقاف Odoo
echo "1. إيقاف Odoo..."
pkill -9 -f odoo-bin
sleep 3
echo "   ✅ تم إيقاف Odoo"
echo ""

# تثبيت opensearch-py
echo "2. تثبيت مكتبة opensearch-py..."
venv/bin/pip install opensearch-py
if [ $? -eq 0 ]; then
    echo "   ✅ تم تثبيت opensearch-py بنجاح"
else
    echo "   ❌ فشل تثبيت opensearch-py"
    exit 1
fi
echo ""

# تثبيت المكتبات المرتبطة (إذا لزم الأمر)
echo "3. تثبيت المكتبات المرتبطة..."
venv/bin/pip install urllib3 certifi
echo "   ✅ تم تثبيت المكتبات المرتبطة"
echo ""

# إعادة تشغيل Odoo
echo "4. إعادة تشغيل Odoo..."
DB_NAME=$(grep "^db_name" odoo.conf 2>/dev/null | sed 's/.*= *\([^ ]*\).*/\1/' | head -1)
if [ -z "$DB_NAME" ]; then
    DB_NAME="nbs_lugalai"
fi

nohup venv/bin/python odoo-bin -c odoo.conf -d "$DB_NAME" --http-port=8069 > odoo.log 2>&1 &
sleep 5

# التحقق من التشغيل
if pgrep -f "odoo-bin.*$DB_NAME" > /dev/null; then
    echo "   ✅ Odoo يعمل الآن"
    PID=$(pgrep -f "odoo-bin.*$DB_NAME")
    echo "   PID: $PID"
else
    echo "   ❌ فشل تشغيل Odoo"
    echo "   تحقق من الخطأ في: tail -50 odoo.log"
fi

echo ""
echo "============================================================"
echo "✅ تم الانتهاء!"
echo "============================================================"
echo ""
echo "الآن يمكنك:"
echo "1. تثبيت وحدة sale أو أي وحدة أخرى من Apps"
echo "2. الوحدة nbs_archive يجب أن تعمل بدون مشاكل"
echo ""
