#!/bin/bash
# تثبيت جميع المكتبات المطلوبة لوحدة nbs_archive

echo "============================================================"
echo "تثبيت مكتبات nbs_archive"
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

# تثبيت جميع المكتبات المطلوبة
echo "2. تثبيت المكتبات المطلوبة لـ nbs_archive..."

echo "   - تثبيت opensearch-py..."
venv/bin/pip install opensearch-py
if [ $? -eq 0 ]; then
    echo "     ✅ تم تثبيت opensearch-py"
else
    echo "     ❌ فشل تثبيت opensearch-py"
fi

echo "   - تثبيت PyJWT..."
venv/bin/pip install PyJWT
if [ $? -eq 0 ]; then
    echo "     ✅ تم تثبيت PyJWT"
else
    echo "     ❌ فشل تثبيت PyJWT"
fi

echo "   - تثبيت cryptography..."
venv/bin/pip install cryptography
if [ $? -eq 0 ]; then
    echo "     ✅ تم تثبيت cryptography"
else
    echo "     ❌ فشل تثبيت cryptography"
fi

echo "   - تثبيت requests..."
venv/bin/pip install requests
if [ $? -eq 0 ]; then
    echo "     ✅ تم تثبيت requests"
else
    echo "     ❌ فشل تثبيت requests"
fi

echo ""

# التحقق من التثبيت
echo "3. التحقق من المكتبات المثبتة..."
echo ""
venv/bin/pip list | grep -iE "opensearch|jwt|cryptography|requests"
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
    exit 1
fi

echo ""
echo "============================================================"
echo "✅ تم الانتهاء!"
echo "============================================================"
echo ""
echo "الآن يمكنك:"
echo "1. تثبيت وحدة sale من Apps"
echo "2. الوحدة nbs_archive يجب أن تعمل بدون مشاكل"
echo ""
echo "إذا ظهر خطأ مكتبة مفقودة أخرى، أرسل لي اسم المكتبة"
echo ""
