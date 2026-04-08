# -*- coding: utf-8 -*-

import json
import logging
from odoo import http
from odoo.http import request, Response
from odoo.api import Environment, SUPERUSER_ID
from odoo.modules.registry import Registry

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
        if origin and ('localhost' in origin or '127.0.0.1' in origin):
            headers['Access-Control-Allow-Origin'] = origin
            headers['Access-Control-Allow-Credentials'] = 'true'
        elif not origin or origin == 'null':
            headers['Access-Control-Allow-Origin'] = '*'
        return Response(
            json.dumps(data, ensure_ascii=False),
            status=status,
            headers=list(headers.items())
        )
    
    def _authenticate_in_db(self, dbname, username, password):
        """Authenticate in a given database (used when request has no db / nodb). Returns auth result or None."""
        try:
            registry = Registry(dbname)
            with registry.cursor() as cr:
                env = Environment(cr, SUPERUSER_ID, {})
                jwt_service = env['nbs.jwt.service'].sudo()
                return jwt_service.authenticate_user(username, password)
        except Exception as e:
            _logger.warning('Auth failed for db %s: %s', dbname, e)
            return None
    
    @http.route('/api/auth/login', type='http', auth='none', methods=['POST'], csrf=False, cors='*', save_session=False)
    def login(self, **kwargs):
        """Login endpoint (works with or without database in session; use X-Odoo-Database header or body.database)"""
        try:
            # Parse JSON from request body
            try:
                data = json.loads(request.httprequest.data.decode('utf-8') or '{}')
            except Exception:
                data = {}
            if isinstance(data, list):
                data = data[0] if data and isinstance(data[0], dict) else {}
            if not isinstance(data, dict):
                data = {}

            # Extract params (handle both direct and JSON-RPC format; params may be dict or list)
            if 'params' in data:
                params = data['params']
                if isinstance(params, list):
                    params = params[0] if params and isinstance(params[0], dict) else {}
                if not isinstance(params, dict):
                    params = {}
                username = params.get('username')
                password = params.get('password')
                database = params.get('database')
            else:
                username = data.get('username')
                password = data.get('password')
                database = data.get('database')
            
            # Database: from session, header, or body (required when no session db / nodb)
            dbname = getattr(request, 'db', None) or request.httprequest.headers.get('X-Odoo-Database') or database
            
            _logger.info(f'Login attempt for user: {username} db: {dbname}')
            
            if not username or not password:
                return self._json_response({
                    'error': 'Username and password required',
                    'success': False
                }, 400)

            # Use request.env if we have a db in session; otherwise authenticate in dbname
            if getattr(request, 'env', None) and request.db:
                jwt_service = request.env['nbs.jwt.service'].sudo()
                auth_result = jwt_service.authenticate_user(username, password)
            elif dbname:
                auth_result = self._authenticate_in_db(dbname, username, password)
                if auth_result is None:
                    return self._json_response({
                        'error': 'Database not found, not accessible, or invalid credentials',
                        'success': False
                    }, 400)
            else:
                return self._json_response({
                    'error': 'No database selected. Set X-Odoo-Database header or pass "database" in body (e.g. {"database":"lugal_local","username":"admin","password":"admin"})',
                    'success': False
                }, 400)

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
            if isinstance(data, list):
                data = data[0] if data and isinstance(data[0], dict) else {}
            if not isinstance(data, dict):
                data = {}
            params = data.get('params')
            if isinstance(params, list):
                params = params[0] if params and isinstance(params[0], dict) else {}
            if not isinstance(params, dict):
                params = {}
            refresh_token = data.get('refresh_token') or params.get('refresh_token')
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
