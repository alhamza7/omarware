# -*- coding: utf-8 -*-
"""
POS Perfume API v1 — Order Actions

Routes:
  POST /api/pos_perfume/v1/orders/<id>/confirm          Confirm order → creates sale.order + SAP sync
  POST /api/pos_perfume/v1/orders/<id>/quotation        Set state to 'quotation'
  POST /api/pos_perfume/v1/orders/<id>/cancel           Cancel order
  POST /api/pos_perfume/v1/orders/<id>/draft            Reset cancelled order to draft
  POST /api/pos_perfume/v1/orders/<id>/send_whatsapp    Send text message via WhatsApp
  POST /api/pos_perfume/v1/orders/<id>/send_whatsapp_image  Send image via WhatsApp
  GET  /api/pos_perfume/v1/orders/<id>/report           Download PDF report
  POST /api/pos_perfume/v1/orders/<id>/sync_sap         Force re-sync to SAP
  PUT  /api/pos_perfume/v1/orders/<id>/exchange_rate    Update IQD exchange rate on order
"""

import logging
from odoo import http
from odoo.http import request, Response

from ._helpers import _success, _error, _get_json_body, _check_auth, _serialize_order

_logger = logging.getLogger(__name__)


class PosPerfumeApiOrderActions(http.Controller):

    # -----------------------------------------------------------------------
    # State transitions
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>/confirm',
                type='http', auth='none', methods=['POST'], csrf=False)
    def confirm_order(self, order_id, **kwargs):
        """Confirm a POS order → creates/updates a sale.order in 'sale' state and syncs to SAP.

        POST /api/pos_perfume/v1/orders/123/confirm
        Allowed from: draft, quotation.
        Requires at least one order line.
        POS state  → 'sale'
        SO state   → 'sale'
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)
            if order.state in ('done', 'cancel'):
                return _error(f"Cannot confirm an order in '{order.state}' state")
            if not order.order_line_ids:
                return _error('Cannot confirm an order without lines')

            order.sudo().action_confirm()
            order.invalidate_recordset()

            return _success(_serialize_order(order), message='Order confirmed')
        except Exception as e:
            _logger.error('[POS API] confirm_order: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>/quotation',
                type='http', auth='none', methods=['POST'], csrf=False)
    def set_quotation(self, order_id, **kwargs):
        """Create a Quotation from this POS order.

        POST /api/pos_perfume/v1/orders/123/quotation
        Allowed from: draft.
        Requires at least one order line.
        POS state  → 'quotation'
        SO state   → 'draft'  (Odoo Quotation)
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)
            if order.state in ('done', 'cancel'):
                return _error(f"Cannot change state of a '{order.state}' order")
            if not order.order_line_ids:
                return _error('Cannot create a quotation without order lines')

            order.sudo().action_quotation()
            order.invalidate_recordset()

            return _success(_serialize_order(order), message='Quotation created')
        except Exception as e:
            _logger.error('[POS API] set_quotation: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>/cancel',
                type='http', auth='none', methods=['POST'], csrf=False)
    def cancel_order(self, order_id, **kwargs):
        """Cancel an order.

        POST /api/pos_perfume/v1/orders/123/cancel
        POS state → 'cancel'
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)
            if order.state == 'done':
                return _error("Cannot cancel a done order")

            order.sudo().action_cancel()
            order.invalidate_recordset()

            return _success(_serialize_order(order), message='Order cancelled')
        except Exception as e:
            _logger.error('[POS API] cancel_order: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>/draft',
                type='http', auth='none', methods=['POST'], csrf=False)
    def reset_to_draft(self, order_id, **kwargs):
        """Reset any order back to draft.

        POST /api/pos_perfume/v1/orders/123/draft
        POS state → 'draft'
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)

            order.sudo().action_draft()
            order.invalidate_recordset()

            return _success(_serialize_order(order), message='Order reset to draft')
        except Exception as e:
            _logger.error('[POS API] reset_to_draft: %s', e, exc_info=True)
            return _error(str(e), 500)

    # -----------------------------------------------------------------------
    # WhatsApp
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>/send_whatsapp',
                type='http', auth='none', methods=['POST'], csrf=False)
    def send_whatsapp(self, order_id, **kwargs):
        """Send order invoice as a WhatsApp text message.

        POST /api/pos_perfume/v1/orders/123/send_whatsapp
        Returns { sent: false, available: false } when ULTRAMSG is not configured.
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)

            # Pre-flight: ULTRAMSG must be configured
            ultramsg_config = request.env['ultramsg.config'].sudo().search(
                [('active', '=', True)], limit=1
            )
            if not ultramsg_config:
                return _success({
                    'sent': False,
                    'available': False,
                    'setup_required': (
                        'Configure ULTRAMSG in Odoo: '
                        'Settings → Technical → ULTRAMSG Config → New'
                    ),
                }, message='WhatsApp feature not configured')

            from odoo.addons.pos_perfume_custom.controllers.pos_perfume_controller import PosPerfumeController
            ctrl = PosPerfumeController()
            result = ctrl.send_whatsapp(order_id=order_id)

            if result.get('success'):
                return _success(
                    {'sent': True, 'message_id': result.get('message_id')},
                    message=result.get('message', 'Sent'),
                )
            return _error(result.get('error', 'Failed to send WhatsApp'))
        except Exception as e:
            _logger.error('[POS API] send_whatsapp: %s', e, exc_info=True)
            return _error(str(e), 500)

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>/send_whatsapp_image',
                type='http', auth='none', methods=['POST'], csrf=False)
    def send_whatsapp_image(self, order_id, **kwargs):
        """Send order invoice as a WhatsApp image.

        POST /api/pos_perfume/v1/orders/123/send_whatsapp_image
        Returns { sent: false, available: false } when wkhtmltoimage or ULTRAMSG is not available.
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)

            # Pre-flight: wkhtmltoimage must be installed
            try:
                from odoo.tools.misc import find_in_path
                find_in_path('wkhtmltoimage')
                wkhtmltoimage_ok = True
            except IOError:
                wkhtmltoimage_ok = False

            if not wkhtmltoimage_ok:
                return _success({
                    'sent': False,
                    'available': False,
                    'setup_required': 'sudo apt-get install wkhtmltopdf',
                }, message='WhatsApp image feature not available (wkhtmltoimage not installed)')

            # Pre-flight: ULTRAMSG must be configured
            ultramsg_config = request.env['ultramsg.config'].sudo().search(
                [('active', '=', True)], limit=1
            )
            if not ultramsg_config:
                return _success({
                    'sent': False,
                    'available': False,
                    'setup_required': (
                        'Configure ULTRAMSG in Odoo: '
                        'Settings → Technical → ULTRAMSG Config → New'
                    ),
                }, message='WhatsApp image feature not configured (ULTRAMSG missing)')

            from odoo.addons.pos_perfume_custom.controllers.pos_perfume_whatsapp_image import POSPerfumeWhatsAppImage
            ctrl = POSPerfumeWhatsAppImage()
            result = ctrl.send_whatsapp_image(order_id=order_id)

            if isinstance(result, dict):
                if result.get('success'):
                    return _success(
                        {'sent': True, 'message_id': result.get('message_id')},
                        message=result.get('message', 'Sent'),
                    )
                return _error(result.get('error', 'Failed to send WhatsApp image'))
            return _success({'sent': True}, message='WhatsApp image request sent')
        except Exception as e:
            _logger.error('[POS API] send_whatsapp_image: %s', e, exc_info=True)
            return _error(str(e), 500)

    # -----------------------------------------------------------------------
    # PDF Report
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>/report',
                type='http', auth='none', methods=['GET'], csrf=False)
    def get_order_report(self, order_id, download='true', **kwargs):
        """Download the order PDF report.

        GET /api/pos_perfume/v1/orders/123/report
        GET /api/pos_perfume/v1/orders/123/report?download=false  → inline view
        Returns the PDF binary, or JSON with pdf_available=false if wkhtmltopdf is missing.
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)

            # Pre-flight: wkhtmltopdf must be installed
            try:
                from odoo.tools.misc import find_in_path
                find_in_path('wkhtmltopdf')
                wkhtmltopdf_ok = True
            except IOError:
                wkhtmltopdf_ok = False

            if not wkhtmltopdf_ok:
                return _success({
                    'pdf_available': False,
                    'setup_required': 'sudo apt-get install wkhtmltopdf',
                }, message='PDF report not available (wkhtmltopdf not installed)')

            report = request.env.ref('pos_perfume_custom.action_report_pos_perfume_order')
            pdf_content, content_type = report._render_qweb_pdf(
                report_ref=report.report_name,
                res_ids=[order_id],
            )

            is_download = download.lower() in ('1', 'true', 'yes')
            disposition = 'attachment' if is_download else 'inline'
            headers = {
                'Content-Type': 'application/pdf',
                'Content-Disposition': f'{disposition}; filename="{order.name}.pdf"',
                'Content-Length': str(len(pdf_content)),
                'Access-Control-Allow-Origin': '*',
            }
            return Response(pdf_content, status=200, headers=headers, direct_passthrough=True)
        except Exception as e:
            _logger.error('[POS API] get_order_report: %s', e, exc_info=True)
            return _error(str(e), 500)

    # -----------------------------------------------------------------------
    # SAP Sync
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>/sync_sap',
                type='http', auth='none', methods=['POST'], csrf=False)
    def sync_sap(self, order_id, **kwargs):
        """Force re-sync the linked sale order to SAP.

        POST /api/pos_perfume/v1/orders/123/sync_sap
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)
            if not order.sale_order_id:
                return _error('No sale order linked. Please confirm the order first.')

            sale_order = order.sale_order_id
            sale_order._send_to_sap()
            sale_order.invalidate_recordset(['sap_synced', 'sap_doc_num', 'sap_doc_entry'])

            return _success({
                'sap_synced': order.sap_synced,
                'sap_doc_num': order.sap_doc_num or '',
                'sap_doc_entry': order.sap_doc_entry or 0,
                'sap_error_message': order.sap_error_message or '',
            }, message='SAP sync completed')
        except Exception as e:
            _logger.error('[POS API] sync_sap: %s', e, exc_info=True)
            return _error(str(e), 500)

    # -----------------------------------------------------------------------
    # Exchange rate
    # -----------------------------------------------------------------------

    @http.route('/api/pos_perfume/v1/orders/<int:order_id>/exchange_rate',
                type='http', auth='none', methods=['PUT'], csrf=False)
    def update_order_exchange_rate(self, order_id, **kwargs):
        """Update the IQD exchange rate on a specific order.

        PUT /api/pos_perfume/v1/orders/123/exchange_rate
        Body: { "exchange_rate": 1490.0 }
        Omit body (or send {}) to reset to the current system default.
        """
        try:
            auth_err = _check_auth()
            if auth_err:
                return auth_err

            order = request.env['pos.perfume.order'].browse(order_id)
            if not order.exists():
                return _error('Order not found', 404)

            body = _get_json_body()
            rate = body.get('exchange_rate')
            if rate is None:
                order.action_update_exchange_rate()
            else:
                order.write({'exchange_rate': float(rate)})

            return _success({
                'id': order.id,
                'exchange_rate': order.exchange_rate,
                'amount_total_iqd': order.amount_total_iqd,
            }, message='Exchange rate updated')
        except Exception as e:
            _logger.error('[POS API] update_order_exchange_rate: %s', e, exc_info=True)
            return _error(str(e), 500)
