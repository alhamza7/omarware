# -*- coding: utf-8 -*-

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Auto Scraping Settings
    fragrantica_auto_scraping_enabled = fields.Boolean(
        string='Enable Auto Scraping',
        config_parameter='lugal_fragrantica.auto_scraping_enabled',
        default=False,
        help='Enable automatic scraping of Fragrantica perfumes'
    )
    
    fragrantica_scraping_method = fields.Selection([
        ('manual', 'Manual'),
        ('auto', 'Automatic'),
        ('scheduled', 'Scheduled')
    ], string='Scraping Method',
        config_parameter='lugal_fragrantica.scraping_method',
        default='manual',
        help='Method for scraping Fragrantica perfumes'
    )
    
    fragrantica_auto_scraping_interval = fields.Integer(
        string='Auto Scraping Interval (minutes)',
        config_parameter='lugal_fragrantica.auto_scraping_interval',
        default=60,
        help='Interval in minutes for automatic scraping'
    )
    
    fragrantica_batch_size = fields.Integer(
        string='Batch Size',
        config_parameter='lugal_fragrantica.batch_size',
        default=10,
        help='Number of perfumes to scrape in each batch'
    )
    
    fragrantica_api_key = fields.Char(
        string='Fragrantica API Key',
        config_parameter='lugal_fragrantica.api_key',
        help='API key for Fragrantica integration (if available)'
    )
    
    fragrantica_max_retries = fields.Integer(
        string='Max Retries',
        config_parameter='lugal_fragrantica.max_retries',
        default=3,
        help='Maximum number of retries for failed scraping attempts'
    )
