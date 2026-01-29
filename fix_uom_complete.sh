#!/bin/bash

echo "============================================================"
echo "إصلاح شامل لخطأ UoM Transaction"
echo "============================================================"
echo ""

# الانتقال إلى مجلد المشروع
cd /home/lugalai/Lugal-ai

echo "1. إيقاف Odoo..."
pkill -9 -f odoo-bin
sleep 3
echo "   ✅ تم إيقاف Odoo"

echo ""
echo "2. تشغيل سكريبت إصلاح UoM..."
venv/bin/python fix_uom_transaction_error.py

echo ""
echo "3. تحديث وحدة uom..."
venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai -u uom --stop-after-init

echo ""
echo "4. تحديث قاعدة البيانات الكاملة..."
venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai -u all --stop-after-init

echo ""
echo "5. إعادة تشغيل Odoo..."
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &
echo "   PID: $!"
sleep 5

echo ""
echo "6. التحقق من حالة Odoo..."
if pgrep -f "odoo-bin" > /dev/null; then
    echo "   ✅ Odoo يعمل بنجاح!"
    echo ""
    echo "تحقق من اللوغات:"
    echo "   tail -50 odoo.log"
else
    echo "   ❌ فشل تشغيل Odoo!"
    echo ""
    echo "تحقق من الخطأ:"
    echo "   tail -100 odoo.log"
fi

echo ""
echo "============================================================"
echo "✅ انتهى سكريبت الإصلاح"
echo "============================================================"
echo ""
echo "الآن في المتصفح:"
echo "1. امسح الكاش (Ctrl+Shift+Delete)"
echo "2. سجل خروج"
echo "3. سجل دخول مرة أخرى"
echo ""
