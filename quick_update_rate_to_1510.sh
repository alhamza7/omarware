#!/bin/bash

echo "============================================================"
echo "تحديث سريع لسعر الصرف إلى 1510"
echo "============================================================"
echo ""

cd /home/lugalai/Lugal-ai

echo "1. التحقق من السعر الحالي..."
venv/bin/python -c "
import odoo
from odoo import api

odoo.tools.config.parse_config(['-c', 'odoo.conf'])
db_name = odoo.tools.config.get('db_name', '')
if isinstance(db_name, list):
    db_name = db_name[0] if db_name else 'nbs_lugalai'

with odoo.registry(db_name).cursor() as cr:
    env = api.Environment(cr, 1, {})
    
    usd = env['res.currency'].search([('name', '=', 'USD')], limit=1)
    if usd:
        latest_rate = env['res.currency.rate'].search([
            ('currency_id', '=', usd.id),
        ], order='name desc', limit=1)
        
        if latest_rate:
            current_rate = 1.0 / latest_rate.rate if latest_rate.rate != 0 else 0
            print(f'   السعر الحالي: 1 USD = {current_rate:.2f} IQD')
            print(f'   التاريخ: {latest_rate.name}')
        else:
            print('   ⚠️  لا يوجد سعر صرف محدد')
    else:
        print('   ❌ عملة USD غير موجودة')
"

echo ""
echo "2. تحديث السعر إلى 1510..."
venv/bin/python update_exchange_rate.py 1510

echo ""
echo "3. التحقق من النتيجة..."
venv/bin/python -c "
import odoo
from odoo import api

odoo.tools.config.parse_config(['-c', 'odoo.conf'])
db_name = odoo.tools.config.get('db_name', '')
if isinstance(db_name, list):
    db_name = db_name[0] if db_name else 'nbs_lugalai'

with odoo.registry(db_name).cursor() as cr:
    env = api.Environment(cr, 1, {})
    
    usd = env['res.currency'].search([('name', '=', 'USD')], limit=1)
    if usd:
        latest_rate = env['res.currency.rate'].search([
            ('currency_id', '=', usd.id),
        ], order='name desc', limit=1)
        
        if latest_rate:
            current_rate = 1.0 / latest_rate.rate if latest_rate.rate != 0 else 0
            print(f'   ✅ السعر الجديد: 1 USD = {current_rate:.2f} IQD')
            print(f'   ✅ التاريخ: {latest_rate.name}')
"

echo ""
echo "============================================================"
echo "✅ تم التحديث بنجاح!"
echo "============================================================"
echo ""
echo "الآن في المتصفح:"
echo "1. امسح الكاش (Ctrl+Shift+Delete)"
echo "2. أعد تحميل الصفحة (F5)"
echo "3. جميع الفواتير الجديدة ستستخدم السعر 1510"
echo ""
