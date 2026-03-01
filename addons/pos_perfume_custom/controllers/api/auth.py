# -*- coding: utf-8 -*-
"""
POS Perfume API v1 — Auth, Setup, Settings, Pricelists, Warehouses

Routes:
  OPTIONS /api/pos_perfume/v1/*             CORS pre-flight
  GET     /api/pos_perfume/v1/session       Current user info
  GET     /api/pos_perfume/v1/setup         Bootstrap data (pricelists, warehouses, users, invoice_types)
  GET     /api/pos_perfume/v1/settings      Exchange rate setting
  PUT     /api/pos_perfume/v1/settings      Update exchange rate setting
  GET     /api/pos_perfume/v1/pricelists    All active pricelists
  GET     /api/pos_perfume/v1/warehouses    All active warehouses
"""

import logging
from odoo import http
from odoo.http import request, Response

from ._helpers import _success, _error, _get_json_body, _check_auth

_logger = logging.getLogger(__name__)


class PosPerfumeApiAuth(http.Controller):

    # -----------------------------------------------------------------------
    # CORS pre-flight — auth='none': no auth needed for OPTIONS
    # -----------------------------------------------------------------------

    @http.route(
        ['/api/pos_perfume/v1/<path:path>'],
        type='http', auth='none', methods=['OPTIONS'], csrf=False,
    )
    def handle_options(self, path='', **kwargs):
        """Handle CORS pre-flight requests for all API routes."""
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
            'Access-Control-Max-Age': '86400',
        }
        return Response('', status=204, headers=headers)

    # -----------------------------------------------------------------------
    # Session
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/session', type='http', auth='none', methods=['GET'], csrf=False)
    def get_session(self, **kwargs):
        """Return current authenticated user info and default exchange rate.

        GET /api/pos_perfume/v1/session
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            user = request.env.user
            exchange_rate = float(
                request.env['ir.config_parameter'].sudo().get_param(
                    'pos_perfume.default_exchange_rate_usd_iqd', '1470.0'
                )
            )
            return _success({
                'user_id': user.id,
                'user_name': user.name,
                'user_login': user.login,
                'company_id': user.company_id.id,
                'company_name': user.company_id.name,
                'uid': request.env.uid,
                'exchange_rate': exchange_rate,
            })
        except Exception as e:
            _logger.error('[POS API] session: %s', e, exc_info=True)
            return _error(str(e), 500)

    # -----------------------------------------------------------------------
    # Setup — single bootstrap call for external POS
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/setup', type='http', auth='none', methods=['GET'], csrf=False)
    def get_setup(self, **kwargs):
        """Return all data needed to boot the external POS in one call.

        GET /api/pos_perfume/v1/setup
        Returns: pricelists, warehouses, users, invoice_types, exchange_rate
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            env = request.env

            pricelists = env['product.pricelist'].search([('active', '=', True)])
            pricelist_data = [
                {'id': p.id, 'name': p.name, 'currency_id': p.currency_id.id}
                for p in pricelists
            ]

            warehouses = env['stock.warehouse'].search([('active', '=', True)])
            warehouse_data = [{'id': w.id, 'name': w.name, 'code': w.code} for w in warehouses]

            users = env['res.users'].search([('share', '=', False), ('active', '=', True)])
            user_data = [{'id': u.id, 'name': u.name} for u in users]

            exchange_rate = float(
                env['ir.config_parameter'].sudo().get_param(
                    'pos_perfume.default_exchange_rate_usd_iqd', '1470.0'
                )
            )

            invoice_types = [
                {'key': '1', 'label': 'زبون محل'},
                {'key': '2', 'label': 'شركات توصيل'},
                {'key': '3', 'label': 'نقليات'},
                {'key': '4', 'label': 'ديلفري'},
                {'key': '5', 'label': 'NBS'},
                {'key': '6', 'label': 'شورجة'},
                {'key': '7', 'label': 'NA'},
                {'key': '8', 'label': 'مكاتب الشورجة'},
            ]

            default_pricelist = env['pos.perfume.order']._get_default_pricelist()

            return _success({
                'pricelists': pricelist_data,
                'default_pricelist_id': default_pricelist,
                'warehouses': warehouse_data,
                'users': user_data,
                'invoice_types': invoice_types,
                'exchange_rate': exchange_rate,
                'currency': 'USD',
                'secondary_currency': 'IQD',
            })
        except Exception as e:
            _logger.error('[POS API] setup: %s', e, exc_info=True)
            return _error(str(e), 500)

    # -----------------------------------------------------------------------
    # Settings
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/settings', type='http', auth='none', methods=['GET'], csrf=False)
    def get_settings(self, **kwargs):
        """Return current POS settings (exchange rate).

        GET /api/pos_perfume/v1/settings
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            params = request.env['ir.config_parameter'].sudo()
            exchange_rate = float(
                params.get_param('pos_perfume.default_exchange_rate_usd_iqd', '1470.0')
            )
            return _success({'exchange_rate': exchange_rate})
        except Exception as e:
            _logger.error('[POS API] get_settings: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/settings', type='http', auth='none', methods=['PUT'], csrf=False)
    def update_settings(self, **kwargs):
        """Update POS settings.

        PUT /api/pos_perfume/v1/settings
        Body: { "exchange_rate": 1480.0 }
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            body = _get_json_body()
            if 'exchange_rate' in body:
                request.env['ir.config_parameter'].sudo().set_param(
                    'pos_perfume.default_exchange_rate_usd_iqd',
                    str(float(body['exchange_rate']))
                )
            params = request.env['ir.config_parameter'].sudo()
            exchange_rate = float(
                params.get_param('pos_perfume.default_exchange_rate_usd_iqd', '1470.0')
            )
            return _success({'exchange_rate': exchange_rate}, message='Settings updated')
        except Exception as e:
            _logger.error('[POS API] update_settings: %s', e, exc_info=True)
            return _error(str(e), 500)

    # -----------------------------------------------------------------------
    # Pricelists & Warehouses — convenience endpoints
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/pricelists', type='http', auth='none', methods=['GET'], csrf=False)
    def list_pricelists(self, **kwargs):
        """Get all active pricelists.

        GET /api/pos_perfume/v1/pricelists
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            pricelists = request.env['product.pricelist'].search([('active', '=', True)])
            data = [
                {'id': p.id, 'name': p.name, 'currency_id': p.currency_id.id,
                 'currency_name': p.currency_id.name}
                for p in pricelists
            ]
            return _success({'items': data, 'total': len(data)})
        except Exception as e:
            _logger.error('[POS API] list_pricelists: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/warehouses', type='http', auth='none', methods=['GET'], csrf=False)
    def list_warehouses(self, **kwargs):
        """Get all active warehouses.

        GET /api/pos_perfume/v1/warehouses
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            warehouses = request.env['stock.warehouse'].search([('active', '=', True)])
            data = [{'id': w.id, 'name': w.name, 'code': w.code} for w in warehouses]
            return _success({'items': data, 'total': len(data)})
        except Exception as e:
            _logger.error('[POS API] list_warehouses: %s', e, exc_info=True)
            return _error(str(e), 500)
