# -*- coding: utf-8 -*-

import jwt
import logging
from datetime import datetime, timedelta
from odoo import models, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class NBSJWTService(models.AbstractModel):
    _name = 'nbs.jwt.service'
    _description = 'JWT Authentication Service'
    
    def _get_secret_key(self):
        """Get JWT secret key from config"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'nbs_archive.jwt_secret_key',
            'default-secret-change-in-production'
        )
    
    def _get_refresh_secret_key(self):
        """Get JWT refresh secret key from config"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'nbs_archive.jwt_refresh_secret_key',
            'default-refresh-secret-change-in-production'
        )
    
    def _get_access_token_expire_minutes(self):
        """Get access token expiration time in minutes"""
        return int(self.env['ir.config_parameter'].sudo().get_param(
            'nbs_archive.jwt_access_token_expire_minutes',
            '480'  # 8 hours instead of 30 minutes
        ))
    
    def _get_refresh_token_expire_days(self):
        """Get refresh token expiration time in days"""
        return int(self.env['ir.config_parameter'].sudo().get_param(
            'nbs_archive.jwt_refresh_token_expire_days',
            '7'
        ))
    
    @api.model
    def generate_access_token(self, user_id):
        """
        Generate JWT access token
        
        Args:
            user_id: Odoo user ID
        
        Returns:
            JWT token string
        """
        user = self.env['res.users'].sudo().browse(user_id)
        if not user.exists():
            raise ValidationError('User not found')
        
        expire_minutes = self._get_access_token_expire_minutes()
        expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
        
        payload = {
            'user_id': user.id,
            'username': user.login,
            'exp': expire,
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        token = jwt.encode(
            payload,
            self._get_secret_key(),
            algorithm='HS256'
        )
        
        return token
    
    @api.model
    def generate_refresh_token(self, user_id):
        """
        Generate JWT refresh token
        
        Args:
            user_id: Odoo user ID
        
        Returns:
            JWT refresh token string
        """
        user = self.env['res.users'].sudo().browse(user_id)
        if not user.exists():
            raise ValidationError('User not found')
        
        expire_days = self._get_refresh_token_expire_days()
        expire = datetime.utcnow() + timedelta(days=expire_days)
        
        payload = {
            'user_id': user.id,
            'username': user.login,
            'exp': expire,
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        token = jwt.encode(
            payload,
            self._get_refresh_secret_key(),
            algorithm='HS256'
        )
        
        return token
    
    @api.model
    def verify_access_token(self, token):
        """
        Verify and decode access token
        
        Args:
            token: JWT token string
        
        Returns:
            Dict with user info if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self._get_secret_key(),
                algorithms=['HS256']
            )
            
            if payload.get('type') != 'access':
                _logger.warning('Invalid token type')
                return None
            
            user_id = payload.get('user_id')
            user = self.env['res.users'].sudo().browse(user_id)
            
            if not user.exists():
                _logger.warning(f'User {user_id} not found')
                return None
            
            return {
                'user_id': user.id,
                'username': user.login,
                'exp': payload.get('exp')
            }
        
        except jwt.ExpiredSignatureError:
            _logger.warning('Token expired')
            return None
        except jwt.InvalidTokenError as e:
            _logger.warning(f'Invalid token: {e}')
            return None
    
    @api.model
    def verify_refresh_token(self, token):
        """
        Verify and decode refresh token
        
        Args:
            token: JWT refresh token string
        
        Returns:
            Dict with user info if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self._get_refresh_secret_key(),
                algorithms=['HS256']
            )
            
            if payload.get('type') != 'refresh':
                _logger.warning('Invalid token type')
                return None
            
            user_id = payload.get('user_id')
            user = self.env['res.users'].sudo().browse(user_id)
            
            if not user.exists():
                _logger.warning(f'User {user_id} not found')
                return None
            
            return {
                'user_id': user.id,
                'username': user.login
            }
        
        except jwt.ExpiredSignatureError:
            _logger.warning('Refresh token expired')
            return None
        except jwt.InvalidTokenError as e:
            _logger.warning(f'Invalid refresh token: {e}')
            return None
    
    @api.model
    def authenticate_user(self, username, password):
        """
        Authenticate user with username/password
        
        Args:
            username: User login
            password: User password
        
        Returns:
            Dict with user info and tokens if successful, None if failed
        """
        try:
            # Use Odoo 19 authentication API (returns auth_info dict)
            credential = {'type': 'password', 'login': username, 'password': password}
            auth_info = self.env['res.users'].sudo().authenticate(credential, user_agent_env={})

            uid = auth_info.get('uid') if auth_info else None
            if not uid:
                return None

            user = self.env['res.users'].sudo().browse(uid)
            
            # Generate tokens
            access_token = self.generate_access_token(uid)
            refresh_token = self.generate_refresh_token(uid)
            
            # Get user departments with roles
            departments = []
            for dept in user.nbs_department_ids:
                role = 'manager' if dept in user.nbs_manager_department_ids else 'user'
                departments.append({
                    'id': dept.id,
                    'name': dept.name,
                    'code': dept.code,
                    'role': role
                })
            
            # Log successful login
            self.env['nbs.audit.log'].sudo().create({
                'user_id': uid,
                'action': 'login',
                'details': f'Successful login from API'
            })
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'bearer',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'username': user.login,
                    'email': user.email,
                    'departments': departments,
                    'language': user.preferred_nbs_language or 'ar_SA',
                    'is_admin': user.has_group('nbs_archive.group_nbs_admin')
                }
            }
        
        except Exception as e:
            _logger.error(f'Authentication failed: {e}')
            return None
    
    @api.model
    def refresh_access_token(self, refresh_token):
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: JWT refresh token string
        
        Returns:
            New access token if valid, None if invalid
        """
        payload = self.verify_refresh_token(refresh_token)
        
        if not payload:
            return None
        
        # Generate new access token
        access_token = self.generate_access_token(payload['user_id'])
        
        return {
            'access_token': access_token,
            'token_type': 'bearer'
        }


