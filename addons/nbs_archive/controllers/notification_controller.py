# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

from ._auth import ensure_jwt_user_id


class NBSNotificationController(http.Controller):
    """Notification management controller"""
    
    @http.route('/api/notifications', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_notifications(self, unread_only=False, page=1, per_page=20, **kwargs):
        """Get user notifications"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            domain = [('user_id', '=', request.env.user.id)]
            
            if unread_only:
                domain.append(('is_read', '=', False))
            
            Notification = request.env['nbs.notification']
            notifications = Notification.search(domain, limit=per_page, offset=(page-1)*per_page, order='create_date desc')
            total = Notification.search_count(domain)
            unread_count = Notification.search_count([('user_id', '=', request.env.user.id), ('is_read', '=', False)])
            
            return {
                'success': True,
                'data': [{
                    'id': notif.id,
                    'title': notif.title,
                    'message': notif.message,
                    'notification_type': notif.notification_type,
                    'is_read': notif.is_read,
                    'created_date': notif.create_date.isoformat() if notif.create_date else None,
                    'related_document_id': notif.related_document_id.id if notif.related_document_id else None,
                } for notif in notifications],
                'unread_count': unread_count,
                'pagination': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                }
            }
        
        except Exception as e:
            _logger.error(f'Get notifications error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/notifications/<int:notification_id>/mark-read', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def mark_as_read(self, notification_id, **kwargs):
        """Mark notification as read"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            notification = request.env['nbs.notification'].browse(notification_id)
            
            if not notification.exists():
                return {
                    'success': False,
                    'error': 'Notification not found'
                }
            
            # Check if notification belongs to current user
            if notification.user_id.id != request.env.user.id:
                return {
                    'success': False,
                    'error': 'Access denied'
                }
            
            notification.write({'is_read': True})
            
            return {
                'success': True,
                'message': 'Notification marked as read'
            }
        
        except Exception as e:
            _logger.error(f'Mark read error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/notifications/mark-all-read', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def mark_all_read(self, **kwargs):
        """Mark all notifications as read"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            notifications = request.env['nbs.notification'].search([
                ('user_id', '=', request.env.user.id),
                ('is_read', '=', False)
            ])
            
            notifications.write({'is_read': True})
            
            return {
                'success': True,
                'message': f'{len(notifications)} notifications marked as read'
            }
        
        except Exception as e:
            _logger.error(f'Mark all read error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/notifications/unread-count', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_unread_count(self, **kwargs):
        """Get count of unread notifications"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'count': 0}

            count = request.env['nbs.notification'].search_count([
                ('user_id', '=', request.env.user.id),
                ('is_read', '=', False)
            ])
            
            return {
                'success': True,
                'count': count
            }
        
        except Exception as e:
            _logger.error(f'Unread count error: {str(e)}')
            return {
                'success': False,
                'error': str(e),
                'count': 0
            }
