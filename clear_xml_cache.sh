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

# 2. مسح الكاش من النظام
echo ""
echo "2. مسح الكاش من النظام..."
rm -rf ~/.local/share/Odoo/filestore/lugal/* 2>/dev/null || true
rm -rf /tmp/odoo_* 2>/dev/null || true
find ~/Lugal-ai -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find ~/Lugal-ai -type f -name "*.pyc" -delete 2>/dev/null || true

# 3. التحقق من الملف المُصلح
echo ""
echo "3. التحقق من الملف المُصلح..."
head -5 addons/sap_integration/views/sap_dashboard_views.xml

# 4. تحديث المودول مع --stop-after-init
echo ""
echo "4. تحديث المودول..."
python3 odoo-bin -c odoo.conf -d lugal \
    -u sap_integration \
    --stop-after-init \
    --log-level=error

# 5. إعادة تشغيل Odoo
echo ""
echo "5. إعادة تشغيل Odoo..."
python3 odoo-bin -c odoo.conf -d lugal --http-port=8069 &

echo ""
echo "=========================================="
echo "تم الانتهاء!"
echo "=========================================="

