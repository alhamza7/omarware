# -*- coding: utf-8 -*-

import logging
import base64
import json
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class NBSNotesController(http.Controller):
    """Notes management controller"""
    
    @http.route('/api/notes', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def list_notes(self, document_id=None, folder_id=None, user_id=None, include_private=True, page=1, per_page=50, **kwargs):
        """
        List notes with filters.
        
        Params:
            document_id (int): Filter by document
            folder_id (int): Filter by folder
            user_id (int): Filter by user (defaults to current user)
            include_private (bool): Include private notes (default True, only shows user's own private notes)
            page (int): Page number
            per_page (int): Items per page
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            
            domain = [('active', '=', True)]
            
            # Filter by document
            if document_id:
                domain.append(('document_id', '=', document_id))
            
            # Filter by folder
            if folder_id:
                domain.append(('folder_id', '=', folder_id))
            
            # Filter by user (default to current user)
            if user_id is None:
                user_id = request.env.user.id
            
            if user_id:
                # Show user's own notes + public notes
                if include_private:
                    domain.append('|')
                    domain.append(('user_id', '=', user_id))
                    domain.append(('is_private', '=', False))
                else:
                    domain.append(('is_private', '=', False))
            
            Note = request.env['nbs.note']
            notes = Note.search(domain, limit=per_page, offset=(page-1)*per_page, order='is_pinned desc, write_date desc')
            total = Note.search_count(domain)
            
            # Filter by access rights
            accessible_notes = []
            for note in notes:
                if note.can_user_access():
                    accessible_notes.append({
                        'id': note.id,
                        'title': note.title,
                        'content': note.content,
                        'user_id': note.user_id.id,
                        'user_name': note.user_id.name,
                        'document_id': note.document_id.id if note.document_id else None,
                        'document_title': note.document_id.name if note.document_id else None,
                        'folder_id': note.folder_id.id if note.folder_id else None,
                        'folder_name': note.folder_id.name if note.folder_id else None,
                        'department_id': note.department_id.id if note.department_id else None,
                        'department_name': note.department_id.name if note.department_id else None,
                        'has_image': bool(note.image),
                        'image_filename': note.image_filename,
                        'is_private': note.is_private,
                        'is_pinned': note.is_pinned,
                        'color': note.color,
                        'created_at': note.create_date.isoformat() if note.create_date else None,
                        'updated_at': note.write_date.isoformat() if note.write_date else None,
                    })
            
            return {
                'success': True,
                'data': accessible_notes,
                'pagination': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total + per_page - 1) // per_page
                }
            }
        
        except Exception as e:
            _logger.error(f'List notes error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/notes/<int:note_id>', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_note(self, note_id, **kwargs):
        """Get single note with image"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            
            note = request.env['nbs.note'].browse(note_id)
            
            if not note.exists():
                return {'success': False, 'error': 'Note not found'}
            
            if not note.can_user_access():
                return {'success': False, 'error': 'Access denied'}
            
            data = {
                'id': note.id,
                'title': note.title,
                'content': note.content,
                'user_id': note.user_id.id,
                'user_name': note.user_id.name,
                'document_id': note.document_id.id if note.document_id else None,
                'document_title': note.document_id.name if note.document_id else None,
                'folder_id': note.folder_id.id if note.folder_id else None,
                'folder_name': note.folder_id.name if note.folder_id else None,
                'department_id': note.department_id.id if note.department_id else None,
                'department_name': note.department_id.name if note.department_id else None,
                'image': note.image.decode('utf-8') if note.image else None,  # Base64 string
                'image_filename': note.image_filename,
                'is_private': note.is_private,
                'is_pinned': note.is_pinned,
                'color': note.color,
                'created_at': note.create_date.isoformat() if note.create_date else None,
                'updated_at': note.write_date.isoformat() if note.write_date else None,
            }
            
            return {'success': True, 'data': data}
        
        except Exception as e:
            _logger.error(f'Get note error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/notes/create', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def create_note(self, **kwargs):
        """
        Create new note (with optional image).
        
        Body (JSON):
            content (required): Note text
            title (optional): Note title
            document_id (optional): Related document ID
            folder_id (optional): Related folder ID
            department_id (optional): Department ID
            image (optional): Base64 encoded image
            image_filename (optional): Image filename
            is_private (optional): Private note (default True)
            is_pinned (optional): Pin note (default False)
            color (optional): Color code (default 0)
        """
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'})
            
            # Parse JSON body
            try:
                raw_body = request.httprequest.get_data(as_text=True)
                _logger.info(f'[CREATE NOTE] Raw body type: {type(raw_body)}, length: {len(raw_body) if raw_body else 0}')
                
                if not raw_body:
                    return request.make_json_response({
                        'success': False,
                        'error': 'Request body is required'
                    })
                
                data = json.loads(raw_body)
                _logger.info(f'[CREATE NOTE] Parsed data type: {type(data)}')
                
                # Handle if data is a list (take first element)
                if isinstance(data, list):
                    _logger.info(f'[CREATE NOTE] Data is list, length: {len(data)}')
                    data = data[0] if data and isinstance(data[0], dict) else {}
                    _logger.info(f'[CREATE NOTE] After list handling, data type: {type(data)}')
                
                # Ensure data is a dict
                if not isinstance(data, dict):
                    return request.make_json_response({
                        'success': False,
                        'error': f'Request body must be a JSON object. Got: {type(data).__name__}'
                    })
                    
            except json.JSONDecodeError as je:
                _logger.error(f'[CREATE NOTE] JSON decode error: {str(je)}')
                return request.make_json_response({
                    'success': False,
                    'error': 'Invalid JSON'
                })
            
            # Validate required fields
            _logger.info(f'[CREATE NOTE] About to check content, data keys: {list(data.keys())}')
            if not data.get('content'):
                return request.make_json_response({
                    'success': False,
                    'error': 'Field "content" is required'
                })
            
            vals = {
                'content': data.get('content'),
                'title': data.get('title'),
                'user_id': request.env.user.id,
                'is_private': data.get('is_private', True),
                'is_pinned': data.get('is_pinned', False),
                'color': data.get('color', 0),
            }
            
            # Optional relations
            if data.get('document_id'):
                vals['document_id'] = data.get('document_id')
            
            if data.get('folder_id'):
                vals['folder_id'] = data.get('folder_id')
            
            if data.get('department_id'):
                vals['department_id'] = data.get('department_id')
            
            # Handle image
            if data.get('image'):
                vals['image'] = data.get('image')  # Expecting base64 string
                vals['image_filename'] = data.get('image_filename', 'image.png')
            
            note = request.env['nbs.note'].create(vals)
            
            return request.make_json_response({
                'success': True,
                'message': 'Note created successfully',
                'data': {
                    'id': note.id,
                    'created_at': note.create_date.isoformat() if note.create_date else None
                }
            })
        
        except Exception as e:
            _logger.error(f'Create note error: {str(e)}', exc_info=True)
            return request.make_json_response({'success': False, 'error': str(e)})
    
    @http.route('/api/notes/<int:note_id>/update', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def update_note(self, note_id, **kwargs):
        """Update note"""
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'})
            
            note = request.env['nbs.note'].browse(note_id)
            
            if not note.exists():
                return request.make_json_response({'success': False, 'error': 'Note not found'})
            
            # Only creator can update
            if note.user_id.id != request.env.user.id:
                return request.make_json_response({'success': False, 'error': 'Only creator can update'})
            
            # Parse JSON body
            try:
                raw_body = request.httprequest.get_data(as_text=True)
                if not raw_body:
                    return request.make_json_response({'success': False, 'error': 'Request body required'})
                
                data = json.loads(raw_body)
                
                # Handle if data is a list (take first element)
                if isinstance(data, list):
                    data = data[0] if data and isinstance(data[0], dict) else {}
                
                # Ensure data is a dict
                if not isinstance(data, dict):
                    return request.make_json_response({
                        'success': False,
                        'error': 'Request body must be a JSON object or array with object'
                    })
                    
            except json.JSONDecodeError:
                return request.make_json_response({'success': False, 'error': 'Invalid JSON'})
            
            updates = {}
            for key in ['title', 'content', 'is_private', 'is_pinned', 'color', 'image', 'image_filename']:
                if key in data:
                    updates[key] = data[key]
            
            if updates:
                note.write(updates)
            
            return request.make_json_response({
                'success': True,
                'message': 'Note updated successfully',
                'data': {
                    'updated_at': note.write_date.isoformat() if note.write_date else None
                }
            })
        
        except Exception as e:
            _logger.error(f'Update note error: {str(e)}', exc_info=True)
            return request.make_json_response({'success': False, 'error': str(e)})
    
    @http.route('/api/notes/<int:note_id>', type='http', auth='none', methods=['DELETE'], csrf=False, cors='*')
    def delete_note(self, note_id, **kwargs):
        """Delete note (soft delete - set active=False)"""
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'})
            
            note = request.env['nbs.note'].browse(note_id)
            
            if not note.exists():
                return request.make_json_response({'success': False, 'error': 'Note not found'})
            
            # Only creator or admin can delete
            if note.user_id.id != request.env.user.id and not request.env.user.has_group('nbs_archive.group_nbs_admin'):
                return request.make_json_response({'success': False, 'error': 'Permission denied'})
            
            note.write({'active': False})
            
            return request.make_json_response({
                'success': True,
                'message': 'Note deleted successfully'
            })
        
        except Exception as e:
            _logger.error(f'Delete note error: {str(e)}', exc_info=True)
            return request.make_json_response({'success': False, 'error': str(e)})
