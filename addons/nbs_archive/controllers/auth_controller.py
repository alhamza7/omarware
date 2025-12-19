# -*- coding: utf-8 -*-

import json
import logging
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

from ._auth import ensure_jwt_user_id


class NBSAuthController(http.Controller):
    """Authentication controller"""
    
    def _json_response(self, data, status=200):
        """Create JSON response with CORS"""
        origin = request.httprequest.headers.get('Origin', '')
        headers = {
            'Content-Type': 'application/json',
        }
        
        if 'localhost' in origin or '127.0.0.1' in origin:
            headers['Access-Control-Allow-Origin'] = origin
            headers['Access-Control-Allow-Credentials'] = 'true'
        
        return Response(
            json.dumps(data, ensure_ascii=False),
            status=status,
            headers=list(headers.items())
        )
    
    @http.route('/api/auth/login', type='http', auth='none', methods=['POST'], csrf=False, cors='*', save_session=False)
    def login(self, **kwargs):
        """Login endpoint"""
        try:
            # Parse JSON from request body
            data = json.loads(request.httprequest.data.decode('utf-8'))
            
            # Extract params (handle both direct and JSON-RPC format)
            if 'params' in data:
                params = data['params']
                username = params.get('username')
                password = params.get('password')
            else:
                username = data.get('username')
                password = data.get('password')
            
            _logger.info(f'Login attempt for user: {username}')
            
            if not username or not password:
                return self._json_response({
                    'error': 'Username and password required',
                    'success': False
                }, 400)

            # Authenticate + generate JWT tokens
            jwt_service = request.env['nbs.jwt.service'].sudo()
            auth_result = jwt_service.authenticate_user(username, password)

            if not auth_result:
                return self._json_response({
                    'error': 'Invalid credentials',
                    'success': False
                }, 401)

            result = {'success': True, **auth_result}
            
            # Handle JSON-RPC format if requested
            if 'jsonrpc' in data:
                result = {'jsonrpc': '2.0', 'result': result}
            
            return self._json_response(result)
        
        except Exception as e:
            _logger.error(f'Login error: {str(e)}', exc_info=True)
            return self._json_response({
                'error': str(e),
                'success': False
            }, 500)
    
    @http.route('/api/auth/refresh', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def refresh(self, **kwargs):
        """Refresh token"""
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))

            refresh_token = data.get('refresh_token') or (data.get('params') or {}).get('refresh_token')
            if not refresh_token:
                return self._json_response({'success': False, 'error': 'refresh_token is required'}, 400)

            jwt_service = request.env['nbs.jwt.service'].sudo()
            refreshed = jwt_service.refresh_access_token(refresh_token)
            if not refreshed:
                return self._json_response({'success': False, 'error': 'Invalid refresh token'}, 401)

            result = {'success': True, **refreshed}

            if 'jsonrpc' in data:
                result = {'jsonrpc': '2.0', 'result': result}

            return self._json_response(result)

        except Exception as e:
            _logger.error(f'Refresh error: {str(e)}', exc_info=True)
            return self._json_response({'success': False, 'error': str(e)}, 500)
    
    @http.route('/api/auth/logout', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def logout(self, **kwargs):
        """Logout"""
        # Stateless JWT logout (client deletes tokens)
        return self._json_response({'success': True})
    
    @http.route('/api/auth/me', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def me(self, **kwargs):
        """Get current user"""
        uid = ensure_jwt_user_id()
        if not uid:
            return self._json_response({'success': False, 'error': 'Unauthorized'}, 401)

        user = request.env['res.users'].sudo().browse(uid)
        result = {
            'success': True,
            'user': {
                'id': user.id,
                'name': user.name,
                'username': user.login,
                'email': user.login,
                'departments': [],
                'language': user.preferred_nbs_language or 'ar_SA',
                'is_admin': user.has_group('nbs_archive.group_nbs_admin') or user.has_group('base.group_system'),
                'is_manager': user.has_group('nbs_archive.group_nbs_manager'),
                'uploaded_documents': 0,
                'pending_approvals': 0,
                'unread_notifications': 0,
            }
        }
        
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            if 'jsonrpc' in data:
                result = {'jsonrpc': '2.0', 'result': result}
        except:
            pass
        
        return self._json_response(result)
    
    # NOTE:
    # Dashboard stats endpoint is implemented in `admin_controller.py` as JSON-RPC:
    #   POST /api/stats/dashboard (type='jsonrpc')
    # Keeping a second definition here (type='http') can cause routing ambiguity.
