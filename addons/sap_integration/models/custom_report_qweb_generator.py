# -*- coding: utf-8 -*-

"""
QWeb Template Generator for Custom Reports
Generates dynamic QWeb templates based on custom.report.template configuration
"""

from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class CustomReportQWebGenerator(models.AbstractModel):
    """مولد قوالب QWeb الديناميكية"""
    _name = 'custom.report.qweb.generator'
    _description = 'QWeb Template Generator'
    
    def generate_qweb_template(self, template):
        """توليد قالب QWeb من custom.report.template"""
        
        html_parts = []
        
        # بداية القالب
        html_parts.append('''
<template id="report_template_{template_id}">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <div class="page" style="{page_style}">
        '''.format(
            template_id=template.id,
            page_style=self._get_page_style(template)
        ))
        
        # الخلفية والعلامة المائية
        if template.background_image or template.watermark_text:
            html_parts.append(self._generate_background(template))
        
        # الترويسة
        if template.show_header:
            html_parts.append(self._generate_header(template))
        
        # العنوان
        if template.show_title:
            html_parts.append(self._generate_title(template))
        
        # معلومات العميل والمستند
        html_parts.append('<div class="row mt-4">')
        if template.show_customer_info:
            html_parts.append(self._generate_customer_info(template))
        if template.show_document_info:
            html_parts.append(self._generate_document_info(template))
        html_parts.append('</div>')
        
        # الأقسام قبل الجدول
        html_parts.append(self._generate_sections(template, 'before_table'))
        
        # جدول المنتجات
        if template.show_table:
            html_parts.append(self._generate_table(template))
        
        # الأقسام بعد الجدول
        html_parts.append(self._generate_sections(template, 'after_table'))
        
        # الأقسام قبل المجاميع
        html_parts.append(self._generate_sections(template, 'before_totals'))
        
        # المجاميع
        if template.show_totals:
            html_parts.append(self._generate_totals(template))
        
        # الأقسام بعد المجاميع
        html_parts.append(self._generate_sections(template, 'after_totals'))
        
        # التذييل
        if template.show_footer:
            html_parts.append(self._generate_footer(template))
        
        # نهاية القالب
        html_parts.append('''
            </div>
        </t>
    </t>
</template>
        ''')
        
        # CSS مخصص
        if template.custom_css:
            html_parts.append(f'<style>{template.custom_css}</style>')
        
        return '\n'.join(html_parts)
    
    def _get_page_style(self, template):
        """الحصول على CSS للصفحة"""
        styles = []
        styles.append(f'width: {template.page_width}mm')
        styles.append(f'min-height: {template.page_height}mm')
        styles.append(f'padding: {template.margin_top}mm {template.margin_right}mm {template.margin_bottom}mm {template.margin_left}mm')
        styles.append('position: relative')
        return '; '.join(styles)
    
    def _generate_background(self, template):
        """توليد الخلفية والعلامة المائية"""
        html = []
        
        if template.background_image:
            html.append(f'''
            <div class="background-image" style="
                position: absolute;
                top: 0; left: 0; right: 0; bottom: 0;
                opacity: {template.background_opacity};
                background-image: url('data:image/png;base64,{{{{ template.background_image }}}}');
                background-size: cover;
                background-position: center;
                z-index: -1;
            "></div>
            ''')
        
        if template.watermark_text:
            html.append(f'''
            <div class="watermark" style="
                position: absolute;
                top: 50%; left: 50%;
                transform: translate(-50%, -50%) rotate({template.watermark_angle}deg);
                font-size: 72px;
                color: rgba(0,0,0,0.05);
                font-weight: bold;
                z-index: -1;
                white-space: nowrap;
            ">{{{{ template.watermark_text }}}}</div>
            ''')
        
        return '\n'.join(html)
    
    def _generate_header(self, template):
        """توليد الترويسة"""
        if template.header_html:
            return f'<div class="header">{template.header_html}</div>'
        
        html = [f'<div class="header" style="height: {template.header_height}px; margin-bottom: 20px;">']
        html.append('<div class="row">')
        
        # الشعار
        if template.show_logo:
            position_class = {
                'left': 'col-4',
                'center': 'col-12 text-center',
                'right': 'col-4 offset-8 text-right'
            }.get(template.logo_position, 'col-4')
            
            html.append(f'''
            <div class="{position_class}">
                <img t-if="doc.company_id.logo" 
                     t-att-src="'data:image/png;base64,%s' % doc.company_id.logo.decode('utf-8')"
                     style="max-width: {template.logo_width}px; max-height: {template.header_height}px;"
                     alt="Logo"/>
            </div>
            ''')
        
        # معلومات الشركة
        if template.show_company_info:
            position_class = {
                'left': 'col-4',
                'center': 'col-12 text-center',
                'right': 'col-4 offset-4 text-right'
            }.get(template.company_info_position, 'col-4 offset-4 text-right')
            
            html.append(f'''
            <div class="{position_class}">
                <div><strong t-field="doc.company_id.name"/></div>
                <div t-field="doc.company_id.street"/>
                <div>
                    <span t-field="doc.company_id.city"/>
                    <span t-if="doc.company_id.state_id">, <span t-field="doc.company_id.state_id.name"/></span>
                </div>
                <div t-if="doc.company_id.phone">هاتف: <span t-field="doc.company_id.phone"/></div>
                <div t-if="doc.company_id.email">البريد: <span t-field="doc.company_id.email"/></div>
            </div>
            ''')
        
        html.append('</div></div>')
        return '\n'.join(html)
    
    def _generate_title(self, template):
        """توليد العنوان"""
        alignment_class = {
            'left': 'text-left',
            'center': 'text-center',
            'right': 'text-right'
        }.get(template.title_alignment, 'text-center')
        
        return f'''
        <h1 class="{alignment_class} mt-4 mb-4" style="
            font-size: {template.title_font_size}px;
            color: {template.title_color};
        ">{{{{ template.title_text }}}}</h1>
        '''
    
    def _generate_customer_info(self, template):
        """توليد معلومات العميل"""
        position_class = 'col-6' if template.show_document_info else 'col-12'
        
        html = [f'<div class="{position_class}">']
        html.append('<div class="card"><div class="card-body">')
        html.append('<h5>معلومات العميل</h5>')
        html.append('<div><strong t-field="doc.partner_id.name"/></div>')
        html.append('<div t-field="doc.partner_id.street"/>')
        html.append('<div t-if="doc.partner_id.phone">هاتف: <span t-field="doc.partner_id.phone"/></div>')
        
        # حقول إضافية
        for field in template.customer_fields:
            html.append(f'<div>{field.name}: <span t-field="doc.{field.technical_name}"/></div>')
        
        html.append('</div></div></div>')
        return '\n'.join(html)
    
    def _generate_document_info(self, template):
        """توليد معلومات المستند"""
        position_class = 'col-6' if template.show_customer_info else 'col-12'
        
        html = [f'<div class="{position_class}">']
        html.append('<div class="card"><div class="card-body">')
        html.append('<h5>معلومات المستند</h5>')
        html.append('<div><strong>رقم:</strong> <span t-field="doc.name"/></div>')
        html.append('<div><strong>التاريخ:</strong> <span t-field="doc.date_order"/></div>')
        
        # حقول إضافية
        for field in template.document_fields:
            html.append(f'<div><strong>{field.name}:</strong> <span t-field="doc.{field.technical_name}"/></div>')
        
        html.append('</div></div></div>')
        return '\n'.join(html)
    
    def _generate_table(self, template):
        """توليد جدول المنتجات"""
        html = []
        
        # CSS للجدول
        table_style = f'''
        <style>
            .product-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 30px;
                font-size: {template.table_font_size}px;
            }}
            .product-table thead tr {{
                background-color: {template.table_header_bg};
                color: {template.table_header_color};
                height: {template.table_row_height}px;
            }}
            .product-table tbody tr {{
                height: {template.table_row_height}px;
            }}
            {"".join([
                f".product-table tbody tr:nth-child(odd) {{ background-color: {template.row_color_1}; }}",
                f".product-table tbody tr:nth-child(even) {{ background-color: {template.row_color_2}; }}"
            ]) if template.alternate_row_colors else ""}
            .product-table th, .product-table td {{
                border: 1px solid {template.table_border_color};
                padding: 8px;
            }}
        </style>
        '''
        html.append(table_style)
        
        # بداية الجدول
        html.append('<table class="product-table">')
        
        # رأس الجدول
        html.append('<thead><tr>')
        for col in template.table_columns.filtered(lambda c: c.visible).sorted(key=lambda c: c.sequence):
            alignment_class = f'text-{col.alignment}'
            html.append(f'<th class="{alignment_class}" style="width: {col.width}%">{col.name}</th>')
        html.append('</tr></thead>')
        
        # جسم الجدول
        html.append('<tbody>')
        html.append('<t t-foreach="doc.order_line" t-as="line">')
        html.append('<tr>')
        
        for col in template.table_columns.filtered(lambda c: c.visible).sorted(key=lambda c: c.sequence):
            alignment_class = f'text-{col.alignment}'
            
            if col.is_monetary:
                html.append(f'''
                <td class="{alignment_class}">
                    <span t-esc="'{:.{col.decimal_places}f}'.format(line.{col.technical_name})"/>
                    <span t-if="template.show_currency_name" t-field="doc.currency_id.name"/>
                </td>
                ''')
            else:
                html.append(f'<td class="{alignment_class}" t-field="line.{col.technical_name}"/>')
        
        html.append('</tr>')
        html.append('</t>')
        html.append('</tbody>')
        html.append('</table>')
        
        return '\n'.join(html)
    
    def _generate_totals(self, template):
        """توليد المجاميع"""
        position_class = 'offset-6 col-6' if template.totals_position == 'right' else 'col-6'
        
        html = [f'<div class="row mt-4"><div class="{position_class}">']
        html.append('<table class="table table-sm">')
        
        for total in template.totals_fields.filtered(lambda t: t.visible).sorted(key=lambda t: t.sequence):
            html.append(f'''
            <tr style="font-size: {total.font_size}px; font-weight: {total.font_weight}; color: {total.color};">
                <td class="text-right"><strong>{total.name}</strong></td>
                <td class="text-right">
                    <span t-field="doc.{total.technical_name}"/>
                    <span t-if="template.show_currency_name" t-field="doc.currency_id.name"/>
                </td>
            </tr>
            ''')
        
        html.append('</table></div></div>')
        return '\n'.join(html)
    
    def _generate_sections(self, template, position):
        """توليد الأقسام الإضافية"""
        sections = template.sections.filtered(lambda s: s.position == position and s.visible)
        
        if not sections:
            return ''
        
        html = []
        for section in sections.sorted(key=lambda s: s.sequence):
            style = f'''
                background-color: {section.background_color};
                min-height: {section.height}px;
                padding: {section.padding}px;
                {f"border: 1px solid {section.border_color};" if section.border else ""}
            '''
            
            html.append(f'<div class="section mt-3" style="{style}">')
            html.append(f'<h5>{section.name}</h5>')
            
            if section.content_type == 'html':
                html.append(section.content_html or '')
            elif section.content_type == 'text':
                html.append(f'<p>{section.content_text or ""}</p>')
            elif section.content_type == 'field':
                html.append(f'<div t-field="doc.{section.content_field}"/>')
            
            html.append('</div>')
        
        return '\n'.join(html)
    
    def _generate_footer(self, template):
        """توليد التذييل"""
        if template.footer_html:
            return f'<div class="footer">{template.footer_html}</div>'
        
        html = [f'<div class="footer" style="height: {template.footer_height}px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px;">']
        
        if template.show_page_number:
            html.append('''
            <div class="text-center">
                صفحة <span class="page"/> من <span class="topage"/>
            </div>
            ''')
        
        html.append('</div>')
        return '\n'.join(html)

