#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحديث سعر الصرف إلى 1510 عبر Odoo (نفس قاعدة البيانات التي يستخدمها التطبيق).
شغّل من مجلد المشروع على السيرفر:
  python3 set_exchange_rate_1510.py
  أو: python3 set_exchange_rate_1510.py --config=/home/lugalai/Lugal-ai/odoo.conf
"""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

def main():
    import odoo
    from odoo import api
    from odoo.orm.registry import Registry

    # قراءة odoo.conf من المجلد الحالي أو من الوسيط
    config_path = 'odoo.conf'
    for i, arg in enumerate(sys.argv):
        if arg.startswith('--config='):
            config_path = arg.split('=', 1)[1]
            break
    if not os.path.isabs(config_path):
        config_path = os.path.join(script_dir, config_path)

    odoo.tools.config.parse_config(['--config=%s' % config_path])
    db_name = odoo.tools.config.get('db_name') or ''
    if isinstance(db_name, list):
        db_name = db_name[0] if db_name else ''
    if not db_name and odoo.tools.config.get('dbfilter'):
        import re
        m = re.match(r'\^?(\w+).*\$?', odoo.tools.config.get('dbfilter'))
        if m:
            db_name = m.group(1)
    if not db_name:
        db_name = 'nbs_lugalai'

    print('قاعدة البيانات:', db_name)
    registry = Registry(db_name)
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        old = env['ir.config_parameter'].get_param('pos_perfume.default_exchange_rate_usd_iqd')
        print('القيمة الحالية في قاعدة البيانات:', old or '(غير موجود)')
        env['ir.config_parameter'].set_param('pos_perfume.default_exchange_rate_usd_iqd', '1510.0')
        cr.commit()
        value = env['ir.config_parameter'].get_param('pos_perfume.default_exchange_rate_usd_iqd')
    print('تم التحديث. السعر الآن:', value)
    print('')
    print('=' * 60)
    print('مهم: Odoo يخزّن هذه القيمة في الذاكرة (cache).')
    print('يجب إعادة تشغيل Odoo حتى يرى جميع المستخدمين 1510:')
    print('  sudo systemctl restart odoo')
    print('=' * 60)
    return 0

if __name__ == '__main__':
    sys.exit(main())
