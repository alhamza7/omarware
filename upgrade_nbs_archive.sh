#!/bin/bash

echo "============================================================"
echo "ترقية وحدة NBS Archive"
echo "Upgrade NBS Archive Module"
echo "============================================================"
echo ""

cd /home/lugalai/Lugal-ai

echo "1. إيقاف Odoo..."
pkill -9 -f odoo-bin
sleep 3

if pgrep -f "odoo-bin" > /dev/null; then
    echo "   ⚠️  Odoo ما زال يعمل، محاولة إيقاف بقوة..."
    sudo killall -9 python3
    sleep 2
fi

echo "   ✅ تم إيقاف Odoo"
echo ""

echo "2. ترقية وحدة nbs_archive..."
venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai \
    -u nbs_archive --stop-after-init

if [ $? -eq 0 ]; then
    echo "   ✅ تمت الترقية بنجاح"
else
    echo "   ❌ فشلت الترقية - تحقق من اللوغات"
    tail -50 odoo.log
    exit 1
fi

echo ""
echo "3. إعادة تشغيل Odoo..."
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai \
    --http-port=8069 > odoo.log 2>&1 &

ODOO_PID=$!
echo "   PID: $ODOO_PID"
sleep 5

if pgrep -f "odoo-bin" > /dev/null; then
    echo "   ✅ Odoo يعمل بنجاح!"
else
    echo "   ❌ فشل تشغيل Odoo!"
    echo ""
    echo "   📋 آخر 20 سطر من اللوغات:"
    tail -20 odoo.log
    exit 1
fi

echo ""
echo "============================================================"
echo "✅ تمت الترقية بنجاح!"
echo "============================================================"
echo ""
echo "📊 حالة النظام:"
ps aux | grep odoo-bin | grep -v grep
echo ""
echo "🌐 يمكنك الآن الوصول للنظام:"
echo "   http://192.168.116.211:8069"
echo ""
echo "📝 لعرض اللوغات:"
echo "   tail -f odoo.log"
echo ""
