# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'
    
    custom_report_template_id = fields.Many2one(
        'custom.report.template',
        string='قالب التقرير / Report Template',
        domain=[('report_type', 'in', ['pos_order', 'sale_order', 'invoice'])],
        help="اختر قالب تقرير مخصص للطباعة"
    )
    
    def action_print_custom_report(self):
        """طباعة باستخدام قالب مخصص"""
        self.ensure_one()
        
        template = self.custom_report_template_id
        if not template:
            # استخدام القالب الافتراضي
            template = self.env['custom.report.template'].search([
                ('report_type', '=', 'pos_order'),
                ('active', '=', True)
            ], limit=1)
        
        if not template:
            raise UserError(_('لم يتم العثور على قالب تقرير! الرجاء إنشاء قالب أولاً.'))
        
        # توليد PDF
        pdf = template.generate_report(self.id, self._name)
        
        # حفظ كـ attachment
        import base64
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.name}_{template.name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    custom_report_template_id = fields.Many2one(
        'custom.report.template',
        string='قالب التقرير / Report Template',
        domain=[('report_type', 'in', ['sale_order', 'quotation', 'invoice'])],
    )
    
    def action_print_custom_report(self):
        """طباعة باستخدام قالب مخصص"""
        self.ensure_one()
        
        template = self.custom_report_template_id
        if not template:
            # اختيار بناءً على الحالة
            report_type = 'quotation' if self.state == 'draft' else 'sale_order'
            template = self.env['custom.report.template'].search([
                ('report_type', '=', report_type),
                ('active', '=', True)
            ], limit=1)
        
        if not template:
            raise UserError(_('لم يتم العثور على قالب تقرير!'))
        
        # توليد PDF
        pdf = template.generate_report(self.id, self._name)
        
        import base64
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.name}_{template.name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

