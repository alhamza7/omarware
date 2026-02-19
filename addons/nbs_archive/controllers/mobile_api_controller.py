# -*- coding: utf-8 -*-
import logging
from odoo import http, fields
from odoo.http import request
from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class MobileAPIController(http.Controller):
    
    @http.route('/api/mobile/sync', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def mobile_sync(self, last_sync_date=None, **kwargs):
        """Sync data for mobile app"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            
            domain = [('is_deleted', '=', False)]
            if last_sync_date:
                domain.append(('write_date', '>', last_sync_date))
            
            documents = request.env['nbs.document'].search(domain, limit=50)
            
            return {
                'success': True,
                'data': {
                    'documents': [{
                        'id': d.id,
                        'name': d.name,
                        'state': d.state,
                        'updated_at': d.write_date.isoformat() if d.write_date else None
                    } for d in documents],
                    'sync_date': fields.Datetime.now().isoformat()
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/mobile/register', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def register_device(self, device_id, device_type, fcm_token=None, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            
            session = request.env['nbs.mobile.session'].create({
                'user_id': request.env.user.id,
                'device_id': device_id,
                'device_type': device_type,
                'fcm_token': fcm_token
            })
            
            return {'success': True, 'data': {'session_id': session.id}}
        except Exception as e:
            return {'success': False, 'error': str(e)}
