# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_exchange_rate_usd_iqd = fields.Float(
        string='سعر الصرف الافتراضي (دولار → دينار)',
        default=1470.0,
        digits=(12, 2),
        help='معامل التحويل الافتراضي من الدولار الأمريكي إلى الدينار العراقي. '
             'سيتم استخدام هذه القيمة لجميع الفواتير الجديدة في نظام POS Perfume.',
        config_parameter='pos_perfume.default_exchange_rate_usd_iqd'
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        exchange_rate = params.get_param('pos_perfume.default_exchange_rate_usd_iqd', default='1470.0')
        res.update(
            default_exchange_rate_usd_iqd=float(exchange_rate)
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('pos_perfume.default_exchange_rate_usd_iqd', str(self.default_exchange_rate_usd_iqd))

