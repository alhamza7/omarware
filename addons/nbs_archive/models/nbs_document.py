# -*- coding: utf-8 -*-

import json
import secrets
import logging
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class NBSDocument(models.Model):
    _name = 'nbs.document'
    _description = 'NBS Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    _rec_name = 'name'
    
    # CORE FIELDS (always present)
    name = fields.Char(
        string='Title',
        required=True,
        tracking=True,
        index=True
    )
    department_id = fields.Many2one(
        'nbs.department',
        string='Department',
        required=True,
        ondelete='restrict',
        readonly=True,
        states={'draft': [('readonly', False)]},
        tracking=True,
        index=True
    )
    document_type_id = fields.Many2one(
        'nbs.document.type',
        string='Document Type',
        required=True,
        ondelete='restrict',
        readonly=True,
        states={'draft': [('readonly', False)]},
        tracking=True,
        index=True
    )
    
    # User info
    uploader_id = fields.Many2one(
        'res.users',
        string='Uploaded By',
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True,
        index=True
    )
    upload_date = fields.Datetime(
        string='Upload Date',
        default=fields.Datetime.now,
        readonly=True,
        tracking=True,
        index=True
    )
    
    # Tags
    tag_ids = fields.Many2many(
        'nbs.document.tag',
        'nbs_document_tag_rel',
        'document_id',
        'tag_id',
        string='Tags',
        tracking=True
    )
    
    # Related Numbers (searchable fields)
    po_number = fields.Char(
        string='PO Number',
        index=True,
        tracking=True
    )
    bl_number = fields.Char(
        string='BL Number',
        index=True,
        tracking=True
    )
    container_number = fields.Char(
        string='Container Number',
        index=True,
        tracking=True
    )
    invoice_number = fields.Char(
        string='Invoice Number',
        index=True,
        tracking=True
    )
    envoy_number = fields.Char(
        string='Envoy Number',
        index=True,
        tracking=True
    )
    document_date = fields.Date(
        string='Document Date',
        index=True,
        tracking=True,
        help='The official date printed on / associated with this document (dd-mm-yyyy from the frontend).'
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('trash', 'In Trash')
    ], string='Status', default='draft', required=True, tracking=True, index=True)
    
    # Soft Delete Fields
    is_deleted = fields.Boolean(
        string='In Trash',
        default=False,
        index=True,
        help='True if document is in trash'
    )
    deleted_at = fields.Datetime(string='Deleted At')
    deleted_by = fields.Many2one('res.users', string='Deleted By')
    deletion_reason = fields.Text(string='Deletion Reason')
    restore_deadline = fields.Datetime(
        string='Restore Deadline',
        help='Document will be permanently deleted after this date (30 days from deletion)'
    )
    state_before_trash = fields.Char(
        string='State Before Trash',
        help='Original state to restore to'
    )
    company_id_before_trash = fields.Many2one(
        'res.partner',
        string='Company Before Trash',
        help='Preserved company/brand value so it survives the trash → restore cycle'
    )
    
    # Folder (Week 2 - Hierarchical System)
    folder_id = fields.Many2one(
        'nbs.document.folder',
        string='Folder',
        ondelete='restrict',
        index=True,
        tracking=True,
        help='Document folder in hierarchical structure'
    )
    
    # Company/Brand (computed from folder, but can be set manually)
    company_id = fields.Many2one(
        'res.partner',
        string='Company/Brand',
        compute='_compute_company_id',
        store=True,
        readonly=False,
        index=True,
        help='Company/brand from folder. Allows filtering documents by company.'
    )
    
    # Confidentiality
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('strict', 'Strict')
    ], string='Confidentiality Level', default='internal', required=True, tracking=True, index=True)
    
    # Versioning
    current_version_id = fields.Many2one(
        'nbs.document.version',
        string='Current Version',
        readonly=True,
        ondelete='restrict'
    )
    version_ids = fields.One2many(
        'nbs.document.version',
        'document_id',
        string='Versions'
    )
    version_count = fields.Integer(
        string='Version Count',
        compute='_compute_version_count',
        store=True
    )
    
    # Relations & Attachments
    relation_ids = fields.One2many(
        'nbs.document.relation',
        'document_id',
        string='علاقات المستند'
    )
    related_document_ids = fields.Many2many(
        'nbs.document',
        'nbs_document_relation_rel',
        'document_id',
        'related_id',
        string='مستندات ذات صلة',
        compute='_compute_related_documents',
        store=False
    )
    attachment_ids = fields.One2many(
        'nbs.document.attachment',
        'document_id',
        string='المرفقات'
    )
    attachment_count = fields.Integer(
        string='عدد المرفقات',
        compute='_compute_attachment_count',
        store=True
    )
    folder_ids = fields.Many2many(
        'nbs.document.folder',
        'folder_document_rel',
        'document_id',
        'folder_id',
        string='الإضبارات'
    )
    folder_role = fields.Selection([
        ('main', 'Main Document'),
        ('sub', 'Sub Document'),
        ('attachment', 'Attachment'),
        ('other', 'Other'),
    ], string='Folder Role', default='other', index=True, tracking=True,
       help='Role of this document inside its folder(s).')
    folder_count = fields.Integer(
        string='عدد الإضبارات',
        compute='_compute_folder_count',
        store=True
    )
    
    # Parent-Child relationships (for document hierarchy)
    parent_document_id = fields.Many2one(
        'nbs.document',
        string='المستند الأصلي',
        ondelete='restrict',
        help='للمستندات الفرعية أو المرفقات'
    )
    is_attachment = fields.Boolean(
        string='Is Attachment',
        default=False,
        tracking=True,
        help='If true, this document is treated as an attachment (not a sub-document) when it has a parent.'
    )
    child_document_ids = fields.One2many(
        'nbs.document',
        'parent_document_id',
        string='المستندات الفرعية'
    )
    child_count = fields.Integer(
        string='عدد المستندات الفرعية',
        compute='_compute_child_count',
        store=True
    )
    
    # Barcode
    barcode = fields.Char(
        string='Barcode',
        readonly=True,
        index=True,
        copy=False,
        tracking=True
    )
    
    # Lock status
    is_locked = fields.Boolean(
        string='Locked',
        default=True,
        readonly=True,
        help='Document is locked after first upload. Unlock via edit request.'
    )
    unlock_token = fields.Char(
        string='Unlock Token',
        readonly=True,
        copy=False,
        help='One-time token to unlock document for version upload'
    )
    unlock_expiry = fields.Datetime(
        string='Unlock Expiry',
        readonly=True,
        help='Token expiry time (24 hours from approval)'
    )
    
    # Dynamic fields (type-specific, stored as JSON)
    custom_fields_data = fields.Text(
        string='Custom Fields Data',
        help='JSON data for type-specific fields'
    )
    
    # Edit requests
    edit_request_ids = fields.One2many(
        'nbs.edit.request',
        'document_id',
        string='Edit Requests'
    )
    pending_edit_request_count = fields.Integer(
        string='Pending Edit Requests',
        compute='_compute_pending_requests',
        store=False
    )
    
    # OCR status + extracted content
    ocr_status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], string='OCR Status', default='pending', tracking=True, index=True)

    ocr_text = fields.Text(
        string='OCR Content',
        readonly=True,
        help='Full text extracted by Google Vision OCR — used by the search engine.',
    )
    
    # Search indexing
    indexed_in_search = fields.Boolean(
        string='Indexed in Search',
        default=False,
        readonly=True
    )
    last_indexed_date = fields.Datetime(
        string='Last Indexed',
        readonly=True
    )
    
    # Notes
    note_ids = fields.One2many(
        'nbs.note',
        'document_id',
        string='Notes',
        help='User notes attached to this document'
    )
    
    note_count = fields.Integer(
        string='Notes Count',
        compute='_compute_note_count',
        store=False
    )
    
    last_modified = fields.Datetime(
        string='Last Modified',
        compute='_compute_last_modified',
        store=False,
        help='Last modification time of document or its notes'
    )
    
    # Permissions (computed)
    can_edit_tags = fields.Boolean(
        compute='_compute_permissions',
        string='Can Edit Tags'
    )
    can_request_edit = fields.Boolean(
        compute='_compute_permissions',
        string='Can Request Edit'
    )
    can_archive = fields.Boolean(
        compute='_compute_permissions',
        string='Can Archive'
    )
    can_view = fields.Boolean(
        compute='_compute_permissions',
        string='Can View'
    )
    
    _sql_constraints = [
        ('barcode_unique', 'UNIQUE(barcode)', 'Barcode must be unique!'),
        ('check_unlock_expiry', 
         "CHECK(unlock_expiry IS NULL OR unlock_expiry > upload_date)",
         'Unlock expiry must be after upload date'),
    ]
    
    @api.model
    def create(self, vals_list):
        # Handle both single dict and list of dicts (Odoo 19 compatibility)
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        
        documents = []
        for vals in vals_list:
            # Check for duplicate document name within the same department and document type
            if vals.get('name'):
                duplicate_domain = [
                    ('name', '=', vals['name']),
                    ('department_id', '=', vals.get('department_id')),
                    ('document_type_id', '=', vals.get('document_type_id')),
                    ('is_deleted', '=', False)
                ]
                if self.search_count(duplicate_domain) > 0:
                    raise ValidationError(_(
                        'A document with the name "%s" already exists in this department and document type. '
                        'Please use a different name.') % vals['name']
                    )
            
            # Generate barcode
            if not vals.get('barcode'):
                vals['barcode'] = self._generate_barcode()
            
            # Set to active and locked by default
            if 'state' not in vals:
                vals['state'] = 'active'
            if 'is_locked' not in vals:
                vals['is_locked'] = True
            
            # Explicitly set company_id from folder if not already set
            if vals.get('folder_id') and 'company_id' not in vals:
                folder = self.env['nbs.document.folder'].browse(vals['folder_id'])
                if folder.exists() and folder.company_id:
                    vals['company_id'] = folder.company_id.id
        
        docs = super().create(vals_list)
        
        # Handle both single record and recordset
        for doc in docs:
            # Log creation
            self.env['nbs.audit.log'].sudo().create({
                'user_id': self.env.user.id,
                'action': 'upload',
                'document_id': doc.id,
                'department_id': doc.department_id.id,
                'ip_address': self._get_client_ip(),
                'user_agent': self._get_user_agent(),
            })
            
            # Trigger OCR processing in background (if file is PDF or image)
            if doc.current_version_id and doc.current_version_id.file_name:
                file_name = doc.current_version_id.file_name.lower()
                if any(file_name.endswith(ext) for ext in ['.pdf', '.jpg', '.jpeg', '.png', '.tiff']):
                    try:
                        self.env['nbs.ocr.service'].sudo()._process_document_async(doc.id)
                    except Exception as e:
                        _logger.warning(f'Failed to queue OCR for document {doc.id}: {str(e)}')
            
            # Index in OpenSearch (if available)
            try:
                self.env['nbs.opensearch.service'].sudo()._index_document(doc.id)
            except Exception as e:
                _logger.warning(f'Failed to index document {doc.id} in OpenSearch: {str(e)}')
        
        return docs
    
    def write(self, vals):
        # Update company_id if folder_id changes (skip when caller handles it explicitly)
        if 'folder_id' in vals and not self._context.get('skip_company_sync'):
            if vals['folder_id']:
                folder = self.env['nbs.document.folder'].browse(vals['folder_id'])
                if folder.exists() and folder.company_id:
                    vals['company_id'] = folder.company_id.id
                else:
                    vals['company_id'] = False
            else:
                vals['company_id'] = False
        
        # Track important changes
        if 'state' in vals:
            for doc in self:
                if vals['state'] == 'archived':
                    self.env['nbs.audit.log'].sudo().create({
                        'user_id': self.env.user.id,
                        'action': 'archive',
                        'document_id': doc.id,
                        'department_id': doc.department_id.id,
                        'ip_address': self._get_client_ip(),
                    })
                elif vals['state'] == 'active' and doc.state == 'archived':
                    self.env['nbs.audit.log'].sudo().create({
                        'user_id': self.env.user.id,
                        'action': 'unarchive',
                        'document_id': doc.id,
                        'department_id': doc.department_id.id,
                        'ip_address': self._get_client_ip(),
                    })
        
        return super().write(vals)
    
    def unlink(self):
        """Override to allow permanent delete with proper authorization"""
        # Skip the trash guard when called from folder deletion cascade
        if not self.env.context.get('force_delete_from_folder'):
            for document in self:
                if document.state != 'trash' and not document.is_deleted:
                    raise ValidationError(_('Documents cannot be deleted! Move to trash first.'))

        return super(NBSDocument, self).unlink()
    
    def soft_delete(self, reason=None):
        """Move document to trash (soft delete)"""
        from datetime import timedelta
        
        for document in self:
            # Save state before trash
            state_before = document.state
            # Snapshot company so it can be recovered even if folder_id is later cleared
            company_before = document.company_id.id if document.company_id else False

            document.write({
                'state': 'trash',
                'is_deleted': True,
                'deleted_at': fields.Datetime.now(),
                'deleted_by': self.env.user.id,
                'deletion_reason': reason,
                'restore_deadline': fields.Datetime.now() + timedelta(days=30),
                'state_before_trash': state_before,
                'company_id_before_trash': company_before,
            })

            # NOTE: We intentionally do NOT auto-delete the folder when a main document is
            # trashed. If we deleted the folder here, restoring the document would leave it
            # with no folder — an unrecoverable state. Folders must be deleted explicitly by
            # the user via the folder-delete endpoint.
            
            # Log (non-blocking: do not fail operation if audit create fails)
            try:
                self.env['nbs.audit.log'].sudo().create({
                    'action': 'document_soft_deleted',
                    'document_id': document.id,
                    'user_id': self.env.user.id,
                    'department_id': document.department_id.id,
                    'metadata': f'Moved to trash: {document.name}. Reason: {reason or "N/A"}'
                })
            except Exception:
                pass  # audit failure must not flip success of trash operation
    
    def restore_from_trash(self):
        """
        Restore document(s) from trash.

        For MAIN documents (folder_role == 'main') that were trashed as part
        of a folder deletion:
          1. Recreate (or find) the original folder using the snapshot stored
             in deletion_reason.
          2. Restore the main document and re-link it to the folder.
          3. Cascade-restore ALL trashed sub/attachment documents that belong
             to this main document (identified via parent_document_id).
             All siblings are also re-linked to the restored folder.

        For sub/attachment documents restored individually, the document is
        just restored normally without cascading to siblings.
        """
        for document in self:
            if not document.is_deleted:
                raise ValidationError(_('المستند ليس في سلة المحذوفات'))

            # ── Parse folder snapshot ─────────────────────────────────────
            folder_snapshot = None
            try:
                parsed = json.loads(document.deletion_reason or '{}')
                if isinstance(parsed, dict) and parsed.get('__folder_deleted'):
                    folder_snapshot = parsed
            except Exception:
                pass

            saved_company_id = (
                document.company_id_before_trash.id
                if document.company_id_before_trash else False
            )

            # ── Folder recovery (main documents only) ────────────────────
            target_folder = None
            folder_recreated = False
            is_main = document.folder_role == 'main'

            if is_main and folder_snapshot:
                original_folder_id = folder_snapshot.get('folder_id')
                if original_folder_id:
                    existing = self.env['nbs.document.folder'].sudo().browse(original_folder_id)
                    if existing.exists():
                        target_folder = existing

                if not target_folder:
                    folder_vals = {
                        'name':          folder_snapshot.get('folder_name') or document.name,
                        'department_id': (
                            folder_snapshot.get('folder_department_id')
                            or (document.department_id.id if document.department_id else False)
                        ),
                    }
                    code = folder_snapshot.get('folder_code')
                    if code:
                        folder_vals['code'] = code
                    desc = folder_snapshot.get('folder_description')
                    if desc:
                        folder_vals['description'] = desc
                    company = folder_snapshot.get('folder_company_id') or saved_company_id
                    if company:
                        folder_vals['company_id'] = company
                    owner = folder_snapshot.get('folder_owner_id')
                    if owner:
                        folder_vals['owner_id'] = owner

                    target_folder = self.env['nbs.document.folder'].sudo().create(folder_vals)
                    folder_recreated = True
                    _logger.info(
                        'Recreated folder %s (%s) while restoring document %s',
                        target_folder.id, target_folder.name, document.id,
                    )

            elif is_main and not document.folder_id:
                # Fallback: no snapshot but main doc has no folder → create minimal folder
                target_folder = self.env['nbs.document.folder'].sudo().create({
                    'name':          document.name,
                    'department_id': document.department_id.id if document.department_id else False,
                    'company_id':    saved_company_id or False,
                })
                folder_recreated = True
                _logger.info(
                    'Created minimal folder %s for orphaned main document %s',
                    target_folder.id, document.id,
                )

            # ── Restore the document itself ───────────────────────────────
            old_state = document.state_before_trash or 'active'
            restore_vals = {
                'state':                   old_state,
                'is_deleted':              False,
                'deleted_at':              False,
                'deleted_by':              False,
                'deletion_reason':         False,
                'restore_deadline':        False,
                'state_before_trash':      False,
                'company_id_before_trash': False,
            }
            if saved_company_id:
                restore_vals['company_id'] = saved_company_id
            if target_folder:
                restore_vals['folder_id']  = target_folder.id
                restore_vals['folder_ids'] = [(4, target_folder.id)]

            document.write(restore_vals)

            # ── Cascade-restore sub/attachment documents ──────────────────
            if is_main and target_folder:
                # Primary: find siblings by restore_group UUID stored in deletion_reason.
                # Fallback: find by parent_document_id for docs that do have it set.
                restore_group = folder_snapshot.get('restore_group') if folder_snapshot else None
                siblings = self.env['nbs.document'].sudo()
                if restore_group:
                    # Use LIKE on the text field — trash sets are small, cost is negligible.
                    siblings = self.env['nbs.document'].sudo().search([
                        ('id', '!=', document.id),
                        ('is_deleted', '=', True),
                        ('deletion_reason', 'like', restore_group),
                    ])
                if not siblings:
                    # Fallback for sub/attachment docs that carry parent_document_id
                    siblings = self.env['nbs.document'].sudo().search([
                        ('parent_document_id', '=', document.id),
                        ('is_deleted', '=', True),
                    ])

                if siblings:
                    _logger.info(
                        'Cascade-restoring %d sibling document(s) for main doc %s into folder %s',
                        len(siblings), document.id, target_folder.id,
                    )
                    for child in siblings:
                        child_company = (
                            child.company_id_before_trash.id
                            if child.company_id_before_trash else saved_company_id or False
                        )
                        child_vals = {
                            'state':                   child.state_before_trash or 'active',
                            'is_deleted':              False,
                            'deleted_at':              False,
                            'deleted_by':              False,
                            'deletion_reason':         False,
                            'restore_deadline':        False,
                            'state_before_trash':      False,
                            'company_id_before_trash': False,
                            'folder_id':               target_folder.id,
                            'folder_ids':              [(4, target_folder.id)],
                        }
                        if child_company:
                            child_vals['company_id'] = child_company
                        child.sudo().write(child_vals)

            # ── Audit ─────────────────────────────────────────────────────
            try:
                meta = f'Restored from trash: {document.name}'
                if folder_recreated and target_folder:
                    meta += f' (folder recreated: {target_folder.name})'
                elif target_folder and is_main:
                    meta += f' (linked to existing folder: {target_folder.name})'
                self.env['nbs.audit.log'].sudo().create({
                    'action':        'document_restored',
                    'document_id':   document.id,
                    'user_id':       self.env.user.id,
                    'department_id': document.department_id.id,
                    'metadata':      meta,
                })
            except Exception:
                pass  # audit failure must not flip success of restore
    
    def permanent_delete(self, confirmation):
        """Permanently delete document (admin only)"""
        if confirmation != 'DELETE_PERMANENT':
            raise ValidationError(_('Invalid confirmation. Use "DELETE_PERMANENT"'))
        
        for document in self:
            # Must be in trash first
            if not document.is_deleted:
                raise ValidationError(_('Document must be in trash before permanent deletion'))
            
            # CRITICAL: Check if this document has children (is a parent)
            # If yes, clear parent_document_id from children first
            child_docs = self.env['nbs.document'].sudo().search([
                ('parent_document_id', '=', document.id)
            ])
            if child_docs:
                _logger.info(f'Document {document.id} has {len(child_docs)} children - clearing parent references')
                child_docs.sudo().write({'parent_document_id': False})
            
            # Delete all related records first to avoid FK violations
            
            # 0. Clear current_version_id reference to avoid FK constraint violation
            # (current_version_id has ondelete='restrict')
            if document.current_version_id:
                document.sudo().write({'current_version_id': False})
            
            # 1. Delete versions (with context flag to allow deletion)
            if document.version_ids:
                document.version_ids.with_context(force_delete_versions=True).sudo().unlink()
            
            # 2. Delete relations
            if document.relation_ids:
                document.relation_ids.sudo().unlink()
            
            # 3. Delete attachments
            if document.attachment_ids:
                document.attachment_ids.sudo().unlink()
            
            # 4. Audit logs: set document_id to NULL (keep logs but unlink document reference)
            # Since ondelete='set null' on audit_log.document_id, this should happen automatically
            # But we'll ensure it by updating audit logs before delete
            audit_logs = self.env['nbs.audit.log'].sudo().search([('document_id', '=', document.id)])
            if audit_logs:
                # Use SQL to bypass readonly and set document_id to NULL
                self.env.cr.execute(
                    "UPDATE nbs_audit_log SET document_id = NULL WHERE document_id = %s",
                    (document.id,)
                )
            
            # 5. Log the permanent deletion (create new audit with document_id still valid)
            try:
                self.env['nbs.audit.log'].sudo().create({
                    'action': 'document_permanently_deleted',
                    'document_id': None,  # document will be deleted, so use NULL
                    'user_id': self.env.user.id,
                    'department_id': document.department_id.id,
                    'metadata': f'Permanently deleted document ID {document.id}: {document.name}'
                })
            except Exception:
                pass
        
        # Hard delete - use sudo() on entire recordset since permission checked in controller
        return super(NBSDocument, self.sudo()).unlink()
    
    @api.depends('version_ids')
    def _compute_version_count(self):
        for doc in self:
            doc.version_count = len(doc.version_ids)
    
    @api.depends('folder_id', 'folder_id.company_id')
    def _compute_company_id(self):
        """Compute company_id from folder. Works for main and secondary documents."""
        for doc in self:
            if doc.folder_id and doc.folder_id.company_id:
                doc.company_id = doc.folder_id.company_id.id
            else:
                doc.company_id = False
    
    @api.depends('note_ids')
    def _compute_note_count(self):
        for doc in self:
            doc.note_count = len(doc.note_ids.filtered(lambda n: n.active))
    
    def _compute_last_modified(self):
        for doc in self:
            dates = [doc.write_date] if doc.write_date else []
            
            # Include version write dates
            if doc.version_ids:
                version_dates = doc.version_ids.filtered(lambda v: v.write_date).mapped('write_date')
                dates.extend(version_dates)
            
            # Include note write dates
            if doc.note_ids:
                note_dates = doc.note_ids.filtered(lambda n: n.active and n.write_date).mapped('write_date')
                dates.extend(note_dates)
            
            doc.last_modified = max(dates) if dates else doc.write_date
    
    @api.depends('relation_ids', 'relation_ids.related_document_id')
    def _compute_related_documents(self):
        for doc in self:
            related_ids = doc.relation_ids.mapped('related_document_id')
            # Also get documents that reference this document
            reverse_relations = self.env['nbs.document.relation'].search([
                ('related_document_id', '=', doc.id)
            ])
            related_ids += reverse_relations.mapped('document_id')
            doc.related_document_ids = related_ids
    
    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for doc in self:
            doc.attachment_count = len(doc.attachment_ids)
    
    @api.depends('folder_ids')
    def _compute_folder_count(self):
        for doc in self:
            doc.folder_count = len(doc.folder_ids)
    
    @api.depends('child_document_ids')
    def _compute_child_count(self):
        for doc in self:
            doc.child_count = len(doc.child_document_ids)
    
    @api.depends('edit_request_ids', 'edit_request_ids.state')
    def _compute_pending_requests(self):
        for doc in self:
            doc.pending_edit_request_count = len(
                doc.edit_request_ids.filtered(lambda r: r.state == 'pending')
            )
    
    @api.depends_context('uid')
    def _compute_permissions(self):
        for doc in self:
            user = self.env.user
            is_manager = user in doc.department_id.manager_ids
            is_admin = user.has_group('nbs_archive.group_nbs_admin')
            is_uploader = user == doc.uploader_id
            
            # Can edit tags: Manager or Admin
            doc.can_edit_tags = is_manager or is_admin
            
            # Can request edit: Any department user
            doc.can_request_edit = (
                user in doc.department_id.user_ids and 
                doc.state == 'active' and 
                doc.is_locked
            )
            
            # Can archive: Manager or Admin
            doc.can_archive = (is_manager or is_admin) and doc.state == 'active'
            
            # Can view: Based on confidentiality level
            if is_admin:
                doc.can_view = True
            elif doc.confidentiality_level == 'strict':
                doc.can_view = is_admin
            elif doc.confidentiality_level == 'confidential':
                doc.can_view = is_manager or is_admin
            elif doc.confidentiality_level in ['public', 'internal']:
                doc.can_view = user in doc.department_id.user_ids
            else:
                doc.can_view = False
    
    def _generate_barcode(self):
        """Generate unique barcode"""
        sequence = self.env['ir.sequence'].next_by_code('nbs.document.barcode')
        if not sequence:
            # Fallback if sequence not created yet
            sequence = str(self.env['nbs.document'].search_count([]) + 1).zfill(6)
        return f'NBS{sequence}'
    
    def _get_client_ip(self):
        """Get client IP address"""
        request = self.env.get('request')
        if request:
            return request.httprequest.remote_addr
        return None
    
    def _get_user_agent(self):
        """Get user agent"""
        request = self.env.get('request')
        if request:
            return request.httprequest.headers.get('User-Agent')
        return None
    
    def action_activate(self):
        """Activate document and lock it"""
        for doc in self:
            if doc.state == 'draft':
                doc.write({
                    'state': 'active',
                    'is_locked': True
                })
                
                # Schedule OCR if current version exists
                if doc.current_version_id:
                    doc.with_delay()._process_ocr()
    
    def action_archive_document(self):
        """Archive document (soft delete)"""
        self.ensure_one()
        if not self.can_archive:
            raise AccessError(_('You do not have permission to archive this document'))
        
        self.write({'state': 'archived'})
        
        # Send notification to uploader
        self.env['nbs.notification'].sudo().create({
            'user_id': self.uploader_id.id,
            'title': _('Document Archived'),
            'message': _('Your document "%s" has been archived') % self.name,
            'notification_type': 'archive',
            'document_id': self.id,
        })
        
        return True
    
    def action_unarchive(self):
        """Unarchive document"""
        self.ensure_one()
        self.write({'state': 'active'})
        return True
    
    def action_view_versions(self):
        """Open version history"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Version History'),
            'res_model': 'nbs.document.version',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
            'context': {'default_document_id': self.id}
        }
    
    def action_view_audit_logs(self):
        """Open audit logs"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Audit Logs'),
            'res_model': 'nbs.audit.log',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
        }
    
    def action_request_edit(self):
        """Open edit request wizard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Request Edit'),
            'res_model': 'nbs.edit.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_document_id': self.id}
        }
    
    def _schedule_ocr(self):
        """Schedule background OCR job"""
        self.with_delay(priority=5, description=f'OCR: {self.name}')._process_ocr()
    
    def _process_ocr(self):
        """Background job: OCR processing"""
        self.ensure_one()
        
        if not self.current_version_id:
            return
        
        self.write({'ocr_status': 'processing'})
        
        try:
            # Call OCR service
            ocr_service = self.env['nbs.ocr.service']
            success = ocr_service.process_document_version(self.current_version_id)
            
            if success:
                self.write({'ocr_status': 'completed'})
                
                # Schedule OpenSearch indexing
                self.with_delay()._index_in_opensearch()
            else:
                self.write({'ocr_status': 'failed'})
        except Exception as e:
            self.write({'ocr_status': 'failed'})
            raise
    
    def _index_in_opensearch(self):
        """Index document in OpenSearch"""
        self.ensure_one()
        
        try:
            search_service = self.env['nbs.opensearch.service']
            search_service.index_document(self)
            
            self.write({
                'indexed_in_search': True,
                'last_indexed_date': fields.Datetime.now()
            })
        except Exception as e:
            # Log but don't fail
            print(f"Failed to index document {self.id}: {e}")
    
    def get_custom_fields_values(self):
        """Parse and return custom fields data"""
        self.ensure_one()
        if self.custom_fields_data:
            try:
                return json.loads(self.custom_fields_data)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_custom_fields_values(self, values):
        """Set custom fields data"""
        self.ensure_one()
        self.custom_fields_data = json.dumps(values, ensure_ascii=False)

