# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class NBSDepartmentManagementController(http.Controller):
    """Department CRUD Management Controller"""
    
    # ==================== DEPARTMENTS ====================
    
    @http.route('/api/departments', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_departments(self, include_inactive=False, **kwargs):
        """Get list of all departments"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            domain = []
            if not include_inactive:
                domain.append(('active', '=', True))
            
            departments = request.env['nbs.department'].search(domain, order='sequence, name')
            
            return {
                'success': True,
                'data': [{
                    'id': dept.id,
                    'name': dept.name,
                    'code': dept.code,
                    'description': dept.description,
                    'active': dept.active,
                    'sequence': dept.sequence,
                    'manager_ids': [{'id': m.id, 'name': m.name} for m in dept.manager_ids],
                    'document_count': dept.document_count,
                } for dept in departments]
            }
        
        except Exception as e:
            _logger.error(f'Get departments error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/departments/<int:department_id>', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_department(self, department_id, **kwargs):
        """Get single department details"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            department = request.env['nbs.department'].browse(department_id)
            
            if not department.exists():
                return {'success': False, 'error': 'Department not found'}
            
            return {
                'success': True,
                'data': {
                    'id': department.id,
                    'name': department.name,
                    'code': department.code,
                    'description': department.description,
                    'active': department.active,
                    'sequence': department.sequence,
                    'manager_ids': [{'id': m.id, 'name': m.name} for m in department.manager_ids],
                    'document_count': department.document_count,
                    'document_type_count': len(department.document_type_ids),
                }
            }
        
        except Exception as e:
            _logger.error(f'Get department error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/departments/create', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def create_department(self, name, code, description=None, manager_ids=None, sequence=10, **kwargs):
        """Create new department"""
        try:
            user_id = ensure_jwt_user_id()
            if not user_id:
                return {'success': False, 'error': 'Unauthorized'}

            # Check if user is admin
            if not request.env.user.has_group('nbs_archive.group_nbs_admin'):
                return {'success': False, 'error': 'Admin permission required'}

            # Check if code already exists
            existing = request.env['nbs.department'].search([('code', '=', code)], limit=1)
            if existing:
                return {'success': False, 'error': f'Department with code "{code}" already exists'}

            # Prepare values
            values = {
                'name': name,
                'code': code,
                'description': description,
                'sequence': sequence,
                'active': True,
            }
            
            if manager_ids:
                values['manager_ids'] = [(6, 0, manager_ids)]
            
            # Create department
            department = request.env['nbs.department'].create(values)
            
            # Log
            request.env['nbs.audit.log'].create({
                'action': 'department_created',
                'user_id': user_id,
                'details': f'Created department: {name} ({code})'
            })
            
            return {
                'success': True,
                'message': 'تم إنشاء القسم بنجاح',
                'data': {
                    'id': department.id,
                    'name': department.name,
                    'code': department.code
                }
            }
        
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f'Create department error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/departments/<int:department_id>/update', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def update_department(self, department_id, name=None, code=None, description=None, 
                         manager_ids=None, sequence=None, active=None, **kwargs):
        """Update department"""
        try:
            user_id = ensure_jwt_user_id()
            if not user_id:
                return {'success': False, 'error': 'Unauthorized'}

            # Check if user is admin
            if not request.env.user.has_group('nbs_archive.group_nbs_admin'):
                return {'success': False, 'error': 'Admin permission required'}

            department = request.env['nbs.department'].browse(department_id)
            
            if not department.exists():
                return {'success': False, 'error': 'Department not found'}

            # Prepare updates
            updates = {}
            
            if name is not None:
                updates['name'] = name
            
            if code is not None:
                # Check if new code already exists
                existing = request.env['nbs.department'].search([
                    ('code', '=', code),
                    ('id', '!=', department_id)
                ], limit=1)
                if existing:
                    return {'success': False, 'error': f'Department with code "{code}" already exists'}
                updates['code'] = code
            
            if description is not None:
                updates['description'] = description
            
            if sequence is not None:
                updates['sequence'] = sequence
            
            if active is not None:
                updates['active'] = active
            
            if manager_ids is not None:
                updates['manager_ids'] = [(6, 0, manager_ids)]
            
            if updates:
                department.write(updates)
                
                # Log
                request.env['nbs.audit.log'].create({
                    'action': 'department_updated',
                    'user_id': user_id,
                    'details': f'Updated department: {department.name}'
                })
            
            return {
                'success': True,
                'message': 'تم تحديث القسم بنجاح',
                'data': {
                    'id': department.id,
                    'name': department.name,
                    'code': department.code
                }
            }
        
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f'Update department error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/departments/<int:department_id>', type='http', auth='none', methods=['DELETE'], csrf=False, cors='*')
    def delete_department(self, department_id, **kwargs):
        """Delete department (archive)"""
        try:
            user_id = ensure_jwt_user_id()
            if not user_id:
                return request.make_json_response({'success': False, 'error': 'Unauthorized'})

            # Check if user is admin
            if not request.env.user.has_group('nbs_archive.group_nbs_admin'):
                return request.make_json_response({'success': False, 'error': 'Admin permission required'})

            department = request.env['nbs.department'].browse(department_id)
            
            if not department.exists():
                return request.make_json_response({'success': False, 'error': 'Department not found'})

            # Check if department has documents
            if department.document_count > 0:
                return request.make_json_response({
                    'success': False,
                    'error': f'Cannot delete department with {department.document_count} documents. Archive it instead.'
                })

            # Archive (set inactive)
            department.write({'active': False})
            
            # Log
            request.env['nbs.audit.log'].create({
                'action': 'department_archived',
                'user_id': user_id,
                'details': f'Archived department: {department.name}'
            })
            
            return request.make_json_response({
                'success': True,
                'message': 'تم أرشفة القسم بنجاح'
            })
        
        except Exception as e:
            _logger.error(f'Delete department error: {str(e)}', exc_info=True)
            return request.make_json_response({'success': False, 'error': str(e)})
    
    # ==================== DOCUMENT TYPES ====================
    
    @http.route('/api/document-types', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_document_types(self, department_id=None, include_inactive=False, **kwargs):
        """Get list of document types"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            domain = []
            
            if department_id:
                domain.append(('department_id', '=', department_id))
            
            if not include_inactive:
                domain.append(('active', '=', True))
            
            doc_types = request.env['nbs.document.type'].search(domain, order='sequence, name')
            
            return {
                'success': True,
                'data': [{
                    'id': dt.id,
                    'name': dt.name,
                    'code': dt.code,
                    'description': dt.description,
                    'department_id': dt.department_id.id,
                    'department_name': dt.department_id.name,
                    'active': dt.active,
                    'sequence': dt.sequence,
                    'document_count': dt.document_count,
                } for dt in doc_types]
            }
        
        except Exception as e:
            _logger.error(f'Get document types error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/document-types/<int:doc_type_id>', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_document_type(self, doc_type_id, **kwargs):
        """Get single document type details"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            doc_type = request.env['nbs.document.type'].browse(doc_type_id)
            
            if not doc_type.exists():
                return {'success': False, 'error': 'Document type not found'}
            
            return {
                'success': True,
                'data': {
                    'id': doc_type.id,
                    'name': doc_type.name,
                    'code': doc_type.code,
                    'description': doc_type.description,
                    'department_id': doc_type.department_id.id,
                    'department_name': doc_type.department_id.name,
                    'active': doc_type.active,
                    'sequence': doc_type.sequence,
                    'document_count': doc_type.document_count,
                }
            }
        
        except Exception as e:
            _logger.error(f'Get document type error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/document-types/create', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def create_document_type(self, name, code, department_id, description=None, sequence=10, **kwargs):
        """Create new document type"""
        try:
            user_id = ensure_jwt_user_id()
            if not user_id:
                return {'success': False, 'error': 'Unauthorized'}

            # Check if user is admin or manager
            if not (request.env.user.has_group('nbs_archive.group_nbs_admin') or 
                    request.env.user.has_group('nbs_archive.group_nbs_manager')):
                return {'success': False, 'error': 'Manager or Admin permission required'}

            # Check if code already exists
            existing = request.env['nbs.document.type'].search([('code', '=', code)], limit=1)
            if existing:
                return {'success': False, 'error': f'Document type with code "{code}" already exists'}

            # Prepare values
            values = {
                'name': name,
                'code': code,
                'department_id': department_id,
                'description': description,
                'sequence': sequence,
                'active': True,
            }
            
            # Create document type
            doc_type = request.env['nbs.document.type'].create(values)
            
            # Log
            request.env['nbs.audit.log'].create({
                'action': 'document_type_created',
                'user_id': user_id,
                'details': f'Created document type: {name} ({code})'
            })
            
            return {
                'success': True,
                'message': 'تم إنشاء نوع المستند بنجاح',
                'data': {
                    'id': doc_type.id,
                    'name': doc_type.name,
                    'code': doc_type.code
                }
            }
        
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f'Create document type error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/document-types/<int:doc_type_id>/update', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def update_document_type(self, doc_type_id, name=None, code=None, description=None, 
                            department_id=None, sequence=None, active=None, **kwargs):
        """Update document type"""
        try:
            user_id = ensure_jwt_user_id()
            if not user_id:
                return {'success': False, 'error': 'Unauthorized'}

            # Check if user is admin or manager
            if not (request.env.user.has_group('nbs_archive.group_nbs_admin') or 
                    request.env.user.has_group('nbs_archive.group_nbs_manager')):
                return {'success': False, 'error': 'Manager or Admin permission required'}

            doc_type = request.env['nbs.document.type'].browse(doc_type_id)
            
            if not doc_type.exists():
                return {'success': False, 'error': 'Document type not found'}

            # Prepare updates
            updates = {}
            
            if name is not None:
                updates['name'] = name
            
            if code is not None:
                # Check if new code already exists
                existing = request.env['nbs.document.type'].search([
                    ('code', '=', code),
                    ('id', '!=', doc_type_id)
                ], limit=1)
                if existing:
                    return {'success': False, 'error': f'Document type with code "{code}" already exists'}
                updates['code'] = code
            
            if description is not None:
                updates['description'] = description
            
            if department_id is not None:
                updates['department_id'] = department_id
            
            if sequence is not None:
                updates['sequence'] = sequence
            
            if active is not None:
                updates['active'] = active
            
            if updates:
                doc_type.write(updates)
                
                # Log
                request.env['nbs.audit.log'].create({
                    'action': 'document_type_updated',
                    'user_id': user_id,
                    'details': f'Updated document type: {doc_type.name}'
                })
            
            return {
                'success': True,
                'message': 'تم تحديث نوع المستند بنجاح',
                'data': {
                    'id': doc_type.id,
                    'name': doc_type.name,
                    'code': doc_type.code
                }
            }
        
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f'Update document type error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/document-types/<int:doc_type_id>', type='http', auth='none', methods=['DELETE'], csrf=False, cors='*')
    def delete_document_type(self, doc_type_id, **kwargs):
        """Delete document type (archive)"""
        try:
            user_id = ensure_jwt_user_id()
            if not user_id:
                return request.make_json_response({'success': False, 'error': 'Unauthorized'})

            # Check if user is admin or manager
            if not (request.env.user.has_group('nbs_archive.group_nbs_admin') or 
                    request.env.user.has_group('nbs_archive.group_nbs_manager')):
                return request.make_json_response({'success': False, 'error': 'Manager or Admin permission required'})

            doc_type = request.env['nbs.document.type'].browse(doc_type_id)
            
            if not doc_type.exists():
                return request.make_json_response({'success': False, 'error': 'Document type not found'})

            # Check if document type has documents
            if doc_type.document_count > 0:
                return request.make_json_response({
                    'success': False,
                    'error': f'Cannot delete document type with {doc_type.document_count} documents. Archive it instead.'
                })

            # Archive (set inactive)
            doc_type.write({'active': False})
            
            # Log
            request.env['nbs.audit.log'].create({
                'action': 'document_type_archived',
                'user_id': user_id,
                'details': f'Archived document type: {doc_type.name}'
            })
            
            return request.make_json_response({
                'success': True,
                'message': 'تم أرشفة نوع المستند بنجاح'
            })
        
        except Exception as e:
            _logger.error(f'Delete document type error: {str(e)}', exc_info=True)
            return request.make_json_response({'success': False, 'error': str(e)})
