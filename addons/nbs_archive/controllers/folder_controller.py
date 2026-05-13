# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request
from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class NBSFolderController(http.Controller):
    """Folder hierarchy management controller"""
    
    @http.route('/api/folders', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def list_folders(self, department_id=None, parent_id=None, company_id=None, **kwargs):
        """List folders with optional filters: department, parent, company/brand"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            domain = [('active', '=', True)]
            
            if department_id:
                domain.append(('department_id', '=', department_id))
            
            if company_id:
                domain.append(('company_id', '=', company_id))
            
            if parent_id is not None:
                if parent_id == 0 or parent_id == False:
                    domain.append(('parent_id', '=', False))
                else:
                    domain.append(('parent_id', '=', parent_id))
            
            folder_ids = request.env['nbs.document.folder'].search(
                domain, order='sequence, name'
            ).ids
            result = []
            for fid in folder_ids:
                try:
                    folder = request.env['nbs.document.folder'].browse(fid)
                    if not folder.check_access():
                        continue
                    doc_count = 0
                    all_doc_count = 0
                    try:
                        doc_count = folder.document_count
                        all_doc_count = folder.all_document_count
                    except Exception:
                        pass
                    result.append({
                        'id': folder.id,
                        'name': folder.name,
                        'code': folder.code,
                        'description': folder.description,
                        'parent_id': folder.parent_id.id if folder.parent_id else None,
                        'parent_name': folder.parent_id.name if folder.parent_id else None,
                        'level': folder.level,
                        'full_path': folder.full_path,
                        'child_count': folder.child_count,
                        'document_count': doc_count,
                        'all_document_count': all_doc_count,
                        'department_id': folder.department_id.id,
                        'department_name': folder.department_id.name,
                        'company_id': folder.company_id.id if folder.company_id else None,
                        'company_name': folder.company_id.name if folder.company_id else None,
                        'restricted': folder.restricted,
                        'color': folder.color,
                        'icon': folder.icon,
                        'sequence': folder.sequence,
                        'created_at': folder.create_date.isoformat() if folder.create_date else None,
                        'last_modified': folder.last_modified.isoformat() if folder.last_modified else None,
                    })
                except Exception as e:
                    _logger.warning('Skip folder %s: %s', fid, e)
                    continue
            
            return {'success': True, 'data': result, 'count': len(result)}
        except ValueError as e:
            if 'singleton' in str(e).lower() or 'Expected singleton' in str(e):
                _logger.warning('List folders singleton workaround: %s', e)
                return {'success': True, 'data': [], 'count': 0}
            raise
        except Exception as e:
            _logger.error(f'List folders error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/folders/<int:folder_id>', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_folder(self, folder_id, **kwargs):
        """Get folder details"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            folder = request.env['nbs.document.folder'].browse(folder_id)
            
            if not folder.exists():
                return {'success': False, 'error': 'Folder not found'}
            
            if not folder.check_access():
                return {'success': False, 'error': 'Access denied'}
            
            return {
                'success': True,
                'data': {
                    'id': folder.id,
                    'name': folder.name,
                    'code': folder.code,
                    'description': folder.description,
                    'parent_id': folder.parent_id.id if folder.parent_id else None,
                    'parent_name': folder.parent_id.name if folder.parent_id else None,
                    'parent_path': folder.parent_path,
                    'full_path': folder.full_path,
                    'level': folder.level,
                    'child_count': folder.child_count,
                    'document_count': folder.document_count,
                    'all_document_count': folder.all_document_count,
                    'note_count': folder.note_count,
                    'department_id': folder.department_id.id,
                    'department_name': folder.department_id.name,
                    'restricted': folder.restricted,
                    'allowed_users': [{'id': u.id, 'name': u.name} for u in folder.allowed_user_ids],
                    'allowed_groups': [{'id': g.id, 'name': g.name} for g in folder.allowed_group_ids],
                    'color': folder.color,
                    'icon': folder.icon,
                    'sequence': folder.sequence,
                    'active': folder.active,
                    'user_note': folder.user_note,
                    'last_modified': folder.last_modified.isoformat() if folder.last_modified else None,
                    'created_by': folder.created_by.name if folder.created_by else None,
                    'create_date': folder.create_date.isoformat() if folder.create_date else None,
                    'write_date': folder.write_date.isoformat() if folder.write_date else None
                }
            }
        except Exception as e:
            _logger.error(f'Get folder error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/folders/create', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def create_folder(self, name, department_id, parent_id=None, company_id=None, code=None, description=None,
                     restricted=False, color=0, icon='fa-folder', sequence=10, **kwargs):
        """Create new folder with optional company/brand. Accepts either named args or a single dict as first arg."""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            # Check permission
            if not request.env.user.has_group('nbs_archive.group_nbs_manager'):
                return {'success': False, 'error': 'Only managers can create folders'}

            # If first arg is a dict (client sent single object), use it as payload
            if isinstance(name, dict):
                payload = name
                vals = {
                    'name': payload.get('name') or 'New Folder',
                    'department_id': payload.get('department_id'),
                    'parent_id': payload.get('parent_id') or False,
                    'company_id': payload.get('company_id') or False,
                    'code': payload.get('code'),
                    'description': payload.get('description'),
                    'restricted': payload.get('restricted', False),
                    'color': payload.get('color', 0),
                    'icon': payload.get('icon', 'fa-folder'),
                    'sequence': payload.get('sequence', 10),
                    'owner_id': request.env.user.id,
                }
            else:
                vals = {
                    'name': name,
                    'department_id': department_id,
                    'parent_id': parent_id if parent_id else False,
                    'company_id': company_id if company_id else False,
                    'code': code,
                    'description': description,
                    'restricted': restricted,
                    'color': color,
                    'icon': icon,
                    'sequence': sequence,
                    'owner_id': request.env.user.id,
                }
            folder = request.env['nbs.document.folder'].create(vals)
            
            return {
                'success': True,
                'message': 'Folder created successfully',
                'data': {'id': folder.id, 'name': folder.name, 'full_path': folder.full_path}
            }
        except Exception as e:
            _logger.error(f'Create folder error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/folders/<int:folder_id>/update', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def update_folder(self, folder_id, **kwargs):
        """Update folder"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            folder = request.env['nbs.document.folder'].browse(folder_id)
            
            if not folder.exists():
                return {'success': False, 'error': 'Folder not found'}
            
            if not request.env.user.has_group('nbs_archive.group_nbs_manager'):
                return {'success': False, 'error': 'Only managers can update folders'}
            
            updates = {}
            for key in ['name', 'code', 'description', 'restricted', 'color', 'icon', 'sequence', 'parent_id', 'user_note', 'company_id']:
                if key in kwargs:
                    updates[key] = kwargs[key]
            
            if updates:
                folder.write(updates)
            
            return {'success': True, 'message': 'Folder updated successfully'}
        except Exception as e:
            _logger.error(f'Update folder error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/folders/<int:folder_id>', type='http', auth='none', methods=['DELETE'], csrf=False, cors='*')
    def delete_folder(self, folder_id, **kwargs):
        """Delete folder"""
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'}, status=401)

            folder = request.env['nbs.document.folder'].browse(folder_id)
            
            if not folder.exists():
                return request.make_json_response({'success': False, 'error': 'Folder not found'}, status=404)
            
            if not request.env.user.has_group('nbs_archive.group_nbs_admin'):
                return request.make_json_response({'success': False, 'error': 'Admin permission required'}, status=403)
            
            _logger.info(f'[DELETE FOLDER] Starting deletion of folder {folder_id}: {folder.name}')
            
            try:
                folder.unlink()
                _logger.info(f'[DELETE FOLDER] Successfully deleted folder {folder_id}')
            except Exception as unlink_error:
                _logger.error(f'[DELETE FOLDER] Unlink failed for folder {folder_id}: {str(unlink_error)}', exc_info=True)
                return request.make_json_response({
                    'success': False, 
                    'error': f'Failed to delete folder: {str(unlink_error)}'
                }, status=500)
            
            return request.make_json_response({'success': True, 'message': 'Folder deleted successfully'})
            
        except Exception as e:
            _logger.error(f'Delete folder error for folder {folder_id}: {str(e)}', exc_info=True)
            return request.make_json_response({
                'success': False, 
                'error': f'Server error: {str(e)}'
            }, status=500)
    
    @http.route('/api/folders/<int:folder_id>/move', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def move_folder(self, folder_id, target_parent_id=None, **kwargs):
        """Move folder to another parent"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            folder = request.env['nbs.document.folder'].browse(folder_id)
            
            if not folder.exists():
                return {'success': False, 'error': 'Folder not found'}
            
            if not request.env.user.has_group('nbs_archive.group_nbs_manager'):
                return {'success': False, 'error': 'Manager permission required'}
            
            folder.move_to_folder(target_parent_id)
            
            return {'success': True, 'message': 'Folder moved successfully'}
        except Exception as e:
            _logger.error(f'Move folder error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/folders/batch-delete', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def batch_delete_folders(self, folder_ids, force=False, **kwargs):
        """
        Delete multiple folders in one request, permanently deleting all
        documents inside each folder as well.

        Params:
          folder_ids  list[int]  required  IDs of folders to delete
          force       bool       optional  If true, delete folders that have
                                           subfolders by recursively deleting
                                           children first (default: false —
                                           raises an error if subfolders exist).

        Response:
          {
            "success": true,
            "deleted": [192, 191, ...],
            "deleted_count": 20,
            "skipped": [{"id": 5, "reason": "..."}],
            "errors":  [{"id": 9, "error": "..."}]
          }
        """
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            if not isinstance(folder_ids, list) or not folder_ids:
                return {'success': False, 'error': 'folder_ids must be a non-empty list'}

            Folder = request.env['nbs.document.folder'].sudo()
            deleted = []
            skipped = []
            errors  = []

            def _delete_folder_recursive(folder):
                """Delete subfolders depth-first, then delete this folder."""
                # Recurse into children first
                children = Folder.search([('parent_id', '=', folder.id), ('active', '=', True)])
                for child in children:
                    _delete_folder_recursive(child)
                # Now delete this folder (cascade-deletes its documents)
                folder.unlink()

            for fid in folder_ids:
                try:
                    folder = Folder.browse(int(fid))
                    if not folder.exists():
                        skipped.append({'id': fid, 'reason': 'not found'})
                        continue

                    folder_name = folder.name
                    if force and folder.child_count > 0:
                        # Recursively delete children first, then this folder
                        _delete_folder_recursive(folder)
                    else:
                        # folder.unlink() raises ValidationError if subfolders exist
                        folder.unlink()

                    deleted.append(fid)
                    _logger.info('batch_delete_folders: deleted folder %s (%s)', fid, folder_name)

                except Exception as exc:
                    _logger.error('batch_delete_folders: error on folder %s: %s', fid, exc)
                    errors.append({'id': fid, 'error': str(exc)})

            return {
                'success':       True,
                'deleted':       deleted,
                'deleted_count': len(deleted),
                'skipped':       skipped,
                'errors':        errors,
            }

        except Exception as e:
            _logger.error('batch_delete_folders error: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/api/folders/tree', type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_folder_tree(self, department_id=None, **kwargs):
        """Get folder tree structure"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            domain = [('active', '=', True), ('parent_id', '=', False)]
            if department_id:
                domain.append(('department_id', '=', department_id))
            
            root_ids = request.env['nbs.document.folder'].search(
                domain, order='sequence, name'
            ).ids

            def build_tree(folder_id):
                folder = request.env['nbs.document.folder'].browse(folder_id)
                if not folder.exists() or not folder.check_access():
                    return None
                try:
                    doc_count = folder.document_count
                    all_doc_count = folder.all_document_count
                except Exception:
                    doc_count = 0
                    all_doc_count = 0
                child_ids = folder.child_ids.ids if folder.child_ids else []
                children = [build_tree(cid) for cid in child_ids]
                children = [c for c in children if c]
                return {
                    'id': folder.id,
                    'name': folder.name,
                    'code': folder.code,
                    'level': folder.level,
                    'document_count': doc_count,
                    'all_document_count': all_doc_count,
                    'icon': folder.icon,
                    'color': folder.color,
                    'children': children,
                }

            tree = [build_tree(fid) for fid in root_ids]
            tree = [t for t in tree if t]
            
            return {'success': True, 'data': tree}
        except ValueError as e:
            if 'singleton' in str(e).lower() or 'Expected singleton' in str(e):
                _logger.warning('Folder tree singleton workaround: %s', e)
                return {'success': True, 'data': []}
            raise
        except Exception as e:
            _logger.error(f'Get folder tree error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
