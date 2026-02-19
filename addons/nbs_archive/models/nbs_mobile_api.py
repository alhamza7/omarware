# -*- coding: utf-8 -*-
from odoo import models, fields, api


class NBSMobileSession(models.Model):
    _name = 'nbs.mobile.session'
    _description = 'Mobile App Sessions'
    
    user_id = fields.Many2one('res.users', string='User', required=True)
    device_id = fields.Char(string='Device ID', required=True)
    device_type = fields.Selection([
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web Mobile')
    ], string='Device Type')
    
    fcm_token = fields.Char(string='FCM Push Token')
    app_version = fields.Char(string='App Version')
    
    last_sync = fields.Datetime(string='Last Sync')
    is_active = fields.Boolean(string='Active', default=True)
    
    create_date = fields.Datetime(string='First Login', readonly=True)


class NBSMobileSync(models.Model):
    _name = 'nbs.mobile.sync'
    _description = 'Mobile Data Sync'
    
    user_id = fields.Many2one('res.users', required=True)
    sync_type = fields.Selection([
        ('full', 'Full Sync'),
        ('incremental', 'Incremental'),
        ('selective', 'Selective')
    ], default='incremental')
    
    last_sync_date = fields.Datetime()
    status = fields.Selection([
        ('pending', 'Pending'),
        ('syncing', 'Syncing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending')
    
    synced_documents = fields.Integer(string='Documents Synced')
    synced_folders = fields.Integer(string='Folders Synced')
    
    error_log = fields.Text(string='Errors')
