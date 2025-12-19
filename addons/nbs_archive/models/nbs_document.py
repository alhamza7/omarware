# -*- coding: utf-8 -*-

import json
import secrets
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


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
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string='Status', default='draft', required=True, tracking=True, index=True)
    
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
    
    # OCR status
    ocr_status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], string='OCR Status', default='pending', tracking=True, index=True)
    
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
            # Generate barcode
            if not vals.get('barcode'):
                vals['barcode'] = self._generate_barcode()
            
            # Set to active and locked by default
            if 'state' not in vals:
                vals['state'] = 'active'
            if 'is_locked' not in vals:
                vals['is_locked'] = True
        
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
        
        return super().write(vals)
    
    def unlink(self):
        """CRITICAL: Prevent hard delete"""
        raise ValidationError(_('Documents cannot be deleted! Please archive instead.'))
    
    @api.depends('version_ids')
    def _compute_version_count(self):
        for doc in self:
            doc.version_count = len(doc.version_ids)
    
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

