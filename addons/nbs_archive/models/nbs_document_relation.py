# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class NBSDocumentRelation(models.Model):
    _name = 'nbs.document.relation'
    _description = 'Document Relations'
    _rec_name = 'display_name'
    
    document_id = fields.Many2one(
        'nbs.document',
        string='Document',
        required=True,
        ondelete='cascade',
        index=True
    )
    related_document_id = fields.Many2one(
        'nbs.document',
        string='Related Document',
        required=True,
        ondelete='cascade',
        index=True
    )
    relation_type = fields.Selection([
        ('parent', 'مستند أصلي'),
        ('child', 'مستند فرعي'),
        ('attachment', 'مرفق'),
        ('reference', 'مرجع'),
        ('replacement', 'بديل'),
        ('amendment', 'تعديل'),
        ('related', 'ذو صلة'),
    ], string='نوع العلاقة', required=True, default='related')
    
    notes = fields.Text(string='ملاحظات')
    
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    @api.depends('document_id', 'related_document_id', 'relation_type')
    def _compute_display_name(self):
        for rel in self:
            if rel.document_id and rel.related_document_id:
                rel.display_name = f'{rel.document_id.name} - {rel.relation_type} - {rel.related_document_id.name}'
            else:
                rel.display_name = 'Document Relation'
    
    @api.constrains('document_id', 'related_document_id')
    def _check_no_self_relation(self):
        for rel in self:
            if rel.document_id.id == rel.related_document_id.id:
                raise ValidationError(_('لا يمكن ربط المستند بنفسه'))


class NBSDocumentFolder(models.Model):
    _name = 'nbs.document.folder'
    _description = 'Document Folder (إضبارة)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    name = fields.Char(
        string='اسم الإضبارة',
        required=True,
        tracking=True
    )
    code = fields.Char(
        string='الرمز',
        required=True,
        index=True,
        tracking=True
    )
    department_id = fields.Many2one(
        'nbs.department',
        string='القسم',
        required=True,
        index=True
    )
    folder_type = fields.Selection([
        ('project', 'مشروع'),
        ('client', 'عميل'),
        ('shipment', 'شحنة'),
        ('case', 'قضية'),
        ('contract', 'عقد'),
        ('employee', 'موظف'),
        ('other', 'أخرى'),
    ], string='نوع الإضبارة', required=True, default='other')
    
    description = fields.Text(string='الوصف')
    
    document_ids = fields.Many2many(
        'nbs.document',
        'folder_document_rel',
        'folder_id',
        'document_id',
        string='المستندات'
    )
    main_document_id = fields.Many2one(
        'nbs.document',
        string='الوثيقة الرئيسية',
        ondelete='restrict',
        index=True,
        tracking=True,
        help='Main (root) document for this folder.'
    )

    workflow_id = fields.Many2one(
        'nbs.folder.workflow',
        string='Workflow',
        ondelete='restrict',
        index=True,
        help='Workflow configuration for this folder.'
    )
    workflow_state_id = fields.Many2one(
        'nbs.folder.workflow.state',
        string='Current Workflow State',
        ondelete='restrict',
        index=True,
        tracking=True,
        help='Current state of this folder in its workflow.'
    )
    document_count = fields.Integer(
        string='عدد المستندات',
        compute='_compute_document_count',
        store=True
    )
    
    parent_folder_id = fields.Many2one(
        'nbs.document.folder',
        string='الإضبارة الأم',
        ondelete='restrict'
    )
    child_folder_ids = fields.One2many(
        'nbs.document.folder',
        'parent_folder_id',
        string='الإضبارات الفرعية'
    )
    
    owner_id = fields.Many2one(
        'res.users',
        string='المسؤول',
        default=lambda self: self.env.user,
        required=True
    )
    
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('active', 'نشط'),
        ('completed', 'مكتمل'),
        ('archived', 'مؤرشف'),
    ], string='الحالة', default='draft', required=True, tracking=True)
    
    # Metadata fields
    reference_number = fields.Char(string='رقم المرجع', index=True)
    start_date = fields.Date(string='تاريخ البداية')
    end_date = fields.Date(string='تاريخ الانتهاء')
    
    tags = fields.Many2many(
        'nbs.document.tag',
        string='الوسوم'
    )
    
    color = fields.Integer(string='Color Index', default=0)
    
    active = fields.Boolean(default=True)
    
    @api.depends('document_ids')
    def _compute_document_count(self):
        for folder in self:
            folder.document_count = len(folder.document_ids)
    
    @api.constrains('parent_folder_id')
    def _check_parent_folder(self):
        for folder in self:
            if folder.parent_folder_id:
                # Check for circular reference
                parent = folder.parent_folder_id
                visited = set()
                while parent:
                    if parent.id in visited:
                        raise ValidationError(_('لا يمكن إنشاء علاقة دائرية بين الإضبارات'))
                    visited.add(parent.id)
                    parent = parent.parent_folder_id


class NBSDocumentAttachment(models.Model):
    _name = 'nbs.document.attachment'
    _description = 'Document Attachments'
    _order = 'create_date desc'
    
    document_id = fields.Many2one(
        'nbs.document',
        string='المستند الأصلي',
        required=True,
        ondelete='cascade',
        index=True
    )
    name = fields.Char(
        string='اسم المرفق',
        required=True
    )
    description = fields.Text(string='الوصف')
    
    file_data = fields.Binary(
        string='الملف',
        required=True,
        attachment=True
    )
    file_name = fields.Char(string='اسم الملف', required=True)
    file_size = fields.Integer(string='حجم الملف (بايت)')
    file_type = fields.Char(string='نوع الملف', compute='_compute_file_type', store=True)
    
    uploader_id = fields.Many2one(
        'res.users',
        string='الرافع',
        default=lambda self: self.env.user,
        required=True
    )
    upload_date = fields.Datetime(
        string='تاريخ الرفع',
        default=fields.Datetime.now,
        required=True
    )
    
    attachment_type = fields.Selection([
        ('supporting', 'مستند داعم'),
        ('reference', 'مرجع'),
        ('proof', 'إثبات'),
        ('image', 'صورة'),
        ('other', 'أخرى'),
    ], string='نوع المرفق', default='supporting')
    
    @api.depends('file_name')
    def _compute_file_type(self):
        for attachment in self:
            if attachment.file_name:
                ext = attachment.file_name.split('.')[-1].lower() if '.' in attachment.file_name else ''
                attachment.file_type = ext
            else:
                attachment.file_type = ''
    
    @api.model
    def create(self, vals):
        attachment = super().create(vals)
        
        # Log attachment upload
        self.env['nbs.audit.log'].sudo().create({
            'user_id': self.env.user.id,
            'action': 'attachment_upload',
            'document_id': attachment.document_id.id,
            'department_id': attachment.document_id.department_id.id,
            'metadata': f'Attachment: {attachment.name}',
        })
        
        return attachment


