#!/bin/bash
# -*- coding: utf-8 -*-
# سكريبت شامل لحل مشكلة AssetsLoadingError
# خاصة مشكلة تحميل web_tour.interactive.min.js

echo "=========================================="
echo "حل مشكلة تحميل Assets (AssetsLoadingError)"
echo "=========================================="
echo ""

# الانتقال إلى مجلد المشروع
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai || {
    echo "❌ خطأ: لم يتم العثور على مجلد المشروع"
    exit 1
}

echo "✅ تم العثور على مجلد المشروع: $(pwd)"
echo ""

# قراءة اسم قاعدة البيانات من odoo.conf
DB_NAME=$(grep "^dbfilter" odoo.conf 2>/dev/null | sed 's/.*= *\^\([^.*]*\).*/\1/' || echo "lugal")
if [ -z "$DB_NAME" ] || [ "$DB_NAME" = "lugal.*" ]; then
    DB_NAME="lugal"
fi
echo "قاعدة البيانات: $DB_NAME"
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

# 4. مسح الكاش من قاعدة البيانات (بما في ذلك Assets)
echo "3. مسح الكاش من قاعدة البيانات..."
$PYTHON_CMD clear_cache_from_db.py
echo "   ✅ تم مسح الكاش من قاعدة البيانات"
echo ""

# 5. تحديث وحدة web_tour للتأكد من أنها مثبتة بشكل صحيح
echo "4. تحديث وحدة web_tour..."
$PYTHON_CMD odoo-bin -c odoo.conf -d "$DB_NAME" \
    -u web_tour \
    --stop-after-init \
    --log-level=warn 2>&1 | tail -20
echo "   ✅ تم تحديث وحدة web_tour"
echo ""

# 6. إعادة بناء Assets (عن طريق تحديث وحدة web)
echo "5. إعادة بناء Assets..."
$PYTHON_CMD odoo-bin -c odoo.conf -d "$DB_NAME" \
    -u web \
    --stop-after-init \
    --log-level=warn 2>&1 | tail -20
echo "   ✅ تم إعادة بناء Assets"
echo ""

# 7. إعادة تشغيل Odoo
echo "6. إعادة تشغيل Odoo..."
echo "   ℹ️  يمكنك تشغيل Odoo يدوياً باستخدام:"
echo "   $PYTHON_CMD odoo-bin -c odoo.conf -d $DB_NAME --http-port=8069"
echo ""
echo "   أو في الخلفية:"
echo "   nohup $PYTHON_CMD odoo-bin -c odoo.conf -d $DB_NAME --http-port=8069 > odoo.log 2>&1 &"
echo ""

echo "=========================================="
echo "✅ تم إكمال جميع الخطوات بنجاح!"
echo "=========================================="
echo ""
echo "الخطوات التالية:"
echo "1. إعادة تشغيل Odoo"
echo "2. فتح المتصفح ومسح الكاش (Ctrl+Shift+Delete أو Ctrl+F5)"
echo "3. إعادة تحميل الصفحة"
echo ""
