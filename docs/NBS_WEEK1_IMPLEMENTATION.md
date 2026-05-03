# 🚀 Week 1 - Quick Implementation Guide

## الهدف
تنفيذ الميزات الحرجة في أول أسبوع (18 ساعة عمل)

---

## ✅ Task 1: Edit Attachment API (2 hours)

### File: `addons/nbs_archive/controllers/attachments_controller.py`

```python
@http.route('/api/documents/<int:document_id>/attachments/<int:attachment_id>', 
            type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
def update_attachment(self, document_id, attachment_id, name=None, description=None, 
                     file_data=None, file_name=None, **kwargs):
    """Update attachment"""
    try:
        if not ensure_jwt_user_id():
            return {'success': False, 'error': 'Unauthorized'}

        attachment = request.env['nbs.document.attachment'].browse(attachment_id)
        
        if not attachment.exists() or attachment.document_id.id != document_id:
            return {'success': False, 'error': 'Attachment not found'}

        # Check permission
        if not attachment.document_id.check_access_rights('write', raise_exception=False):
            return {'success': False, 'error': 'No permission to edit'}

        updates = {}
        
        if name:
            updates['name'] = name
        
        if description is not None:
            updates['description'] = description
        
        # If new file is uploaded
        if file_data and file_name:
            if 'base64,' in file_data:
                file_data = file_data.split('base64,', 1)[1]
            
            size = len(base64.b64decode(file_data))
            updates.update({
                'file_data': file_data,
                'file_name': file_name,
                'file_size': size,
            })
        
        if updates:
            attachment.write(updates)
            
            # Log activity
            request.env['nbs.audit.log'].create({
                'action': 'attachment_updated',
                'document_id': document_id,
                'user_id': request.env.user.id,
                'details': f'Updated attachment: {attachment.name}'
            })
        
        return {
            'success': True,
            'message': 'تم تحديث المرفق بنجاح',
            'data': {
                'id': attachment.id,
                'name': attachment.name,
                'file_name': attachment.file_name,
                'file_size': attachment.file_size
            }
        }
    except Exception as e:
        _logger.error(f'Update attachment error: {str(e)}', exc_info=True)
        return {'success': False, 'error': str(e)}
```

---

## ✅ Task 2: Delete Attachment API (2 hours)

### Add to Models: `addons/nbs_archive/models/nbs_document.py`

```python
# Find nbs.document.attachment model and add:

class NBSDocumentAttachment(models.Model):
    _name = 'nbs.document.attachment'
    
    # Add new fields
    is_deleted = fields.Boolean('Deleted', default=False, index=True)
    deleted_at = fields.Datetime('Deleted At')
    deleted_by = fields.Many2one('res.users', 'Deleted By')
    deletion_reason = fields.Text('Deletion Reason')
    
    def soft_delete(self, reason=None):
        """Soft delete attachment"""
        self.write({
            'is_deleted': True,
            'deleted_at': fields.Datetime.now(),
            'deleted_by': self.env.user.id,
            'deletion_reason': reason
        })
        
        # Log
        self.env['nbs.audit.log'].create({
            'action': 'attachment_deleted',
            'document_id': self.document_id.id,
            'user_id': self.env.user.id,
            'details': f'Deleted attachment: {self.name}'
        })
    
    def restore(self):
        """Restore attachment"""
        self.write({
            'is_deleted': False,
            'deleted_at': False,
            'deleted_by': False,
            'deletion_reason': False
        })
```

### Add to Controller:

```python
@http.route('/api/documents/<int:document_id>/attachments/<int:attachment_id>', 
            type='http', auth='none', methods=['DELETE'], csrf=False, cors='*')
def delete_attachment(self, document_id, attachment_id, **kwargs):
    """Soft delete attachment"""
    try:
        if not ensure_jwt_user_id():
            return request.make_json_response({'success': False, 'error': 'Unauthorized'})

        attachment = request.env['nbs.document.attachment'].browse(attachment_id)
        
        if not attachment.exists() or attachment.document_id.id != document_id:
            return request.make_json_response({'success': False, 'error': 'Not found'})

        # Soft delete
        attachment.soft_delete()
        
        return request.make_json_response({
            'success': True,
            'message': 'تم حذف المرفق بنجاح'
        })
    except Exception as e:
        _logger.error(f'Delete attachment error: {str(e)}', exc_info=True)
        return request.make_json_response({'success': False, 'error': str(e)})

@http.route('/api/documents/<int:document_id>/attachments/<int:attachment_id>/restore', 
            type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
def restore_attachment(self, document_id, attachment_id, **kwargs):
    """Restore attachment from trash"""
    try:
        if not ensure_jwt_user_id():
            return {'success': False, 'error': 'Unauthorized'}

        attachment = request.env['nbs.document.attachment'].browse(attachment_id)
        
        if not attachment.exists():
            return {'success': False, 'error': 'Not found'}

        attachment.restore()
        
        return {'success': True, 'message': 'تم استعادة المرفق بنجاح'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

---

## ✅ Task 3: Soft Delete Document (4 hours)

### Update Model: `addons/nbs_archive/models/nbs_document.py`

```python
class NBSDocument(models.Model):
    _name = 'nbs.document'
    
    # Update state selection
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('trash', 'In Trash'),  # NEW
    ], string='Status', default='draft', required=True, tracking=True, index=True)
    
    # Add trash fields
    is_deleted = fields.Boolean('In Trash', default=False, index=True)
    deleted_at = fields.Datetime('Deleted At')
    deleted_by = fields.Many2one('res.users', 'Deleted By')
    deletion_reason = fields.Text('Deletion Reason')
    restore_deadline = fields.Datetime('Restore Deadline')
    
    @api.depends('deleted_at', 'restore_deadline')
    def _compute_days_until_deletion(self):
        """Calculate days remaining before permanent deletion"""
        for rec in self:
            if rec.restore_deadline:
                delta = rec.restore_deadline - fields.Datetime.now()
                rec.days_until_deletion = delta.days if delta.days > 0 else 0
            else:
                rec.days_until_deletion = 0
    
    days_until_deletion = fields.Integer('Days Until Deletion', 
                                         compute='_compute_days_until_deletion')
    
    def soft_delete(self, reason=None):
        """Move document to trash"""
        from datetime import timedelta
        
        self.write({
            'state': 'trash',
            'is_deleted': True,
            'deleted_at': fields.Datetime.now(),
            'deleted_by': self.env.user.id,
            'deletion_reason': reason,
            'restore_deadline': fields.Datetime.now() + timedelta(days=30)
        })
        
        # Log
        self.env['nbs.audit.log'].create({
            'action': 'document_soft_deleted',
            'document_id': self.id,
            'user_id': self.env.user.id,
            'details': f'Moved to trash: {self.name}. Reason: {reason or "N/A"}'
        })
        
        # Notify managers
        self._notify_document_deleted()
    
    def restore_from_trash(self):
        """Restore document from trash"""
        old_state = self.state_before_trash or 'active'
        
        self.write({
            'state': old_state,
            'is_deleted': False,
            'deleted_at': False,
            'deleted_by': False,
            'deletion_reason': False,
            'restore_deadline': False
        })
        
        # Log
        self.env['nbs.audit.log'].create({
            'action': 'document_restored',
            'document_id': self.id,
            'user_id': self.env.user.id,
            'details': f'Restored from trash: {self.name}'
        })
    
    def permanent_delete(self, confirmation):
        """Permanently delete document"""
        if confirmation != 'DELETE_PERMANENT':
            raise ValidationError('Invalid confirmation')
        
        # Log before delete
        self.env['nbs.audit.log'].create({
            'action': 'document_permanently_deleted',
            'document_id': self.id,
            'user_id': self.env.user.id,
            'details': f'Permanently deleted: {self.name}'
        })
        
        # Delete
        self.unlink()
```

### Add Controller: `addons/nbs_archive/controllers/trash_controller.py`

```python
# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request

from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class NBSTrashController(http.Controller):
    """Trash management controller"""
    
    @http.route('/api/documents/<int:document_id>', 
                type='http', auth='none', methods=['DELETE'], csrf=False, cors='*')
    def delete_document(self, document_id, reason=None, **kwargs):
        """Soft delete document"""
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'})

            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return request.make_json_response({'success': False, 'error': 'Not found'})

            # Check permission
            if not document.check_access_rights('write', raise_exception=False):
                return request.make_json_response({'success': False, 'error': 'No permission'})

            # Soft delete
            document.soft_delete(reason=reason)
            
            return request.make_json_response({
                'success': True,
                'message': 'تم نقل المستند إلى سلة المحذوفات',
                'restore_deadline': document.restore_deadline.strftime('%Y-%m-%d') if document.restore_deadline else None
            })
        except Exception as e:
            _logger.error(f'Delete document error: {str(e)}', exc_info=True)
            return request.make_json_response({'success': False, 'error': str(e)})
    
    @http.route('/api/documents/<int:document_id>/restore', 
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def restore_document(self, document_id, **kwargs):
        """Restore document from trash"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists() or not document.is_deleted:
                return {'success': False, 'error': 'Not found in trash'}

            document.restore_from_trash()
            
            return {'success': True, 'message': 'تم استعادة المستند بنجاح'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/trash/documents', 
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_trash(self, page=1, per_page=20, **kwargs):
        """Get documents in trash"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized', 'data': []}

            Document = request.env['nbs.document']
            domain = [('is_deleted', '=', True), ('state', '=', 'trash')]
            
            documents = Document.search(domain, limit=per_page, 
                                       offset=(page-1)*per_page, 
                                       order='deleted_at desc')
            total = Document.search_count(domain)
            
            return {
                'success': True,
                'data': [{
                    'id': doc.id,
                    'name': doc.name,
                    'deleted_at': doc.deleted_at.isoformat() if doc.deleted_at else None,
                    'deleted_by': doc.deleted_by.name if doc.deleted_by else None,
                    'deletion_reason': doc.deletion_reason,
                    'restore_deadline': doc.restore_deadline.strftime('%Y-%m-%d') if doc.restore_deadline else None,
                    'days_remaining': doc.days_until_deletion
                } for doc in documents],
                'pagination': {
                    'total': total,
                    'page': page,
                    'per_page': per_page
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'data': []}
    
    @http.route('/api/documents/<int:document_id>/permanent', 
                type='http', auth='none', methods=['DELETE'], csrf=False, cors='*')
    def permanent_delete(self, document_id, confirmation=None, **kwargs):
        """Permanently delete document"""
        try:
            if not ensure_jwt_user_id():
                return request.make_json_response({'success': False, 'error': 'Unauthorized'})

            if confirmation != 'DELETE_PERMANENT':
                return request.make_json_response({'success': False, 'error': 'Invalid confirmation'})

            document = request.env['nbs.document'].browse(document_id)
            
            if not document.exists():
                return request.make_json_response({'success': False, 'error': 'Not found'})

            # Check if admin
            if not request.env.user.has_group('nbs_archive.group_nbs_admin'):
                return request.make_json_response({'success': False, 'error': 'Admin only'})

            document.permanent_delete(confirmation)
            
            return request.make_json_response({
                'success': True,
                'message': 'تم حذف المستند نهائياً'
            })
        except Exception as e:
            return request.make_json_response({'success': False, 'error': str(e)})
```

### Register controller: `addons/nbs_archive/controllers/__init__.py`

```python
from . import trash_controller  # ADD THIS LINE
```

---

## ✅ Task 4: Bulk Upload (8 hours)

### Create new model: `addons/nbs_archive/models/nbs_bulk_upload.py`

```python
# -*- coding: utf-8 -*-

import uuid
from odoo import models, fields, api


class NBSBulkUploadJob(models.Model):
    _name = 'nbs.bulk.upload.job'
    _description = 'Bulk Upload Job'
    _order = 'create_date desc'
    
    job_id = fields.Char('Job ID', required=True, index=True, default=lambda self: str(uuid.uuid4()))
    user_id = fields.Many2one('res.users', 'User', required=True, default=lambda self: self.env.user)
    
    # Counts
    total_files = fields.Integer('Total Files', default=0)
    processed_files = fields.Integer('Processed Files', default=0)
    succeeded_files = fields.Integer('Succeeded Files', default=0)
    failed_files = fields.Integer('Failed Files', default=0)
    
    # Status
    status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending', required=True)
    
    # Results
    created_document_ids = fields.Many2many('nbs.document', string='Created Documents')
    error_log = fields.Text('Error Log')
    progress_details = fields.Text('Progress Details')
    
    # Folder
    folder_id = fields.Many2one('nbs.document.folder', 'Target Folder')
    
    def process_upload(self, files_data):
        """Process bulk upload"""
        self.write({'status': 'processing', 'total_files': len(files_data)})
        
        succeeded = []
        failed = []
        errors = []
        
        for idx, file_data in enumerate(files_data):
            try:
                # Create document
                doc = self.env['nbs.document'].create({
                    'name': file_data.get('name'),
                    'department_id': file_data.get('department_id'),
                    'document_type_id': file_data.get('document_type_id'),
                    'confidentiality_level': file_data.get('confidentiality_level', 'internal'),
                })
                
                # Create version with file
                version = self.env['nbs.document.version'].create({
                    'document_id': doc.id,
                    'file_data': file_data.get('file_data'),
                    'file_name': file_data.get('file_name'),
                    'version_number': 1,
                })
                
                doc.current_version_id = version.id
                
                # Add to folder if specified
                if self.folder_id:
                    doc.folder_ids = [(4, self.folder_id.id)]
                
                succeeded.append(doc.id)
                
            except Exception as e:
                failed.append({
                    'file': file_data.get('name'),
                    'error': str(e)
                })
                errors.append(f"File {idx+1}: {str(e)}")
            
            # Update progress
            self.write({
                'processed_files': idx + 1,
                'succeeded_files': len(succeeded),
                'failed_files': len(failed)
            })
        
        # Complete
        self.write({
            'status': 'completed' if not failed else 'failed',
            'created_document_ids': [(6, 0, succeeded)],
            'error_log': '\n'.join(errors) if errors else False
        })
        
        return {
            'succeeded': len(succeeded),
            'failed': len(failed),
            'documents': succeeded,
            'errors': failed
        }
```

### Register model: `addons/nbs_archive/models/__init__.py`

```python
from . import nbs_bulk_upload  # ADD THIS LINE
```

### Add to `__manifest__.py`:

```python
'data': [
    # ...
    'security/ir.model.access.csv',  # ADD access rights for nbs.bulk.upload.job
    # ...
],
```

### Create controller: `addons/nbs_archive/controllers/bulk_upload_controller.py`

```python
# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request

from ._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)


class NBSBulkUploadController(http.Controller):
    """Bulk upload controller"""
    
    @http.route('/api/documents/bulk-upload', 
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def bulk_upload(self, files, folder_id=None, auto_ocr=False, **kwargs):
        """Bulk upload documents"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            if not files or not isinstance(files, list):
                return {'success': False, 'error': 'files array is required'}

            # Create job
            job = request.env['nbs.bulk.upload.job'].create({
                'folder_id': folder_id if folder_id else False,
            })
            
            # Process upload
            result = job.process_upload(files)
            
            return {
                'success': True,
                'data': {
                    'job_id': job.job_id,
                    'total': len(files),
                    'succeeded': result['succeeded'],
                    'failed': result['failed'],
                    'documents': [{'id': doc_id} for doc_id in result['documents']],
                    'errors': result['errors']
                }
            }
        except Exception as e:
            _logger.error(f'Bulk upload error: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/documents/bulk-upload/<string:job_id>/progress', 
                type='jsonrpc', auth='none', methods=['POST'], csrf=False, cors='*')
    def get_upload_progress(self, job_id, **kwargs):
        """Get upload progress"""
        try:
            if not ensure_jwt_user_id():
                return {'success': False, 'error': 'Unauthorized'}

            job = request.env['nbs.bulk.upload.job'].search([('job_id', '=', job_id)], limit=1)
            
            if not job:
                return {'success': False, 'error': 'Job not found'}

            progress = 0
            if job.total_files > 0:
                progress = int((job.processed_files / job.total_files) * 100)

            return {
                'success': True,
                'data': {
                    'job_id': job.job_id,
                    'status': job.status,
                    'total': job.total_files,
                    'processed': job.processed_files,
                    'succeeded': job.succeeded_files,
                    'failed': job.failed_files,
                    'progress_percentage': progress
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
```

### Register controller: `addons/nbs_archive/controllers/__init__.py`

```python
from . import bulk_upload_controller  # ADD THIS LINE
```

---

## 🧪 Testing

### Test Edit Attachment:

```bash
curl -X POST http://localhost:8070/api/documents/1/attachments/5 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "name": "Updated Name",
        "description": "Updated description"
    }
  }'
```

### Test Delete Attachment:

```bash
curl -X DELETE http://localhost:8070/api/documents/1/attachments/5 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Soft Delete Document:

```bash
curl -X DELETE http://localhost:8070/api/documents/123 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "reason=Test deletion"
```

### Test Bulk Upload:

```bash
curl -X POST http://localhost:8070/api/documents/bulk-upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "files": [
            {
                "name": "Document 1",
                "file_data": "base64...",
                "file_name": "doc1.pdf",
                "department_id": 1,
                "document_type_id": 2
            }
        ]
    }
  }'
```

---

## 📝 Checklist

```
□ Edit Attachment API implemented
□ Delete Attachment API implemented
□ Soft Delete Document implemented
□ Restore from Trash implemented
□ Bulk Upload implemented
□ Bulk Upload Progress tracking
□ All APIs tested
□ Error handling added
□ Audit logging added
□ Documentation updated
□ Code committed to git
```

---

## 🚀 Deployment

```bash
# 1. Update module
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_local \
  -u nbs_archive --stop-after-init

# 2. Restart Odoo
pkill -f odoo-bin && ./start_local.sh

# 3. Test APIs
# Use Postman or curl

# 4. Commit changes
git add .
git commit -m "feat: Add edit/delete attachments, soft delete, bulk upload"
git push origin feature/nbs-archive-enhancements
```

---

**Status:** Ready to implement ✅  
**Estimated Time:** 18 hours  
**Priority:** P0 (Critical)
