# -*- coding: utf-8 -*-

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fragrantica_auto_scraping_enabled = fields.Boolean(
        string='Enable Auto Scraping',
        config_parameter='lugal_fragrantica.auto_scraping_enabled',
        default=False,
        help='Enable automatic scraping of Fragrantica perfumes'
    )
