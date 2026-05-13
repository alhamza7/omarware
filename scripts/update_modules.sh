#!/bin/bash
cd /home/lugalai/Lugal-ai

# تفعيل البيئة الافتراضية
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "تحذير: لم يتم العثور على البيئة الافتراضية"
fi

# التأكد من تثبيت المكتبات المطلوبة
echo "التحقق من المكتبات المطلوبة..."
python3 -m pip install --quiet passlib psycopg2-binary lxml || true

# إيقاف الخادم إذا كان يعمل
pkill -f "odoo-bin.*lugal" || true
sleep 2

# تحديث الوحدات المعدلة
echo "تحديث الوحدات المعدلة..."
python3 odoo-bin -c odoo.conf -d lugal --http-port=8069 \
    -u pos_perfume_custom,sap_integration \
    --stop-after-init \
    --log-level=warn

# إزالة الكاش من النظام
echo "إزالة الكاش من النظام..."
rm -rf /home/lugalai/Lugal-ai/.local/share/Odoo/filestore/lugal/*
rm -rf /tmp/odoo_*
find /home/lugalai/Lugal-ai -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find /home/lugalai/Lugal-ai -type f -name "*.pyc" -delete 2>/dev/null || true

# إزالة الكاش من قاعدة البيانات
echo "إزالة الكاش من قاعدة البيانات..."
python3 odoo-bin shell -c odoo.conf -d lugal << 'PYTHON_SCRIPT'
import odoo
env = odoo.api.Environment(odoo.registry(odoo.tools.config['db_name']).cursor(), odoo.SUPERUSER_ID, {})
# حذف الكاش من ir_ui_view
env['ir.ui.view'].clear_caches()
# حذف الكاش من ir_qweb  
env['ir.qweb'].clear_caches()
# حذف الكاش من ir_http
env['ir.http'].clear_caches()
# حذف الكاش من ir_actions
env['ir.actions.actions'].clear_caches()
env.cr.commit()
print("تم حذف الكاش من قاعدة البيانات")
PYTHON_SCRIPT

echo "تم الانتهاء!"

