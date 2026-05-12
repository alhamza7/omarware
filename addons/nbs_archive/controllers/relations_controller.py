# -*- coding: utf-8 -*-

import logging
import base64
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

from ._auth import ensure_jwt_user_id


class NBSRelationsController(http.Controller):
    """Document relations, attachments, and folders controller"""
    
    @http.route('/api/documents/<int:document_id>/relations', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_relations(self, document_id, **kwargs):
        """Get all relations for a document"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return {
                    'success': False,
                    'error': 'Document not found'
                }
            
            relations = request.env['nbs.document.relation'].search([
                '|',
                ('document_id', '=', document_id),
                ('related_document_id', '=', document_id)
            ])
            
            return {
                'success': True,
                'data': [{
                    'id': rel.id,
                    'document_id': rel.document_id.id,
                    'document_title': rel.document_id.name,
                    'related_document_id': rel.related_document_id.id,
                    'related_document_title': rel.related_document_id.name,
                    'relation_type': rel.relation_type,
                    'notes': rel.notes,
                } for rel in relations]
            }
        
        except Exception as e:
            _logger.error(f'Get relations error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/documents/<int:document_id>/add-relation', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def add_relation(self, document_id, related_document_id, relation_type='related', notes=None, **kwargs):
        """Add relation between two documents"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            if document_id == related_document_id:
                return {
                    'success': False,
                    'error': 'لا يمكن ربط المستند بنفسه'
                }
            
            # Check if both documents exist
            doc1 = request.env['nbs.document'].browse(document_id)
            doc2 = request.env['nbs.document'].browse(related_document_id)
            
            if not (doc1.exists() and doc2.exists()):
                return {
                    'success': False,
                    'error': 'أحد المستندات غير موجود'
                }
            
            # Create relation
            relation = request.env['nbs.document.relation'].create({
                'document_id': document_id,
                'related_document_id': related_document_id,
                'relation_type': relation_type,
                'notes': notes,
            })
            
            # Log
            request.env['nbs.audit.log'].create({
                'user_id': request.env.user.id,
                'action': 'relation_created',
                'document_id': document_id,
                'department_id': doc1.department_id.id,
                'metadata': f'Related to: {doc2.name}',
            })
            
            return {
                'success': True,
                'data': {
                    'id': relation.id,
                    'message': 'تم إنشاء العلاقة بنجاح'
                }
            }
        
        except Exception as e:
            _logger.error(f'Add relation error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    # NOTE:
    # Attachments endpoints are implemented in `attachments_controller.py`:
    #   POST /api/documents/<document_id>/attachments          (type='jsonrpc')
    #   POST /api/documents/<document_id>/add-attachment       (type='jsonrpc')
    #   GET  /api/documents/<document_id>/attachments/<id>/download (type='http')
    
    @http.route('/api/folders', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_folders(self, department_id=None, folder_type=None, state='active',
                    company_id=None, from_date=None, to_date=None, **kwargs):
        """Get list of folders. Supports filtering by department, company/brand, state, and date range."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': []}

            domain = [('active', '=', (state == 'active'))]
            if department_id:
                domain.append(('department_id', '=', department_id))
            if company_id:
                domain.append(('company_id', '=', company_id))
            if folder_type:
                domain.append(('folder_type', '=', folder_type))
            # Date range filter on create_date
            if from_date:
                domain.append(('create_date', '>=', from_date))
            if to_date:
                domain.append(('create_date', '<=', to_date))

            folders = request.env['nbs.document.folder'].search(domain, order='create_date desc')

            return {
                'success': True,
                'data': [{
                    'id': folder.id,
                    'name': folder.name,
                    'code': folder.code,
                    'folder_type': getattr(folder, 'folder_type', None),
                    'department_id': folder.department_id.id,
                    'department_name': folder.department_id.name,
                    'company_id': folder.company_id.id if folder.company_id else None,
                    'company_name': folder.company_id.name if folder.company_id else None,
                    'description': folder.description,
                    'document_count': folder.document_count,
                    'owner_name': folder.created_by.name if folder.created_by else None,
                    'create_date': folder.create_date.isoformat() if folder.create_date else None,
                    'last_modified': folder.last_modified.isoformat() if folder.last_modified else None,
                    'state': 'active' if folder.active else 'archived',
                } for folder in folders]
            }
        
        except Exception as e:
            _logger.error(f'Get folders error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/folders/<int:folder_id>/documents', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_folder_documents(self, folder_id, from_date=None, to_date=None, **kwargs):
        """Get all documents in a folder"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            folder = request.env['nbs.document.folder'].browse(folder_id)
            
            if not folder.exists():
                return {
                    'success': False,
                    'error': 'Folder not found'
                }
            
            # Get documents via folder_id (Many2one) and folder_ids (Many2many), excluding deleted
            docs_via_folder_id = request.env['nbs.document'].search([
                ('folder_id', '=', folder_id),
                ('is_deleted', '=', False)
            ])
            docs_via_many2many = folder.document_ids.filtered(lambda d: not d.is_deleted)
            all_doc_ids = list(set(docs_via_folder_id.ids + docs_via_many2many.ids))

            # Apply date filters via ORM for proper type handling
            doc_domain = [('id', 'in', all_doc_ids)]
            if from_date:
                doc_domain.append(('upload_date', '>=', from_date))
            if to_date:
                doc_domain.append(('upload_date', '<=', to_date))
            all_docs = request.env['nbs.document'].search(doc_domain)

            # Calculate updated_at
            updated_at = None
            if all_docs:
                write_dates = [doc.write_date for doc in all_docs if doc.write_date]
                if write_dates:
                    updated_at = max(write_dates).isoformat()

            return {
                'success': True,
                'folder': {
                    'id':              folder.id,
                    'name':            folder.name,
                    'code':            folder.code,
                    'description':     folder.description,
                    'folder_type':     folder.icon if folder.icon else None,
                    'icon':            folder.icon,
                    'color':           folder.color,
                    'sequence':        folder.sequence,
                    'restricted':      folder.restricted,
                    'department_id':   folder.department_id.id if folder.department_id else None,
                    'department_name': folder.department_id.name if folder.department_id else None,
                    'company_id':      folder.company_id.id if folder.company_id else None,
                    'company_name':    folder.company_id.name if folder.company_id else None,
                    'parent_id':       folder.parent_id.id if folder.parent_id else None,
                    'parent_name':     folder.parent_id.name if folder.parent_id else None,
                    'full_path':       folder.full_path,
                    'level':           folder.level,
                    'child_count':     folder.child_count,
                    'document_count':  len(all_docs),
                    'note_count':      folder.note_count,
                    'user_note':       folder.user_note,
                    'owner_name':      folder.owner_id.name if folder.owner_id else None,
                    'created_by':      folder.created_by.name if folder.created_by else None,
                    'state':           'active' if folder.active else 'inactive',
                    'create_date':     folder.create_date.isoformat() if folder.create_date else None,
                    'last_modified':   folder.last_modified.isoformat() if folder.last_modified else None,
                    'updated_at':      updated_at,
                },
                'data': [{
                    'id': doc.id,
                    'title': doc.name,
                    'barcode': doc.barcode,
                    'document_type_name': doc.document_type_id.name,
                    'upload_date': doc.upload_date.isoformat() if doc.upload_date else None,
                    'document_date': doc.document_date.strftime('%d-%m-%Y') if doc.document_date else None,
                    'status': doc.state,
                    'parent_document_id': doc.parent_document_id.id if doc.parent_document_id else None,
                    'parent_title': doc.parent_document_id.name if doc.parent_document_id else None,
                    'relation_type': 'attachment' if doc.parent_document_id and getattr(doc, 'is_attachment', False) else ('secondary_document' if doc.parent_document_id else None),
                    'folder_role': getattr(doc, 'folder_role', None),
                    'is_attachment': getattr(doc, 'is_attachment', False),
                } for doc in all_docs]
            }
        
        except Exception as e:
            _logger.error(f'Get folder documents error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/folders/create', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def create_folder(self, name, code, department_id, folder_type='other', description=None, document_ids=None, company_id=None, **kwargs):
        """Create new folder. Accepts named args or a single dict as first arg (params: [{"name":"...", "code":"...", "department_id": 1, "company_id": 1}])."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            if isinstance(name, dict):
                payload = name
                vals = {
                    'name': payload.get('name') or 'New Folder',
                    'code': payload.get('code') or payload.get('name') or 'F',
                    'department_id': payload.get('department_id'),
                    'company_id': payload.get('company_id') or False,
                    'description': payload.get('description'),
                    'active': True,
                    'owner_id': request.env.user.id,
                }
                document_ids = payload.get('document_ids') or document_ids
            else:
                vals = {
                    'name': name,
                    'code': code or name,
                    'department_id': department_id,
                    'company_id': company_id if company_id else False,
                    'description': description,
                    'active': True,
                    'owner_id': request.env.user.id,
                }
            if document_ids:
                vals['document_ids'] = [(6, 0, document_ids)] if isinstance(document_ids, list) else [(6, 0, [document_ids])]
            folder = request.env['nbs.document.folder'].create(vals)
            
            return {
                'success': True,
                'data': {
                    'id': folder.id,
                    'name': folder.name,
                    'message': 'تم إنشاء الإضبارة بنجاح'
                }
            }
        
        except Exception as e:
            _logger.error(f'Create folder error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/folders/<int:folder_id>/add-document', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def add_document_to_folder(self, folder_id, document_id, **kwargs):
        """Add document to folder"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            folder = request.env['nbs.document.folder'].browse(folder_id)
            
            if not folder.exists():
                return {
                    'success': False,
                    'error': 'Folder not found'
                }
            
            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return {
                    'success': False,
                    'error': 'Document not found'
                }
            
            # Add document to folder
            folder.write({
                'document_ids': [(4, document_id)]
            })
            
            return {
                'success': True,
                'message': 'تم إضافة المستند للإضبارة بنجاح'
            }
        
        except Exception as e:
            _logger.error(f'Add document to folder error: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }


