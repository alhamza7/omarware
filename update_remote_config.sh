#!/bin/bash
# تحديث إعدادات قاعدة البيانات على سطح المكتب البعيد

echo "=========================================="
echo "تحديث إعدادات قاعدة البيانات"
echo "=========================================="
echo ""

cd ~/Lugal-ai || cd /home/lugalai/Lugal-ai || {
    echo "❌ خطأ: لم يتم العثور على مجلد المشروع"
    exit 1
}

# معلومات قاعدة البيانات الجديدة
DB_USER="odoo_user1"
DB_PASSWORD="rooto"
DB_NAME="lugal_nbs"

echo "معلومات قاعدة البيانات الجديدة:"
echo "   db_user: $DB_USER"
echo "   db_password: $DB_PASSWORD"
echo "   db_name: $DB_NAME"
echo ""

# التحقق من وجود odoo.conf
if [ ! -f "odoo.conf" ]; then
    echo "❌ ملف odoo.conf غير موجود!"
    exit 1
fi

# نسخ احتياطي
cp odoo.conf odoo.conf.backup
echo "✅ تم إنشاء نسخة احتياطية: odoo.conf.backup"
echo ""

# تحديث odoo.conf
echo "تحديث odoo.conf..."

# تحديث db_user
sed -i "s/^db_user = .*/db_user = $DB_USER/" odoo.conf

# تحديث db_password
sed -i "s/^db_password = .*/db_password = $DB_PASSWORD/" odoo.conf

# تحديث dbfilter
sed -i "s/^dbfilter = .*/dbfilter = ^${DB_NAME}.*$/" odoo.conf

echo "✅ تم تحديث odoo.conf"
echo ""

# عرض التغييرات
echo "التغييرات:"
grep -E "db_user|db_password|dbfilter" odoo.conf
echo ""

# التحقق من وجود قاعدة البيانات
echo "التحقق من وجود قاعدة البيانات..."
if command -v psql &> /dev/null; then
    PGPASSWORD="$DB_PASSWORD" psql -h localhost -U "$DB_USER" -d postgres -c "\l" 2>/dev/null | grep "$DB_NAME" && {
        echo "   ✅ قاعدة البيانات '$DB_NAME' موجودة"
    } || {
        echo "   ⚠️  قاعدة البيانات '$DB_NAME' غير موجودة"
        echo "   💡 قد تحتاج إلى إنشائها"
    }
else
    echo "   ⚠️  psql غير متوفر، لا يمكن التحقق من قاعدة البيانات"
fi
echo ""

echo "=========================================="
echo "✅ تم الانتهاء!"
echo "=========================================="
echo ""
echo "الخطوات التالية:"
echo "1. تأكد من وجود قاعدة البيانات: $DB_NAME"
echo "2. أعد تشغيل Odoo:"
echo "   venv/bin/python odoo-bin -c odoo.conf -d $DB_NAME"
echo ""

