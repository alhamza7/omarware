#!/bin/bash

echo "============================================================"
echo "إصلاح صلاحيات نظام الأرشفة NBS Archive"
echo "============================================================"
echo ""

# تحديد المستخدم الحالي
CURRENT_USER=$(whoami)
echo "المستخدم الحالي: $CURRENT_USER"

# تحديد مجلد filestore
ODOO_DATA_DIR="/var/lib/odoo"
FILESTORE_DIR="$ODOO_DATA_DIR/filestore"
DB_NAME="nbs_lugalai"
DB_FILESTORE="$FILESTORE_DIR/$DB_NAME"

echo ""
echo "1. التحقق من المجلدات..."
echo "   مجلد البيانات: $ODOO_DATA_DIR"
echo "   مجلد filestore: $FILESTORE_DIR"
echo "   مجلد قاعدة البيانات: $DB_FILESTORE"

# التحقق من وجود المجلدات
if [ ! -d "$ODOO_DATA_DIR" ]; then
    echo ""
    echo "⚠️  مجلد $ODOO_DATA_DIR غير موجود!"
    echo "   إنشاء المجلد..."
    sudo mkdir -p "$ODOO_DATA_DIR"
fi

if [ ! -d "$FILESTORE_DIR" ]; then
    echo ""
    echo "⚠️  مجلد $FILESTORE_DIR غير موجود!"
    echo "   إنشاء المجلد..."
    sudo mkdir -p "$FILESTORE_DIR"
fi

if [ ! -d "$DB_FILESTORE" ]; then
    echo ""
    echo "⚠️  مجلد $DB_FILESTORE غير موجود!"
    echo "   إنشاء المجلد..."
    sudo mkdir -p "$DB_FILESTORE"
fi

echo ""
echo "2. إصلاح الصلاحيات..."

# إعطاء صلاحيات للمستخدم الحالي
echo "   إعطاء ملكية المجلدات للمستخدم: $CURRENT_USER"
sudo chown -R $CURRENT_USER:$CURRENT_USER "$ODOO_DATA_DIR"

# إعطاء صلاحيات قراءة وكتابة
echo "   إعطاء صلاحيات rwx..."
sudo chmod -R 755 "$ODOO_DATA_DIR"

# صلاحيات خاصة لمجلد filestore
echo "   إعطاء صلاحيات كاملة لـ filestore..."
sudo chmod -R 775 "$FILESTORE_DIR"

# إنشاء مجلد خاص لنظام الأرشفة
NBS_ARCHIVE_DIR="$DB_FILESTORE/nbs_archive"
if [ ! -d "$NBS_ARCHIVE_DIR" ]; then
    echo "   إنشاء مجلد نظام الأرشفة..."
    sudo mkdir -p "$NBS_ARCHIVE_DIR"
fi
sudo chown -R $CURRENT_USER:$CURRENT_USER "$NBS_ARCHIVE_DIR"
sudo chmod -R 775 "$NBS_ARCHIVE_DIR"

echo ""
echo "3. التحقق من النتائج..."
echo ""
echo "   صلاحيات $ODOO_DATA_DIR:"
ls -ld "$ODOO_DATA_DIR"

echo ""
echo "   صلاحيات $FILESTORE_DIR:"
ls -ld "$FILESTORE_DIR"

echo ""
echo "   صلاحيات $DB_FILESTORE:"
ls -ld "$DB_FILESTORE"

if [ -d "$NBS_ARCHIVE_DIR" ]; then
    echo ""
    echo "   صلاحيات $NBS_ARCHIVE_DIR:"
    ls -ld "$NBS_ARCHIVE_DIR"
fi

echo ""
echo "4. اختبار الكتابة..."

# اختبار إنشاء ملف
TEST_FILE="$DB_FILESTORE/test_write_$(date +%s).txt"
if echo "Test write permission" > "$TEST_FILE" 2>/dev/null; then
    echo "   ✅ نجح اختبار الكتابة!"
    rm -f "$TEST_FILE"
else
    echo "   ❌ فشل اختبار الكتابة!"
    echo "   جرب تشغيل السكريبت بصلاحيات sudo"
fi

echo ""
echo "============================================================"
echo "✅ تم إصلاح الصلاحيات!"
echo "============================================================"
echo ""
echo "الآن:"
echo "1. أعد تشغيل Odoo"
echo "2. جرب رفع مستند في نظام الأرشفة"
echo ""
