#!/bin/bash
# سكريبت لإصلاح قائمة Sale على السيرفر البعيد

echo "============================================================"
echo "إصلاح قائمة Sale - السيرفر البعيد"
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

# قراءة اسم قاعدة البيانات
DB_NAME=$(grep "^db_name" odoo.conf 2>/dev/null | sed 's/.*= *\([^ ]*\).*/\1/' | head -1)
if [ -z "$DB_NAME" ]; then
    DB_NAME=$(grep "^dbfilter" odoo.conf 2>/dev/null | sed 's/.*= *\^\([^.*]*\).*/\1/' | head -1)
fi
if [ -z "$DB_NAME" ] || [ "$DB_NAME" = "lugal.*" ]; then
    DB_NAME="nbs_lugalai"
fi

echo "قاعدة البيانات: $DB_NAME"
echo ""

# 1. إيقاف Odoo
echo "1. إيقاف Odoo..."
pkill -9 -f odoo-bin
sleep 3
echo "   ✅ تم إيقاف Odoo"
echo ""

# 2. تثبيت/ترقية وحدة sale
echo "2. تثبيت/ترقية وحدة sale..."
venv/bin/python odoo-bin -c odoo.conf -d "$DB_NAME" -i sale --stop-after-init
if [ $? -eq 0 ]; then
    echo "   ✅ تم تثبيت/ترقية وحدة sale"
else
    echo "   ⚠️  حدث خطأ أثناء التثبيت، محاولة الترقية..."
    venv/bin/python odoo-bin -c odoo.conf -d "$DB_NAME" -u sale --stop-after-init
fi
echo ""

# 3. إصلاح active_id error
echo "3. إصلاح active_id error..."
venv/bin/python fix_sale_menu_action.py
echo ""

# 4. تشغيل سكريبت فحص وإصلاح Sale
echo "4. تشغيل سكريبت الفحص والإصلاح..."
venv/bin/python check_sale_module.py
echo ""

# 5. إصلاح القوائم الفرعية (Sub Menus)
echo "5. إصلاح القوائم الفرعية في Sales..."
venv/bin/python fix_sale_submenus.py
echo ""

# 6. تفعيل جميع القوائم وجميع التصنيفات
echo "6. تفعيل جميع قوائم Sale وجميع التصنيفات..."
venv/bin/python activate_all_sale_menus.py
echo ""

# 7. إصلاح Action Views
echo "7. إصلاح Action Views (View types not defined)..."
venv/bin/python fix_action_views.py
echo ""

# 8. إعادة تشغيل Odoo
echo "8. إعادة تشغيل Odoo..."
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
echo "الخطوات التالية في المتصفح:"
echo "1. امسح كاش المتصفح (Ctrl+Shift+Delete)"
echo "2. سجل خروج من Odoo"
echo "3. سجل دخول مرة أخرى"
echo "4. يجب أن تظهر قائمة Sales/المبيعات"
echo ""
