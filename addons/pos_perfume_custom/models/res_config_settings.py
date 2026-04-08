# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_perfume_exchange_rate = fields.Float(
        string='سعر الصرف الافتراضي (دولار → دينار)',
        default=1550.0,
        digits=(12, 2),
        help='معامل التحويل الافتراضي من الدولار الأمريكي إلى الدينار العراقي. '
             'سيتم استخدام هذه القيمة لجميع الفواتير الجديدة في نظام POS Perfume.',
        config_parameter='pos_perfume.default_exchange_rate_usd_iqd'
    )


