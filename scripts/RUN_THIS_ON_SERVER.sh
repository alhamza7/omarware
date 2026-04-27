#!/bin/bash

echo "🔧 إصلاح مشكلة الترميز العربي في PDF - Odoo"
echo "=================================================="
echo ""

# 1. مسح ذاكرة wkhtmltopdf المؤقتة
echo "⏳ 1/6 - مسح الذاكرة المؤقتة..."
sudo rm -rf /tmp/wkhtmlto* 2>/dev/null
sudo rm -rf /tmp/wktemp* 2>/dev/null
echo "✅ تم مسح الذاكرة المؤقتة"
echo ""

# 2. تثبيت خطوط إضافية
echo "⏳ 2/6 - تثبيت خطوط إضافية..."
sudo apt-get install -y fonts-liberation fonts-liberation2 2>/dev/null
echo "✅ تم تثبيت خطوط Liberation"
echo ""

# 3. تحديث ذاكرة الخطوط
echo "⏳ 3/6 - تحديث ذاكرة الخطوط..."
sudo fc-cache -f -v 2>&1 | grep -i "dejavu\|arab\|succeeded"
echo "✅ تم تحديث ذاكرة الخطوط"
echo ""

# 4. تحديث إعدادات locale
echo "⏳ 4/6 - تحديث locale..."
sudo locale-gen en_US.UTF-8 2>/dev/null
echo "✅ تم تحديث locale"
echo ""

# 5. مسح ذاكرة Odoo cache
echo "⏳ 5/6 - مسح ذاكرة Odoo..."
sudo find /var/lib/odoo -name "*.pyc" -delete 2>/dev/null
sudo find /home/lugalai/Lugal-ai -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
echo "✅ تم مسح ذاكرة Odoo"
echo ""

# 6. إعادة تشغيل Odoo بشكل كامل
echo "⏳ 6/6 - إعادة تشغيل Odoo..."
sudo systemctl stop odoo
sleep 3
sudo pkill -9 -f odoo 2>/dev/null
sleep 2
sudo systemctl start odoo
sleep 5
echo "✅ تم إعادة تشغيل Odoo"
echo ""

# التحقق من النجاح
echo "=================================================="
echo "📊 التحقق من التثبيت:"
echo ""

# عدد الخطوط
DEJAVU_COUNT=$(fc-list | grep -i dejavu | wc -l)
echo "✓ خطوط DejaVu المثبتة: $DEJAVU_COUNT"

# حالة Odoo
ODOO_STATUS=$(sudo systemctl is-active odoo)
echo "✓ حالة Odoo: $ODOO_STATUS"

echo ""
echo "=================================================="
echo "✅ تم إكمال جميع الخطوات!"
echo ""
echo "📋 الخطوات التالية:"
echo "1. افتح المتصفح"
echo "2. Apps → POS Perfume Custom → Upgrade"
echo "3. Ctrl + Shift + Delete (امسح الكاش)"
echo "4. Ctrl + F5 (أعد تحميل)"
echo "5. جرّب الطباعة"
echo ""
echo "🎯 إذا ما زالت المشكلة موجودة، أخبرني!"
echo "=================================================="

