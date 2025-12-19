# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

from ._auth import ensure_jwt_user_id


class NBSWebSocketController(http.Controller):
    """WebSocket controller for real-time notifications"""
    
    @http.route('/api/ws/poll', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def poll_notifications(self, last_poll_id=0, **kwargs):
        """
        Poll for new notifications (simple polling as fallback to WebSocket)
        
        Params:
        - last_poll_id: int - last notification ID received
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': [], 'has_new': False}

            # Get new notifications since last poll
            notifications = request.env['nbs.notification'].search([
                ('user_id', '=', request.env.user.id),
                ('id', '>', last_poll_id),
                ('is_read', '=', False)
            ], order='create_date desc')
            
            return {
                'success': True,
                'data': [{
                    'id': notif.id,
                    'title': notif.title,
                    'message': notif.message,
                    'notification_type': notif.notification_type,
                    'created_date': notif.create_date.isoformat() if notif.create_date else None,
                    'related_document_id': notif.related_document_id.id if notif.related_document_id else None,
                } for notif in notifications],
                'has_new': len(notifications) > 0
            }
        
        except Exception as e:
            _logger.error(f'Poll notifications error: {str(e)}')
            return {
                'success': False,
                'error': str(e),
                'data': []
            }
