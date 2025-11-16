#!/bin/bash
# سكريبت لمسح الكاش وإعادة تحميل ملفات XML

echo "=========================================="
echo "مسح الكاش وإعادة تحميل ملفات XML"
echo "=========================================="

cd ~/Lugal-ai || exit 1

# 1. إيقاف Odoo
echo ""
echo "1. إيقاف Odoo..."
pkill -f odoo-bin || true
sleep 2

# 2. التحقق من virtual environment وتثبيت passlib
echo ""
echo "2. التحقق من virtual environment وتثبيت passlib..."
if [ -d "venv" ]; then
    echo "✅ تم العثور على virtual environment"
    PIP_CMD="venv/bin/pip"
    PYTHON_CMD="venv/bin/python"
elif [ -d ".venv" ]; then
    echo "✅ تم العثور على virtual environment (.venv)"
    PIP_CMD=".venv/bin/pip"
    PYTHON_CMD=".venv/bin/python"
else
    echo "⚠️  لم يتم العثور على virtual environment"
    echo "   محاولة استخدام pip3 مع --break-system-packages..."
    PIP_CMD="pip3 --break-system-packages"
    PYTHON_CMD="python3"
fi

echo ""
echo "3. تثبيت passlib..."
$PIP_CMD install passlib==1.7.4 || echo "⚠️  فشل تثبيت passlib"

# 4. مسح الكاش من النظام
echo ""
echo "4. مسح الكاش من النظام..."
rm -rf ~/.local/share/Odoo/filestore/lugal/* 2>/dev/null || true
rm -rf /tmp/odoo_* 2>/dev/null || true
find ~/Lugal-ai -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find ~/Lugal-ai -type f -name "*.pyc" -delete 2>/dev/null || true

# 5. التحقق من الملف المُصلح
echo ""
echo "3. التحقق من الملف المُصلح..."
head -5 addons/sap_integration/views/sap_dashboard_views.xml

# 6. تحديث المودول مع --stop-after-init
echo ""
echo "6. تحديث المودول..."
$PYTHON_CMD odoo-bin -c odoo.conf -d lugal \
    -u sap_integration \
    --stop-after-init \
    --log-level=error

# 7. إعادة تشغيل Odoo
echo ""
echo "7. إعادة تشغيل Odoo..."
$PYTHON_CMD odoo-bin -c odoo.conf -d lugal --http-port=8069 &

echo ""
echo "=========================================="
echo "تم الانتهاء!"
echo "=========================================="

