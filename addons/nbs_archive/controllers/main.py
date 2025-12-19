# -*- coding: utf-8 -*-

import json
import logging
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class NBSMainController(http.Controller):
    """Main controller for CORS and common utilities"""
    
    def _get_allowed_origins(self):
        """Get allowed CORS origins from config"""
        try:
            config = request.env['ir.config_parameter'].sudo()
            origins_str = config.get_param(
                'nbs_archive.allowed_origins',
                'http://localhost:5173,http://localhost:3000'
            )
            return [origin.strip() for origin in origins_str.split(',')]
        except:
            # Fallback if config not available
            return ['http://localhost:5173', 'http://localhost:3000']
    
    def _set_cors_headers(self):
        """Set CORS headers for cross-origin requests"""
        origin = request.httprequest.headers.get('Origin')
        
        # In development, allow all origins from localhost
        if origin and 'localhost' in origin:
            headers = {
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, PATCH',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Max-Age': '3600'
            }
        else:
            allowed_origins = self._get_allowed_origins()
            headers = {}
            
            if origin in allowed_origins or '*' in allowed_origins:
                headers.update({
                    'Access-Control-Allow-Origin': origin or '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, PATCH',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Max-Age': '3600'
                })
        
        return headers
    
    def _make_json_response(self, data, status=200):
        """Create JSON response with CORS headers"""
        headers = self._set_cors_headers()
        headers['Content-Type'] = 'application/json'
        
        return Response(
            json.dumps(data, ensure_ascii=False, default=str),
            status=status,
            headers=headers
        )
    
    def _make_error_response(self, message, status=400, error_code=None):
        """Create error response"""
        return self._make_json_response({
            'error': message,
            'error_code': error_code,
            'success': False
        }, status=status)
    
    def _verify_jwt_token(self):
        """
        Verify JWT token from Authorization header
        
        Returns:
            User ID if valid, None if invalid
        """
        auth_header = request.httprequest.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        jwt_service = request.env['nbs.jwt.service'].sudo()
        payload = jwt_service.verify_access_token(token)
        
        if payload:
            return payload['user_id']
        
        return None
    
    @http.route('/api/<path:path>', type='http', auth='none', methods=['OPTIONS'], csrf=False)
    def handle_preflight(self, **kwargs):
        """Handle CORS preflight requests"""
        headers = self._set_cors_headers()
        return Response('', status=200, headers=headers)
    
    @http.route('/api/health', type='http', auth='none', methods=['GET'], csrf=False)
    def health_check(self):
        """Health check endpoint"""
        return self._make_json_response({
            'status': 'healthy',
            'service': 'NBS Archive API',
            'version': '1.0.0'
        })

