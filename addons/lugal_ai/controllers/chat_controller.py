# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class ChatController(http.Controller):
    
    @http.route('/lugal/chat', type='http', auth='user', website=True)
    def chat_interface(self, **kwargs):
        """Render chat interface"""
        return request.render('lugal_ai.chat_interface_template', {
            'user': request.env.user,
            'role': request.env['lugal.permission'].get_user_role(),
        })
    
    @http.route('/lugal/api/chat/history', type='json', auth='user', methods=['POST'], csrf=False)
    def get_chat_history(self, limit=50, offset=0, **kwargs):
        """Get user's conversation history"""
        try:
            conversations = request.env['lugal.conversation'].search([
                ('user_id', '=', request.env.user.id),
            ], limit=limit, offset=offset, order='create_date desc')
            
            return {
                'success': True,
                'conversations': [{
                    'id': c.id,
                    'question': c.question,
                    'answer': c.answer,
                    'category': c.category,
                    'create_date': c.create_date.strftime('%Y-%m-%d %H:%M:%S') if c.create_date else '',
                    'response_time_ms': c.response_time_ms,
                    'was_cached': c.was_cached,
                    'user_rating': c.user_rating,
                } for c in conversations],
                'total_count': request.env['lugal.conversation'].search_count([
                    ('user_id', '=', request.env.user.id),
                ]),
            }
            
        except Exception as e:
            _logger.error(f"Error getting chat history: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/lugal/api/chat/stats', type='json', auth='user', methods=['POST'], csrf=False)
    def get_user_stats(self, days=30, **kwargs):
        """Get user's usage statistics"""
        try:
            stats = request.env['lugal.conversation'].get_conversation_stats(
                user_id=request.env.user.id,
                days=days,
            )
            
            return {
                'success': True,
                'stats': stats,
            }
            
        except Exception as e:
            _logger.error(f"Error getting user stats: {str(e)}")
            return {'success': False, 'error': str(e)}

