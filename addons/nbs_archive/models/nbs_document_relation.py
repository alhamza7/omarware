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


# NOTE: nbs.document.folder is now defined in nbs_folder.py (Week 2 - Hierarchical system)
# Old "Dossier/Case File" concept has been replaced with modern folder hierarchy


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
    
    # Soft Delete Fields
    is_deleted = fields.Boolean(
        string='محذوف',
        default=False,
        index=True,
        help='True if attachment is in trash'
    )
    deleted_at = fields.Datetime(string='تاريخ الحذف')
    deleted_by = fields.Many2one('res.users', string='حذف بواسطة')
    deletion_reason = fields.Text(string='سبب الحذف')
    restore_deadline = fields.Datetime(
        string='موعد الحذف النهائي',
        help='Permanent deletion after this date (30 days from deletion)'
    )
    
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
        
        # Log attachment upload (non-blocking)
        try:
            self.env['nbs.audit.log'].sudo().create({
                'user_id': self.env.user.id,
                'action': 'attachment_upload',
                'document_id': attachment.document_id.id,
                'department_id': attachment.document_id.department_id.id,
                'metadata': f'Attachment: {attachment.name}',
            })
        except Exception:
            pass  # non-blocking
        
        return attachment
    
    def soft_delete(self, reason=None):
        """Soft delete attachment - move to trash"""
        from datetime import timedelta
        
        for attachment in self:
            attachment.write({
                'is_deleted': True,
                'deleted_at': fields.Datetime.now(),
                'deleted_by': self.env.user.id,
                'deletion_reason': reason,
                'restore_deadline': fields.Datetime.now() + timedelta(days=30)
            })
            
            # Log (non-blocking)
            try:
                self.env['nbs.audit.log'].sudo().create({
                    'user_id': self.env.user.id,
                    'action': 'attachment_deleted',
                    'document_id': attachment.document_id.id,
                    'department_id': attachment.document_id.department_id.id,
                    'metadata': f'Deleted attachment: {attachment.name}. Reason: {reason or "N/A"}'
                })
            except Exception:
                pass  # non-blocking
    
    def restore(self):
        """Restore attachment from trash"""
        for attachment in self:
            attachment.write({
                'is_deleted': False,
                'deleted_at': False,
                'deleted_by': False,
                'deletion_reason': False,
                'restore_deadline': False
            })
            
            # Log (non-blocking)
            try:
                self.env['nbs.audit.log'].sudo().create({
                    'user_id': self.env.user.id,
                    'action': 'attachment_restored',
                    'document_id': attachment.document_id.id,
                    'department_id': attachment.document_id.department_id.id,
                    'metadata': f'Restored attachment: {attachment.name}'
                })
            except Exception:
                pass  # non-blocking
    
    def permanent_delete(self):
        """Permanently delete attachment"""
        for attachment in self:
            doc_id = attachment.document_id.id
            dept_id = attachment.document_id.department_id.id
            att_name = attachment.name
            
            # Log before deletion (non-blocking)
            try:
                self.env['nbs.audit.log'].sudo().create({
                    'user_id': self.env.user.id,
                    'action': 'attachment_permanently_deleted',
                    'document_id': doc_id,
                    'department_id': dept_id,
                    'metadata': f'Permanently deleted attachment: {att_name}'
                })
            except Exception:
                pass  # non-blocking
            
            # Delete
            attachment.unlink()


