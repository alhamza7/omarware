# -*- coding: utf-8 -*-

import json
import base64
import os
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class NBSDocumentVersion(models.Model):
    _name = 'nbs.document.version'
    _description = 'Document Version'
    _order = 'version_number desc'
    _rec_name = 'display_name'
    
    document_id = fields.Many2one(
        'nbs.document',
        string='Document',
        required=True,
        ondelete='restrict',
        index=True
    )
    version_number = fields.Integer(
        string='Version',
        required=True,
        readonly=True,
        index=True
    )
    display_name = fields.Char(
        string='Version',
        compute='_compute_display_name',
        store=True
    )
    
    # File storage
    file_data = fields.Binary(
        string='File',
        attachment=True,
        required=True
    )
    file_name = fields.Char(
        string='Filename',
        required=True
    )
    file_size = fields.Integer(
        string='File Size (bytes)',
        readonly=True
    )
    file_type = fields.Char(
        string='MIME Type',
        readonly=True
    )
    file_path = fields.Char(
        string='Server Path',
        readonly=True,
        help='Physical file path on server'
    )
    
    # Extracted text (for search)
    extracted_text = fields.Text(
        string='Extracted Text',
        readonly=True,
        help='Full text extracted from document'
    )
    extracted_text_per_page = fields.Text(
        string='Per-Page Text',
        readonly=True,
        help='JSON array of text per page: [{"page": 1, "text": "..."}, ...]'
    )
    
    # OCR
    ocr_completed = fields.Boolean(
        string='OCR Completed',
        default=False,
        readonly=True
    )
    ocr_language = fields.Char(
        string='OCR Languages',
        default='ara+eng',
        readonly=True
    )
    ocr_date = fields.Datetime(
        string='OCR Date',
        readonly=True
    )
    
    # Metadata
    uploader_id = fields.Many2one(
        'res.users',
        string='Uploaded By',
        default=lambda self: self.env.user,
        readonly=True,
        required=True
    )
    upload_date = fields.Datetime(
        string='Upload Date',
        default=fields.Datetime.now,
        readonly=True,
        required=True
    )
    notes = fields.Text(
        string='Version Notes',
        help='Notes about changes in this version'
    )
    
    # Related fields for easy access
    department_id = fields.Many2one(
        related='document_id.department_id',
        string='Department',
        store=True,
        index=True
    )
    document_name = fields.Char(
        related='document_id.name',
        string='Document Name',
        store=True
    )
    
    _sql_constraints = [
        ('version_document_unique', 
         'UNIQUE(document_id, version_number)',
         'Version number must be unique per document!'),
        ('no_delete_protection',
         'CHECK(1=1)',  # Enforced in code, not DB
         'Versions cannot be deleted!'),
    ]
    
    @api.depends('document_id', 'version_number')
    def _compute_display_name(self):
        for version in self:
            if version.document_id and version.version_number:
                version.display_name = f'{version.document_id.name} - v{version.version_number}'
            else:
                version.display_name = 'New Version'
    
    @api.model
    def create(self, vals):
        # Auto-increment version number
        if 'document_id' in vals and not vals.get('version_number'):
            document = self.env['nbs.document'].browse(vals['document_id'])
            existing_versions = self.search([('document_id', '=', document.id)])
            vals['version_number'] = len(existing_versions) + 1
        
        # Calculate file size from binary data
        if 'file_data' in vals and vals['file_data']:
            # File data is base64 encoded string
            vals['file_size'] = len(base64.b64decode(vals['file_data']))
        
        # Determine MIME type from filename
        if 'file_name' in vals and not vals.get('file_type'):
            vals['file_type'] = self._get_mime_type(vals['file_name'])
        
        version = super().create(vals)
        
        # Organize file storage
        version._organize_file_storage()
        
        # Update document's current version
        if version.document_id:
            version.document_id.write({'current_version_id': version.id})
        
        # Log version creation
        self.env['nbs.audit.log'].sudo().create({
            'user_id': self.env.user.id,
            'action': 'new_version',
            'document_id': version.document_id.id,
            'department_id': version.document_id.department_id.id,
            'details': json.dumps({
                'version_number': version.version_number,
                'file_name': version.file_name,
                'file_size': version.file_size
            })
        })
        
        return version
    
    def unlink(self):
        """CRITICAL: Prevent hard delete of versions"""
        raise ValidationError(_('Document versions cannot be deleted! All history must be preserved.'))
    
    def _get_mime_type(self, filename):
        """Determine MIME type from file extension"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def _organize_file_storage(self):
        """Organize file in structured folder on server"""
        self.ensure_one()
        
        if not self.file_data or not self.document_id:
            return
        
        # Build path: /data/nbs-archive/{dept_code}/{doc_type_code}/{doc_id}/v{version}/
        dept_code = self.document_id.department_id.code
        doc_type_code = self.document_id.document_type_id.code
        doc_id = self.document_id.id
        version_num = self.version_number
        
        base_path = self.env['ir.config_parameter'].sudo().get_param(
            'nbs_archive.storage_path', '/var/lib/odoo/nbs_archive'
        )
        
        folder_path = os.path.join(
            base_path,
            dept_code,
            doc_type_code,
            str(doc_id),
            f'v{version_num}'
        )
        
        # Create folder if not exists
        os.makedirs(folder_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(folder_path, self.file_name)
        
        try:
            with open(file_path, 'wb') as f:
                f.write(base64.b64decode(self.file_data))
            
            self.write({'file_path': file_path})
        except Exception as e:
            print(f"Warning: Could not save file to {file_path}: {e}")
    
    def action_download(self):
        """Download this version"""
        self.ensure_one()
        
        # Log download
        self.env['nbs.audit.log'].sudo().create({
            'user_id': self.env.user.id,
            'action': 'download',
            'document_id': self.document_id.id,
            'department_id': self.document_id.department_id.id,
            'details': json.dumps({
                'version_number': self.version_number,
                'file_name': self.file_name
            })
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/nbs/documents/{self.document_id.id}/versions/{self.id}/download',
            'target': 'new',
        }
    
    def get_extracted_pages(self):
        """Return parsed per-page text"""
        self.ensure_one()
        if self.extracted_text_per_page:
            try:
                return json.loads(self.extracted_text_per_page)
            except json.JSONDecodeError:
                return []
        return []


