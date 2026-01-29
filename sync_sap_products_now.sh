#!/bin/bash
# سكريبت لمزامنة المنتجات من SAP فوراً

echo "============================================================"
echo "🔄 SAP Products Full Sync - Remote Server"
echo "============================================================"
echo ""

# تحديد مسار المشروع
PROJECT_DIR="/home/lugalai/Lugal-ai"
cd "$PROJECT_DIR" || {
    echo "❌ خطأ: لم يتم العثور على مجلد المشروع"
    exit 1
}

echo "✅ مجلد المشروع: $(pwd)"
echo ""

# قراءة اسم قاعدة البيانات
DB_NAME=$(grep "^db_name" odoo.conf 2>/dev/null | sed 's/.*= *\([^ ]*\).*/\1/' | head -1)
if [ -z "$DB_NAME" ]; then
    DB_NAME="nbs_lugalai"
fi

echo "قاعدة البيانات: $DB_NAME"
echo ""

# 1. التحقق من SAP Backend
echo "1. التحقق من SAP Backend..."
venv/bin/python -c "
import odoo
from odoo import api, SUPERUSER_ID
odoo.tools.config.parse_config(['-c', 'odoo.conf'])
with api.Environment.manage():
    env = api.Environment(odoo.registry('$DB_NAME').cursor(), SUPERUSER_ID, {})
    try:
        backend = env['sap.backend'].search([('active', '=', True)], limit=1)
        if backend:
            print(f'✅ Backend Active: {backend.name}')
            print(f'   URL: {backend.location}')
            try:
                result = backend.test_connection()
                print(f'✅ Connection Test: Success')
            except Exception as e:
                print(f'❌ Connection Test Failed: {e}')
                exit(1)
        else:
            print('❌ No active SAP Backend found!')
            print('   يرجى إنشاء SAP Backend من Odoo Interface أولاً')
            exit(1)
    except Exception as e:
        print(f'❌ Error: {e}')
        exit(1)
    finally:
        env.cr.close()
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ فشل التحقق من SAP Backend"
    echo "   يرجى التحقق من إعدادات SAP Backend في Odoo"
    exit 1
fi

echo ""

# 2. التحقق من/إنشاء Auto Sync Configuration
echo "2. التحقق من Auto Sync Configuration..."
venv/bin/python -c "
import odoo
from odoo import api, SUPERUSER_ID
odoo.tools.config.parse_config(['-c', 'odoo.conf'])
with api.Environment.manage():
    env = api.Environment(odoo.registry('$DB_NAME').cursor(), SUPERUSER_ID, {})
    try:
        auto_sync = env['sap.auto.sync'].search([('active', '=', True)], limit=1)
        if not auto_sync:
            print('⚠️  لم يتم العثور على Auto Sync Configuration')
            print('   جاري الإنشاء...')
            backend = env['sap.backend'].search([('active', '=', True)], limit=1)
            if backend:
                auto_sync = env['sap.auto.sync'].create({
                    'name': 'Remote Server Daily Sync',
                    'backend_id': backend.id,
                    'active': True,
                    'sync_products': True,
                    'sync_pricelists': True,
                    'sync_warehouse': False,
                    'sync_uom_groups': False,
                    'batch_size': 100,
                    'product_limit': 0,
                })
                env.cr.commit()
                print(f'✅ تم إنشاء Auto Sync: {auto_sync.name}')
            else:
                print('❌ لا يوجد Backend!')
                exit(1)
        else:
            print(f'✅ Auto Sync موجود: {auto_sync.name}')
    except Exception as e:
        print(f'❌ Error: {e}')
        exit(1)
    finally:
        env.cr.close()
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ فشل إعداد Auto Sync"
    exit 1
fi

echo ""

# 3. تفعيل Cron Job
echo "3. تفعيل Cron Job..."
venv/bin/python -c "
import odoo
from odoo import api, SUPERUSER_ID
odoo.tools.config.parse_config(['-c', 'odoo.conf'])
with api.Environment.manage():
    env = api.Environment(odoo.registry('$DB_NAME').cursor(), SUPERUSER_ID, {})
    try:
        cron = env['ir.cron'].search([('name', '=', 'SAP Daily Auto-Sync')], limit=1)
        if cron:
            cron.write({
                'active': True,
                'interval_number': 1,
                'interval_type': 'days',
            })
            env.cr.commit()
            print(f'✅ Cron Job Active')
            print(f'   Next Call: {cron.nextcall}')
        else:
            print('⚠️  Cron Job not found (يحتاج ترقية الوحدة)')
    except Exception as e:
        print(f'⚠️  Cron Warning: {e}')
    finally:
        env.cr.close()
"

echo ""

# 4. تشغيل Full Sync الآن
echo "4. تشغيل Full Sync من SAP..."
echo "   ⏳ هذا قد يستغرق عدة دقائق حسب عدد المنتجات..."
echo ""

venv/bin/python -c "
import odoo
from odoo import api, SUPERUSER_ID
import time
odoo.tools.config.parse_config(['-c', 'odoo.conf'])
with api.Environment.manage():
    env = api.Environment(odoo.registry('$DB_NAME').cursor(), SUPERUSER_ID, {})
    try:
        auto_sync = env['sap.auto.sync'].search([('active', '=', True)], limit=1)
        if auto_sync:
            print('🔄 Starting Full Sync...')
            print('')
            start_time = time.time()
            
            auto_sync.execute_sync()
            
            duration = time.time() - start_time
            print('')
            print('='*60)
            print(f'✅ Sync Completed!')
            print('='*60)
            print(f'Status: {auto_sync.last_sync_status}')
            print(f'Total Synced: {auto_sync.total_synced}')
            print(f'Total Errors: {auto_sync.total_errors}')
            print(f'Duration: {duration:.2f} seconds')
            print('')
            print('📄 Sync Log:')
            print('-'*60)
            print(auto_sync.last_sync_log)
        else:
            print('❌ No Auto Sync configuration found!')
            exit(1)
    except Exception as e:
        print(f'❌ Sync Error: {e}')
        import traceback
        traceback.print_exc()
        exit(1)
    finally:
        env.cr.close()
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ فشل Full Sync"
    echo "   تحقق من الأخطاء أعلاه"
    exit 1
fi

echo ""

# 5. عرض الإحصائيات
echo "5. الإحصائيات:"
echo ""
venv/bin/python -c "
import odoo
from odoo import api, SUPERUSER_ID
odoo.tools.config.parse_config(['-c', 'odoo.conf'])
with api.Environment.manage():
    env = api.Environment(odoo.registry('$DB_NAME').cursor(), SUPERUSER_ID, {})
    try:
        total_products = env['product.product'].search_count([])
        sap_products = env['sap.product.product'].search_count([])
        
        print(f'📦 Total Products in Odoo: {total_products}')
        print(f'🔗 Total SAP Product Bindings: {sap_products}')
        print('')
        
        # آخر 5 منتجات
        recent = env['product.product'].search([], order='create_date desc', limit=5)
        print('📦 Last 5 Products:')
        for p in recent:
            print(f'   - {p.name} (ID: {p.id})')
    except Exception as e:
        print(f'⚠️  Statistics Error: {e}')
    finally:
        env.cr.close()
"

echo ""
echo "============================================================"
echo "✅ تم الانتهاء!"
echo "============================================================"
echo ""
echo "الآن المنتجات من SAP يجب أن تكون موجودة في Odoo"
echo ""
echo "للتحقق:"
echo "1. افتح Odoo في المتصفح"
echo "2. اذهب إلى: Inventory → Products → Products"
echo "3. يجب أن ترى جميع المنتجات من SAP"
echo ""
echo "ملاحظة: سيتم المزامنة تلقائياً كل يوم الساعة 2:00 صباحاً"
echo ""
