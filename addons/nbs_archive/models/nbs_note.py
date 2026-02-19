# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class NBSNote(models.Model):
    _name = 'nbs.note'
    _description = 'User Notes for Documents and Folders'
    _order = 'write_date desc, create_date desc'
    _rec_name = 'title'
    
    title = fields.Char(
        string='Title',
        index=True,
        help='Optional title for the note'
    )
    
    content = fields.Text(
        string='Note Content',
        required=True,
        help='Note text content'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        index=True,
        ondelete='cascade',
        help='User who created this note'
    )
    
    document_id = fields.Many2one(
        'nbs.document',
        string='Related Document',
        index=True,
        ondelete='cascade',
        help='Document this note is attached to (optional)'
    )
    
    folder_id = fields.Many2one(
        'nbs.document.folder',
        string='Related Folder',
        index=True,
        ondelete='cascade',
        help='Folder this note is attached to (optional)'
    )
    
    department_id = fields.Many2one(
        'nbs.department',
        string='Department',
        index=True,
        ondelete='restrict',
        help='Department context for the note'
    )
    
    image = fields.Binary(
        string='Attached Image',
        attachment=True,
        help='Optional image attachment for the note'
    )
    
    image_filename = fields.Char(
        string='Image Filename',
        help='Name of the attached image file'
    )
    
    is_private = fields.Boolean(
        string='Private Note',
        default=True,
        help='If true, only the creator can see this note'
    )
    
    is_pinned = fields.Boolean(
        string='Pinned',
        default=False,
        help='Pin this note to the top'
    )
    
    color = fields.Integer(
        string='Color',
        default=0,
        help='Color code for UI display'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        index=True
    )
    
    @api.constrains('document_id', 'folder_id')
    def _check_attachment(self):
        """Ensure note is attached to at least something or standalone"""
        for note in self:
            # Notes can be standalone (no document or folder)
            # or attached to document, folder, or both
            pass
    
    @api.model
    def create(self, vals_list):
        """Create note with automatic department assignment"""
        _logger.info(f'[NBSNote.create] Received vals_list type: {type(vals_list)}')
        
        # Handle both single dict and list of dicts (Odoo 17 compatibility)
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        
        _logger.info(f'[NBSNote.create] After normalization, vals_list type: {type(vals_list)}, length: {len(vals_list)}')
        
        for vals in vals_list:
            _logger.info(f'[NBSNote.create] Processing vals type: {type(vals)}')
            # Auto-assign department from document or folder if not provided
            if not vals.get('department_id'):
                if vals.get('document_id'):
                    doc = self.env['nbs.document'].browse(vals['document_id'])
                    if doc.exists() and doc.department_id:
                        vals['department_id'] = doc.department_id.id
                elif vals.get('folder_id'):
                    folder = self.env['nbs.document.folder'].browse(vals['folder_id'])
                    if folder.exists() and folder.department_id:
                        vals['department_id'] = folder.department_id.id
        
        return super().create(vals_list)
    
    def name_get(self):
        """Custom display name"""
        result = []
        for note in self:
            name = note.title or (note.content[:50] + '...' if len(note.content) > 50 else note.content)
            result.append((note.id, name))
        return result
    
    def can_user_access(self):
        """Check if current user can access this note"""
        self.ensure_one()
        
        # Creator always has access
        if self.user_id.id == self.env.user.id:
            return True
        
        # If not private, check department access
        if not self.is_private:
            # Admin has access to all
            if self.env.user.has_group('nbs_archive.group_nbs_admin'):
                return True
            
            # Manager has access within their departments
            if self.env.user.has_group('nbs_archive.group_nbs_manager'):
                if self.department_id and self.department_id in self.env.user.department_ids:
                    return True
        
        return False
