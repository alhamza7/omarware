#!/bin/bash
# إنشاء قاعدة بيانات lugal_nbs على سطح المكتب البعيد

echo "=========================================="
echo "إنشاء قاعدة بيانات lugal_nbs"
echo "=========================================="
echo ""

# معلومات قاعدة البيانات
DB_USER="odoo_user1"
DB_PASSWORD="rooto"
DB_NAME="lugal_nbs"
DB_HOST="localhost"
DB_PORT="5432"

echo "معلومات قاعدة البيانات:"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   User: $DB_USER"
echo "   Database: $DB_NAME"
echo ""

# التحقق من وجود قاعدة البيانات
echo "1. التحقق من وجود قاعدة البيانات..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 && {
    echo "   ✅ قاعدة البيانات '$DB_NAME' موجودة بالفعل"
    read -p "   هل تريد حذفها وإنشاء جديدة؟ (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   جاري حذف قاعدة البيانات القديمة..."
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" && {
            echo "   ✅ تم حذف قاعدة البيانات القديمة"
        } || {
            echo "   ❌ فشل حذف قاعدة البيانات"
            exit 1
        }
    else
        echo "   تم الإلغاء"
        exit 0
    fi
} || {
    echo "   ℹ️  قاعدة البيانات '$DB_NAME' غير موجودة"
}
echo ""

# إنشاء قاعدة البيانات
echo "2. إنشاء قاعدة البيانات..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres << EOF
CREATE DATABASE $DB_NAME
    WITH OWNER = $DB_USER
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;
EOF

if [ $? -eq 0 ]; then
    echo "   ✅ تم إنشاء قاعدة البيانات '$DB_NAME' بنجاح"
else
    echo "   ❌ فشل إنشاء قاعدة البيانات"
    exit 1
fi
echo ""

# التحقق من الإنشاء
echo "3. التحقق من الإنشاء..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1 && {
    echo "   ✅ قاعدة البيانات '$DB_NAME' تعمل بشكل صحيح"
} || {
    echo "   ❌ فشل الاتصال بقاعدة البيانات"
    exit 1
}
echo ""

echo "=========================================="
echo "✅ تم الانتهاء!"
echo "=========================================="
echo ""
echo "الخطوات التالية:"
echo "1. قم بتحديث odoo.conf (استخدم update_remote_config.sh)"
echo "2. قم بتهيئة قاعدة البيانات:"
echo "   venv/bin/python odoo-bin -c odoo.conf -d $DB_NAME --init=base --stop-after-init"
echo "3. قم بتثبيت الوحدات المطلوبة:"
echo "   venv/bin/python odoo-bin -c odoo.conf -d $DB_NAME -i pos_perfume_custom,sap_integration --stop-after-init"
echo "4. أعد تشغيل Odoo:"
echo "   venv/bin/python odoo-bin -c odoo.conf -d $DB_NAME"
echo ""

