# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class BatchOperationsController(http.Controller):
    
    @http.route('/api/documents/batch/archive', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def batch_archive(self, document_ids, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            
            if not request.env.user.has_group('nbs_archive.group_nbs_manager'):
                return {'success': False, 'error': 'Manager permission required'}
            
            documents = request.env['nbs.document'].browse(document_ids)
            success = 0
            errors = []
            
            for doc in documents:
                try:
                    doc.write({'state': 'archived'})
                    success += 1
                except Exception as e:
                    errors.append(f"Doc {doc.id}: {str(e)}")
            
            return {
                'success': True,
                'message': f'Archived {success}/{len(document_ids)} documents',
                'data': {'successful': success, 'failed': len(errors), 'errors': errors}
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/documents/batch/unarchive', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def batch_unarchive(self, document_ids, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            if not request.env.user.has_group('nbs_archive.group_nbs_manager'):
                return {'success': False, 'error': 'Manager permission required'}

            documents = request.env['nbs.document'].browse(document_ids)
            success = 0
            errors = []

            for doc in documents:
                try:
                    if doc.state != 'archived':
                        errors.append(f"Doc {doc.id}: not in archived state (current: {doc.state})")
                        continue
                    doc.write({'state': 'active'})
                    success += 1
                except Exception as e:
                    errors.append(f"Doc {doc.id}: {str(e)}")

            return {
                'success': True,
                'message': f'Unarchived {success}/{len(document_ids)} documents',
                'data': {'successful': success, 'failed': len(errors), 'errors': errors}
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/api/documents/batch/trash', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def batch_trash(self, document_ids, reason=None, **kwargs):
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            
            documents = request.env['nbs.document'].browse(document_ids)
            success = 0
            errors = []
            
            for doc in documents:
                try:
                    doc.soft_delete(reason=reason)
                    success += 1
                except Exception as e:
                    errors.append(f"Doc {doc.id}: {str(e)}")
            
            return {
                'success': True,
                'message': f'Moved {success}/{len(document_ids)} documents to trash',
                'data': {'successful': success, 'failed': len(errors), 'errors': errors}
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/documents/batch/move-folder', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def batch_move_folder(self, document_ids, target_folder_id, source_folder_id=None, **kwargs):
        """Move documents to a target folder (removes from source, adds to target)
        
        Args:
            document_ids: List of document IDs to move
            target_folder_id: Target folder ID
            source_folder_id: Optional source folder ID (for validation)
        
        IMPORTANT: When moving secondary/sub documents:
        - They should NOT replace the target folder's main document
        - They should be added as secondary documents in the target folder
        - Their parent_document_id should be updated to the target folder's main document
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}
            
            _logger.info(f'[MOVE REQUEST] document_ids={document_ids}, source={source_folder_id}, target={target_folder_id}')
            
            documents = request.env['nbs.document'].browse(document_ids)
            target_folder = request.env['nbs.document.folder'].browse(target_folder_id)
            
            if not target_folder.exists():
                return {'success': False, 'error': 'Target folder not found'}
            
            # Find the main document in the target folder
            # Check BOTH folder_id AND Many2many relationship
            target_main_doc = request.env['nbs.document'].search([
                ('folder_role', '=', 'main'),
                ('is_deleted', '=', False),
                '|',
                ('folder_id', '=', target_folder_id),
                ('folder_ids', 'in', [target_folder_id])
            ], limit=1)
            
            if not target_main_doc:
                _logger.warning(f'[MOVE] Target folder {target_folder_id} has no main document')
                # Check if any documents in target folder (via both methods)
                any_docs_via_folder_id = request.env['nbs.document'].search_count([
                    ('folder_id', '=', target_folder_id),
                    ('is_deleted', '=', False)
                ])
                any_docs_via_m2m = len(target_folder.document_ids.filtered(lambda d: not d.is_deleted))
                any_docs_in_target = any_docs_via_folder_id + any_docs_via_m2m
                
                if any_docs_in_target == 0:
                    _logger.info(f'[MOVE] Target folder {target_folder_id} is empty')
                else:
                    _logger.warning(f'[MOVE] Target folder has {any_docs_in_target} documents but no main!')
            
            moved_count = 0
            errors = []
            
            for doc in documents:
                if not doc.exists():
                    errors.append(f'Document {doc.id} not found')
                    continue
                
                try:
                    old_folder_id = doc.folder_id.id if doc.folder_id else None
                    old_folder_ids_list = doc.folder_ids.ids if doc.folder_ids else []
                    is_secondary_doc = bool(doc.parent_document_id) or doc.folder_role in ('sub', 'attachment')
                    
                    _logger.info(f'[MOVE] Doc {doc.id} "{doc.name}": old_folder_id={old_folder_id}, old_folder_ids={old_folder_ids_list}, target={target_folder_id}, is_secondary={is_secondary_doc}')
                    
                    # Check if already in target
                    if old_folder_id == target_folder_id and target_folder_id in old_folder_ids_list:
                        _logger.warning(f'[MOVE] Doc {doc.id} already in target folder {target_folder_id}')
                        errors.append(f'Document {doc.id} already in target folder')
                        continue
                    
                    # Build folder_ids commands: remove from ALL current folders, add ONLY to target
                    folder_commands = []
                    
                    # Remove from all current folders in Many2many
                    for fid in old_folder_ids_list:
                        folder_commands.append((3, fid))  # unlink
                        _logger.info(f'[MOVE] Unlinking doc {doc.id} from folder {fid}')
                    
                    # Add to target folder
                    folder_commands.append((4, target_folder_id))  # link
                    _logger.info(f'[MOVE] Linking doc {doc.id} to folder {target_folder_id}')
                    
                    # Prepare update values
                    vals = {
                        'folder_ids': folder_commands  # Update Many2many (remove all old, add target)
                    }
                    
                    # Handle based on document type
                    if is_secondary_doc:
                        # This is a secondary/sub document
                        # Update folder_id to target folder (for consistency)
                        # Update parent_document_id to target folder's main document
                        _logger.info(f'[MOVE] Doc {doc.id} is secondary - updating folder_id and parent')
                        
                        vals['folder_id'] = target_folder_id  # Move to target folder
                        
                        if target_main_doc:
                            vals['parent_document_id'] = target_main_doc.id
                            _logger.info(f'[MOVE] Set parent_document_id to {target_main_doc.id}')
                        else:
                            # No main document in target
                            # Check if folder truly has NO documents (check both folder_id and Many2many)
                            any_docs_via_folder_id = request.env['nbs.document'].search_count([
                                ('folder_id', '=', target_folder_id),
                                ('is_deleted', '=', False)
                            ])
                            any_docs_via_m2m = len(target_folder.document_ids.filtered(lambda d: not d.is_deleted))
                            total_docs = any_docs_via_folder_id + any_docs_via_m2m
                            
                            if total_docs == 0:
                                # Target folder is truly empty - this becomes main document
                                _logger.info(f'[MOVE] Target folder is truly empty (0 docs) - promoting doc {doc.id} to main')
                                vals['folder_role'] = 'main'
                                vals['parent_document_id'] = False
                            else:
                                # Target has docs but no main - DO NOT promote, keep as sub
                                _logger.warning(f'[MOVE] Target folder has {total_docs} docs but no main - keeping doc {doc.id} as sub with no parent')
                                vals['parent_document_id'] = False
                                # Force keep as sub
                                vals['folder_role'] = 'sub'
                        
                        # Ensure folder_role is explicitly set to sub if not promoting to main
                        if 'folder_role' not in vals:
                            vals['folder_role'] = 'sub'
                    else:
                        # This is a main document - update folder_id (Many2one)
                        _logger.info(f'[MOVE] Doc {doc.id} is main document - updating folder_id')
                        
                        # Check if target folder already has a main document
                        if target_main_doc:
                            # Target already has main - incoming doc becomes secondary
                            _logger.warning(f'[MOVE] Target folder already has main doc {target_main_doc.id} - converting doc {doc.id} to secondary')
                            vals['folder_id'] = target_folder_id
                            vals['folder_role'] = 'sub'
                            vals['parent_document_id'] = target_main_doc.id
                        else:
                            # No main in target - this becomes the main
                            vals['folder_id'] = target_folder_id
                            vals['folder_role'] = 'main'
                    
                    doc.write(vals)
                    
                    # Verify after write - refresh from DB
                    doc.invalidate_recordset(['folder_id', 'folder_ids', 'parent_document_id'])
                    doc_after = request.env['nbs.document'].browse(doc.id)
                    _logger.info(f'[MOVE] ✓ After: Doc {doc.id} folder_id={doc_after.folder_id.id if doc_after.folder_id else None}, folder_ids={doc_after.folder_ids.ids}, parent={doc_after.parent_document_id.id if doc_after.parent_document_id else None}')
                    
                    moved_count += 1
                    
                except Exception as e:
                    error_msg = f'Doc {doc.id}: {str(e)}'
                    errors.append(error_msg)
                    _logger.error(f'[MOVE] Error moving doc {doc.id}: {e}', exc_info=True)
            
            return {
                'success': True,
                'message': f'Moved {moved_count}/{len(document_ids)} documents',
                'data': {
                    'moved': moved_count,
                    'failed': len(errors),
                    'errors': errors
                }
            }
        except Exception as e:
            _logger.error(f'Batch move folder error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    # ── Trash list ───────────────────────────────────────────────────────────
    @http.route('/api/documents/trash/list', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def list_trash(self, department_id=None, document_type_id=None, search=None,
                   from_date=None, to_date=None, page=1, per_page=20, **kwargs):
        """
        List trashed documents with pagination and optional filters.
        Identical to POST /api/documents/trash.
        """
        try:
            if not ensure_jwt_user_id():
                return {
                    'success': False, 'error': 'Unauthorized',
                    'data': [], 'pagination': {'total': 0, 'page': 1, 'per_page': 20, 'total_pages': 0}
                }

            domain = [('state', '=', 'trash'), ('is_deleted', '=', True)]
            if department_id:
                domain.append(('department_id', '=', department_id))
            if document_type_id:
                domain.append(('document_type_id', '=', document_type_id))
            if search:
                domain.append(('name', 'ilike', search))
            if from_date:
                domain.append(('deleted_at', '>=', from_date))
            if to_date:
                domain.append(('deleted_at', '<=', to_date))

            per_page = int(per_page)
            page     = int(page)
            Document  = request.env['nbs.document']
            docs      = Document.search(domain, limit=per_page, offset=(page - 1) * per_page, order='deleted_at desc')
            total     = Document.search_count(domain)

            result = []
            for doc in docs:
                result.append({
                    'id':                  doc.id,
                    'name':                doc.name,
                    'title':               doc.name,
                    'document_number':     getattr(doc, 'document_number', None) or doc.barcode,
                    'department_id':       doc.department_id.id,
                    'department_name':     doc.department_id.name,
                    'document_type_id':    doc.document_type_id.id   if doc.document_type_id else None,
                    'document_type_name':  doc.document_type_id.name if doc.document_type_id else None,
                    'uploader_id':         doc.uploader_id.id   if doc.uploader_id else None,
                    'uploader_name':       doc.uploader_id.name if doc.uploader_id else None,
                    'upload_date':         doc.upload_date.isoformat()      if doc.upload_date      else None,
                    'deleted_at':          doc.deleted_at.isoformat()       if doc.deleted_at       else None,
                    'deleted_by':          doc.deleted_by.name              if doc.deleted_by       else None,
                    'deletion_reason':     doc.deletion_reason,
                    'restore_deadline':    doc.restore_deadline.isoformat() if doc.restore_deadline else None,
                    'state_before_trash':  doc.state_before_trash,
                    'status':              doc.state,
                    'confidentiality_level': doc.confidentiality_level,
                    'barcode':             doc.barcode,
                    'file_name':           doc.current_version_id.file_name if doc.current_version_id else None,
                    'file_size':           doc.current_version_id.file_size if doc.current_version_id else 0,
                    'is_main_document':    (doc.folder_role == 'main'),
                    'document_role':       doc.folder_role or 'other',
                })

            return {
                'success': True,
                'data':    result,
                'count':   len(result),
                'pagination': {
                    'total':       total,
                    'page':        page,
                    'per_page':    per_page,
                    'total_pages': (total + per_page - 1) // per_page if per_page else 1,
                },
            }
        except Exception as e:
            _logger.error('list_trash error: %s', e, exc_info=True)
            return {
                'success': False, 'error': str(e),
                'data': [], 'pagination': {'total': 0, 'page': 1, 'per_page': 20, 'total_pages': 0}
            }
