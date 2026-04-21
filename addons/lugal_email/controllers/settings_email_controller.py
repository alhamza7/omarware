# -*- coding: utf-8 -*-
"""
Layer 3 — /api/crm/settings/email/*
User-facing CRUD for email account configuration (JSON-RPC).
"""

import logging
from odoo import http
from odoo.http import request
from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


def _crm_error(exc, handler=''):
    _logger.exception('%s error', handler)
    try:
        request.env.cr.rollback()
    except Exception:
        pass
    return {'success': False, 'error': str(exc)}


def _acc_to_dict(acc):
    return {
        'id':             acc.id,
        'name':           acc.name,
        'email_address':  acc.email_address,
        'display_name':   acc.display_name_field or '',
        'imap_host':      acc.imap_host or '',
        'imap_port':      acc.imap_port,
        'imap_use_ssl':   acc.imap_use_ssl,
        'smtp_host':      acc.smtp_host or '',
        'smtp_port':      acc.smtp_port,
        'smtp_use_tls':   acc.smtp_use_tls,
        'is_default':     acc.is_default,
        'is_active':      acc.is_active,
        'sync_status':    acc.sync_status or 'never',
        'last_sync_date': acc.last_sync_date.isoformat() if acc.last_sync_date else None,
        'unread_count':   acc.unread_count,
    }


class SettingsEmailController(http.Controller):

    @http.route('/api/crm/settings/email/accounts',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def list_accounts(self, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            accs = request.env['lugal.email.account'].sudo().search([
                ('user_id', '=', uid), ('is_deleted', '=', False),
            ])
            return {'success': True, 'data': [_acc_to_dict(a) for a in accs]}
        except Exception as exc:
            return _crm_error(exc, 'list_accounts')

    @http.route('/api/crm/settings/email/accounts/add',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def add_account(self, name, email_address, username=None, password=None,
                    imap_host='imap.gmail.com', imap_port=993, imap_use_ssl=True,
                    smtp_host='smtp.gmail.com', smtp_port=587, smtp_use_tls=True,
                    display_name=None, is_default=False, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().create({
                'user_id':           uid,
                'name':              name,
                'email_address':     email_address,
                'display_name_field': display_name or '',
                'username':          username or email_address,
                'password':          password or '',
                'imap_host':         imap_host,
                'imap_port':         int(imap_port),
                'imap_use_ssl':      imap_use_ssl,
                'smtp_host':         smtp_host,
                'smtp_port':         int(smtp_port),
                'smtp_use_tls':      smtp_use_tls,
                'is_default':        is_default,
            })
            if is_default:
                acc.action_set_default()
            return {'success': True, 'data': _acc_to_dict(acc)}
        except Exception as exc:
            return _crm_error(exc, 'add_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/update',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def update_account(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid or acc.is_deleted:
                return {'success': False, 'error': 'Account not found'}
            allowed = {
                'name', 'email_address', 'display_name_field', 'username', 'password',
                'imap_host', 'imap_port', 'imap_use_ssl',
                'smtp_host', 'smtp_port', 'smtp_use_tls', 'is_active',
            }
            vals = {k: v for k, v in kwargs.items() if k in allowed}
            if vals:
                acc.write(vals)
            return {'success': True, 'data': _acc_to_dict(acc)}
        except Exception as exc:
            return _crm_error(exc, 'update_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/delete',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def delete_account(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return {'success': False, 'error': 'Account not found'}
            acc.write({'is_deleted': True, 'active': False})
            return {'success': True}
        except Exception as exc:
            return _crm_error(exc, 'delete_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/test',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def test_account(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return {'success': False, 'error': 'Account not found'}
            return acc.action_test_connection()
        except Exception as exc:
            return _crm_error(exc, 'test_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/sync',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def sync_account(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return {'success': False, 'error': 'Account not found'}
            return acc.action_sync()
        except Exception as exc:
            return _crm_error(exc, 'sync_account')

    @http.route('/api/crm/settings/email/accounts/<int:account_id>/set_default',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def set_default(self, account_id, **kwargs):
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}
            acc = request.env['lugal.email.account'].sudo().browse(account_id)
            if not acc.exists() or acc.user_id.id != uid:
                return {'success': False, 'error': 'Account not found'}
            acc.action_set_default()
            return {'success': True, 'data': _acc_to_dict(acc)}
        except Exception as exc:
            return _crm_error(exc, 'set_default')
