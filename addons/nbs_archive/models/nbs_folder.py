# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class NBSDocumentFolder(models.Model):
    _name = 'nbs.document.folder'
    _description = 'Document Folder Hierarchy'
    _order = 'sequence, name'
    _parent_store = True
    _parent_name = 'parent_id'
    
    name = fields.Char(
        string='Folder Name',
        required=True,
        index=True,
        translate=False  # table has varchar; set False to avoid ->> on varchar
    )
    
    code = fields.Char(
        string='Folder Code',
        index=True,
        copy=False
    )
    
    description = fields.Text(
        string='Description',
        translate=False  # table has text; set False to avoid jsonb operator on varchar
    )
    
    # Hierarchy (DB may have parent_folder_id; model uses parent_id - add column if missing)
    parent_id = fields.Many2one(
        'nbs.document.folder',
        string='Parent Folder',
        ondelete='restrict',
        index=True
    )
    
    parent_path = fields.Char(
        index=True
    )
    
    child_ids = fields.One2many(
        'nbs.document.folder',
        'parent_id',
        string='Subfolders'
    )
    
    # Computed fields
    level = fields.Integer(
        string='Hierarchy Level',
        compute='_compute_level',
        store=True
    )
    
    full_path = fields.Char(
        string='Full Path',
        compute='_compute_full_path',
        store=True
    )
    
    child_count = fields.Integer(
        string='Subfolders Count',
        compute='_compute_child_count',
        store=True
    )
    
    document_count = fields.Integer(
        string='Documents Count',
        compute='_compute_document_count'
    )
    
    all_document_count = fields.Integer(
        string='All Documents (Including Subfolders)',
        compute='_compute_all_document_count'
    )
    
    # Relations
    department_id = fields.Many2one(
        'nbs.department',
        string='Department',
        required=True,
        index=True
    )
    
    # Company/Brand for folder grouping
    company_id = fields.Many2one(
        'res.partner',
        string='Company/Brand',
        domain="[('is_company', '=', True)]",
        index=True,
        help='Company or brand this folder belongs to. Allows filtering folders by company.'
    )
    
    document_ids = fields.Many2many(
        'nbs.document',
        'folder_document_rel',  # Same table as in nbs_document
        'folder_id',
        'document_id',
        string='Documents'
    )
    
    # Access control
    restricted = fields.Boolean(
        string='Restricted Access',
        default=False,
        help='If checked, only specific users can access this folder'
    )
    
    allowed_user_ids = fields.Many2many(
        'res.users',
        'folder_user_access_rel',
        'folder_id',
        'user_id',
        string='Allowed Users'
    )
    
    allowed_group_ids = fields.Many2many(
        'res.groups',
        'folder_group_access_rel',
        'folder_id',
        'group_id',
        string='Allowed Groups'
    )
    
    # Metadata
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    color = fields.Integer(
        string='Color Index',
        default=0
    )
    
    icon = fields.Char(
        string='Icon',
        default='fa-folder'
    )
    
    created_by = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True
    )
    
    # Notes
    note_ids = fields.One2many(
        'nbs.note',
        'folder_id',
        string='Notes',
        help='User notes attached to this folder'
    )
    
    note_count = fields.Integer(
        string='Notes Count',
        compute='_compute_note_count',
        store=False
    )
    
    user_note = fields.Text(
        string='User Note',
        help='Quick note field for user annotations (deprecated - use nbs.note instead)'
    )
    
    last_modified = fields.Datetime(
        string='Last Modified',
        compute='_compute_last_modified',
        store=False,
        help='Last modification time of folder or its contents'
    )
    # Table nbs_document_folder has owner_id NOT NULL; set on create for compatibility
    owner_id = fields.Many2one(
        'res.users',
        string='Owner',
        default=lambda self: self.env.user,
        required=True
    )

    create_date = fields.Datetime(
        string='Created Date',
        readonly=True
    )
    
    write_uid = fields.Many2one(
        'res.users',
        string='Last Updated By',
        readonly=True
    )
    
    write_date = fields.Datetime(
        string='Last Updated',
        readonly=True
    )
    
    @api.depends('parent_id')
    def _compute_level(self):
        for folder in self:
            level = 0
            current = folder.parent_id
            while current:
                level += 1
                current = current.parent_id
            folder.level = level
    
    @api.depends('name', 'parent_id', 'parent_id.full_path')
    def _compute_full_path(self):
        for folder in self:
            if folder.parent_id:
                folder.full_path = f"{folder.parent_id.full_path}/{folder.name}"
            else:
                folder.full_path = folder.name
    
    @api.depends('child_ids')
    def _compute_child_count(self):
        for folder in self:
            folder.child_count = len(folder.child_ids)
    
    def _compute_document_count(self):
        for folder in self:
            folder.document_count = len(folder.document_ids.filtered(lambda d: not d.is_deleted))
    
    def _compute_all_document_count(self):
        for folder in self:
            # Get all descendant folders
            all_folders = self._get_all_children(folder)
            all_folders.append(folder.id)
            
            count = self.env['nbs.document'].search_count([
                ('folder_id', 'in', all_folders),
                ('is_deleted', '=', False)
            ])
            folder.all_document_count = count
    
    @api.depends('note_ids')
    def _compute_note_count(self):
        for folder in self:
            folder.note_count = len(folder.note_ids.filtered(lambda n: n.active))
    
    def _compute_last_modified(self):
        for folder in self:
            dates = [folder.write_date] if folder.write_date else []
            
            # Include document write dates
            if folder.document_ids:
                doc_dates = folder.document_ids.filtered(lambda d: not d.is_deleted and d.write_date).mapped('write_date')
                dates.extend(doc_dates)
            
            # Include note write dates
            if folder.note_ids:
                note_dates = folder.note_ids.filtered(lambda n: n.active and n.write_date).mapped('write_date')
                dates.extend(note_dates)
            
            folder.last_modified = max(dates) if dates else folder.write_date
    
    def _get_all_children(self, folder):
        """Recursively get all child folder IDs"""
        children = []
        for child in folder.child_ids:
            children.append(child.id)
            children.extend(self._get_all_children(child))
        return children
    
    @api.constrains('parent_id')
    def _check_recursion(self):
        # Call base implementation (do not call self._check_recursion to avoid infinite recursion)
        if self._has_cycle('parent_id'):
            raise ValidationError(_('Error! You cannot create recursive folders.'))
    
    @api.constrains('name', 'parent_id', 'department_id')
    def _check_unique_name(self):
        for folder in self:
            domain = [
                ('name', '=', folder.name),
                ('parent_id', '=', folder.parent_id.id if folder.parent_id else False),
                ('department_id', '=', folder.department_id.id),
                ('id', '!=', folder.id)
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_('A folder with this name already exists in the same parent folder!'))
    
    @api.model
    def create(self, vals):
        # Ensure vals is a dict (avoid "dictionary update sequence element #0 has length 6" when list/string passed)
        if isinstance(vals, dict):
            vals = dict(vals)
        elif isinstance(vals, (list, tuple)):
            if len(vals) == 1 and isinstance(vals[0], dict):
                vals = dict(vals[0])
            else:
                try:
                    vals = dict(vals)  # list of (key, value) pairs only
                except (TypeError, ValueError) as e:
                    raise ValidationError(
                        _("Invalid folder data: send a single object with fields (e.g. name, code, department_id). %s") % e
                    )
        else:
            try:
                vals = dict(vals)
            except (TypeError, ValueError) as e:
                raise ValidationError(_("Invalid folder data: expected a dict of fields. %s") % e)
        # Table nbs_document_folder.owner_id is NOT NULL
        if not vals.get('owner_id'):
            vals['owner_id'] = getattr(self.env.user, 'id', None) or 1
        # department_id is NOT NULL; set default to first department if missing (ORM sends NULL explicitly, so DB default is not used)
        if not vals.get('department_id'):
            first = self.env['nbs.department'].search([], limit=1)
            vals['department_id'] = first.id if first else 1
        # name is NOT NULL; always set so ORM never sends NULL
        vals['name'] = (vals.get('name') or _('New Folder') or 'New Folder').strip() or 'New Folder'
        # code: table may require it; ensure non-empty
        vals['code'] = (vals.get('code') or (vals.get('name') or 'F')[:64] or 'F').strip() or 'F'
        folder = super().create(vals)
        
        # Log creation
        self.env['nbs.audit.log'].sudo().create({
            'user_id': self.env.user.id,
            'action': 'folder_created',
            'folder_id': folder.id,  # Track which folder was created
            'department_id': folder.department_id.id,
            'metadata': f'Created folder: {folder.name} (Path: {folder.full_path})'
        })
        
        return folder
    
    def write(self, vals):
        # Track old values before update
        old_values = {}
        for folder in self:
            old_values[folder.id] = {
                'name': folder.name,
                'code': folder.code,
                'description': folder.description,
                'company_id': folder.company_id.id if folder.company_id else None,
                'company_name': folder.company_id.name if folder.company_id else None,
                'parent_id': folder.parent_id.id if folder.parent_id else None,
                'restricted': folder.restricted,
            }
        
        result = super().write(vals)
        
        # Log update with details of what changed
        if vals:
            for folder in self:
                changes = []
                old = old_values.get(folder.id, {})
                
                # Check what changed
                if 'name' in vals and old.get('name') != folder.name:
                    changes.append(f"Name: '{old.get('name')}' → '{folder.name}'")
                
                if 'code' in vals and old.get('code') != folder.code:
                    changes.append(f"Code: '{old.get('code')}' → '{folder.code}'")
                
                if 'description' in vals:
                    old_desc = old.get('description') or ''
                    new_desc = folder.description or ''
                    if old_desc != new_desc:
                        changes.append(f"Description updated")
                
                if 'company_id' in vals:
                    old_company = old.get('company_name') or 'None'
                    new_company = folder.company_id.name if folder.company_id else 'None'
                    if old.get('company_id') != (folder.company_id.id if folder.company_id else None):
                        changes.append(f"Company: '{old_company}' → '{new_company}'")
                
                if 'parent_id' in vals:
                    old_parent = old.get('parent_id')
                    new_parent = folder.parent_id.id if folder.parent_id else None
                    if old_parent != new_parent:
                        changes.append(f"Moved to different parent")
                
                if 'restricted' in vals and old.get('restricted') != folder.restricted:
                    status = "Enabled" if folder.restricted else "Disabled"
                    changes.append(f"Restricted access: {status}")
                
                # Create audit log with change details
                metadata = f"Updated folder: {folder.name}"
                if changes:
                    metadata += f" | Changes: {', '.join(changes)}"
                
                self.env['nbs.audit.log'].sudo().create({
                    'user_id': self.env.user.id,
                    'action': 'folder_updated',
                    'folder_id': folder.id,  # Track which folder was updated
                    'department_id': folder.department_id.id,
                    'metadata': metadata
                })
        
        return result
    
    def unlink(self):
        for folder in self:
            # Check if has subfolders first (must delete children before parent)
            if folder.child_count > 0:
                raise ValidationError(
                    _('Cannot delete folder "%s" because it contains %d subfolders. '
                      'Please delete the subfolders first.') % (folder.name, folder.child_count)
                )
            
            # SOFT DELETE: Move all documents to trash (do NOT permanently delete)
            # Get documents via folder_id (Many2one)
            docs_via_folder_id = self.env['nbs.document'].search([
                ('folder_id', '=', folder.id)
            ])
            
            # Get documents via Many2many
            docs_via_many2many = folder.document_ids
            
            # Combine both (union to avoid duplicates)
            all_docs = docs_via_folder_id | docs_via_many2many
            
            if all_docs:
                _logger.info(f'Moving {len(all_docs)} documents in folder {folder.name} to trash')
                
                # For each document: ONLY move to trash (do NOT permanently delete)
                failed_docs = []
                for doc in all_docs:
                    try:
                        # Soft delete if not already deleted
                        if not doc.is_deleted:
                            _logger.info(f'  Processing doc {doc.id}: {doc.name}, role={doc.folder_role}')
                            # IMPORTANT: Pass skip_folder_auto_delete=True to prevent infinite recursion
                            doc.with_context(skip_folder_auto_delete=True).soft_delete(
                                reason=f'Folder deletion: {folder.name}'
                            )
                            _logger.info(f'  ✓ Moved document {doc.id} to trash')
                        else:
                            _logger.info(f'  Document {doc.id} already in trash, skipping')
                    except Exception as e:
                        _logger.error(f'Error moving document {doc.id} to trash: {str(e)}', exc_info=True)
                        failed_docs.append(doc.id)
                        # Continue with other documents
                
                if failed_docs:
                    raise ValidationError(
                        _('Failed to delete folder because some documents could not be moved to trash: %s') 
                        % str(failed_docs)
                    )
                
                # CRITICAL: Clear folder_id from all documents to allow folder deletion
                # Documents are in trash but still reference folder via FK constraint
                _logger.info(f'Clearing folder_id from {len(all_docs)} documents to allow folder deletion')
                for doc in all_docs:
                    try:
                        doc.sudo().write({'folder_id': False})
                        _logger.info(f'  Cleared folder_id from doc {doc.id}')
                    except Exception as e:
                        _logger.error(f'Failed to clear folder_id from doc {doc.id}: {str(e)}')
            
            # Log folder deletion
            try:
                self.env['nbs.audit.log'].sudo().create({
                    'user_id': self.env.user.id,
                    'action': 'folder_deleted',
                    'folder_id': folder.id,  # Track which folder was deleted
                    'department_id': folder.department_id.id,
                    'metadata': f'Deleted folder: {folder.name} with {len(all_docs)} documents'
                })
            except Exception:
                pass
        
        return super().unlink()
    
    def action_view_documents(self):
        """Open documents in this folder"""
        self.ensure_one()
        return {
            'name': _('Documents in %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'nbs.document',
            'view_mode': 'tree,form',
            'domain': [('folder_id', '=', self.id), ('is_deleted', '=', False)],
            'context': {'default_folder_id': self.id}
        }
    
    def action_view_all_documents(self):
        """Open all documents including subfolders"""
        self.ensure_one()
        all_folders = self._get_all_children(self)
        all_folders.append(self.id)
        
        return {
            'name': _('All Documents in %s (Including Subfolders)') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'nbs.document',
            'view_mode': 'tree,form',
            'domain': [('folder_id', 'in', all_folders), ('is_deleted', '=', False)],
        }
    
    def check_access(self, user_id=None):
        """Check if user has access to this folder"""
        if not self or len(self) != 1:
            return False

        if not self.restricted:
            return True
        
        user = self.env['res.users'].browse(user_id) if user_id else self.env.user
        
        # Check if user is admin
        if user.has_group('nbs_archive.group_nbs_admin'):
            return True
        
        # Check if user is in allowed users
        if user in self.allowed_user_ids:
            return True
        
        # Check if user's groups intersect with allowed groups
        if set(user.groups_id.ids) & set(self.allowed_group_ids.ids):
            return True
        
        return False
    
    def move_to_folder(self, target_folder_id):
        """Move this folder to another parent folder"""
        self.ensure_one()
        
        if target_folder_id == self.id:
            raise ValidationError(_('Cannot move folder to itself!'))
        
        target = self.browse(target_folder_id) if target_folder_id else None
        
        if target:
            # Check for circular reference
            current = target
            while current:
                if current.id == self.id:
                    raise ValidationError(_('Cannot move folder into its own subfolder!'))
                current = current.parent_id
        
        self.write({'parent_id': target_folder_id})
        
        # Log
        self.env['nbs.audit.log'].sudo().create({
            'user_id': self.env.user.id,
            'action': 'folder_moved',
            'department_id': self.department_id.id,
            'metadata': f'Moved folder {self.name} to {target.name if target else "root"}'
        })
