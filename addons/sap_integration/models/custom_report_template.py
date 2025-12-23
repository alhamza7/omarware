# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import base64

_logger = logging.getLogger(__name__)


class CustomReportTemplate(models.Model):
    """قالب تقرير مخصص - Custom Report Template"""
    _name = 'custom.report.template'
    _description = 'Custom Report Template Designer'
    _order = 'sequence, name'
    
    # ========== Basic Info ==========
    name = fields.Char('اسم القالب / Template Name', required=True, translate=True)
    code = fields.Char('الرمز / Code', required=True, copy=False,
                      help="رمز فريد للقالب (مثل: SALES_INV_USD)")
    sequence = fields.Integer('الترتيب / Sequence', default=10)
    active = fields.Boolean('نشط / Active', default=True)
    
    # ========== Report Type ==========
    report_type = fields.Selection([
        ('sale_order', 'أمر بيع / Sale Order'),
        ('quotation', 'عرض سعر / Quotation'),
        ('invoice', 'فاتورة / Invoice'),
        ('pos_order', 'فاتورة POS / POS Order'),
        ('delivery', 'إشعار تسليم / Delivery Note'),
        ('custom', 'مخصص / Custom'),
    ], string='نوع التقرير / Report Type', required=True, default='sale_order')
    
    # ========== Currency & Language ==========
    currency_id = fields.Many2one('res.currency', 'العملة / Currency',
                                  default=lambda self: self.env.company.currency_id)
    show_currency_name = fields.Boolean('إظهار اسم العملة', default=True)
    currency_position = fields.Selection([
        ('before', 'قبل المبلغ'),
        ('after', 'بعد المبلغ'),
    ], default='after')
    
    language = fields.Selection([
        ('ar_SA', 'عربي'),
        ('en_US', 'English'),
        ('both', 'ثنائي اللغة'),
    ], default='ar_SA', string='اللغة / Language')
    
    # ========== Paper Settings ==========
    paper_format_id = fields.Many2one('report.paperformat', 'حجم الورق / Paper Size',
                                     default=lambda self: self.env.ref('base.paperformat_euro', raise_if_not_found=False))
    orientation = fields.Selection([
        ('Portrait', 'عمودي / Portrait'),
        ('Landscape', 'أفقي / Landscape'),
    ], default='Portrait', string='الاتجاه / Orientation')
    
    page_width = fields.Integer('عرض الصفحة (mm)', default=210)
    page_height = fields.Integer('طول الصفحة (mm)', default=297)
    margin_top = fields.Integer('الهامش العلوي (mm)', default=10)
    margin_bottom = fields.Integer('الهامش السفلي (mm)', default=10)
    margin_left = fields.Integer('الهامش الأيسر (mm)', default=10)
    margin_right = fields.Integer('الهامش الأيمن (mm)', default=10)
    
    # ========== Header Settings ==========
    show_header = fields.Boolean('إظهار الترويسة', default=True)
    header_html = fields.Html('HTML الترويسة / Header HTML')
    header_height = fields.Integer('ارتفاع الترويسة (px)', default=100)
    
    show_logo = fields.Boolean('إظهار الشعار', default=True)
    logo_position = fields.Selection([
        ('left', 'يسار'),
        ('center', 'وسط'),
        ('right', 'يمين'),
    ], default='left', string='موضع الشعار')
    logo_width = fields.Integer('عرض الشعار (px)', default=150)
    
    show_company_info = fields.Boolean('إظهار معلومات الشركة', default=True)
    company_info_position = fields.Selection([
        ('left', 'يسار'),
        ('center', 'وسط'),
        ('right', 'يمين'),
    ], default='right')
    
    # ========== Title Settings ==========
    show_title = fields.Boolean('إظهار العنوان', default=True)
    title_text = fields.Char('نص العنوان / Title', translate=True,
                             default='فاتورة مبيعات / Sales Invoice')
    title_font_size = fields.Integer('حجم خط العنوان', default=24)
    title_alignment = fields.Selection([
        ('left', 'يسار'),
        ('center', 'وسط'),
        ('right', 'يمين'),
    ], default='center')
    title_color = fields.Char('لون العنوان', default='#333333')
    
    # ========== Customer Info ==========
    show_customer_info = fields.Boolean('إظهار معلومات العميل', default=True)
    customer_info_position = fields.Selection([
        ('left', 'يسار'),
        ('right', 'يمين'),
    ], default='left')
    customer_fields = fields.Many2many('custom.report.field', 
                                      'template_customer_field_rel',
                                      string='حقول العميل / Customer Fields')
    
    # ========== Document Info ==========
    show_document_info = fields.Boolean('إظهار معلومات المستند', default=True)
    document_info_position = fields.Selection([
        ('left', 'يسار'),
        ('right', 'يمين'),
    ], default='right')
    document_fields = fields.Many2many('custom.report.field',
                                      'template_document_field_rel',
                                      string='حقول المستند / Document Fields')
    
    # ========== Table Settings ==========
    show_table = fields.Boolean('إظهار جدول المنتجات', default=True)
    table_columns = fields.One2many('custom.report.column', 'template_id',
                                   string='أعمدة الجدول / Table Columns')
    table_header_bg = fields.Char('خلفية رأس الجدول', default='#4A90E2')
    table_header_color = fields.Char('لون نص رأس الجدول', default='#FFFFFF')
    table_border_color = fields.Char('لون حدود الجدول', default='#DDDDDD')
    table_row_height = fields.Integer('ارتفاع الصف (px)', default=30)
    table_font_size = fields.Integer('حجم خط الجدول', default=11)
    
    # Alternating row colors
    alternate_row_colors = fields.Boolean('ألوان صفوف متناوبة', default=True)
    row_color_1 = fields.Char('لون الصف 1', default='#FFFFFF')
    row_color_2 = fields.Char('لون الصف 2', default='#F9F9F9')
    
    # ========== Totals Section ==========
    show_totals = fields.Boolean('إظهار المجاميع', default=True)
    totals_position = fields.Selection([
        ('left', 'يسار'),
        ('right', 'يمين'),
    ], default='right')
    totals_fields = fields.One2many('custom.report.total', 'template_id',
                                   string='حقول المجاميع / Totals Fields')
    
    # ========== Footer Settings ==========
    show_footer = fields.Boolean('إظهار التذييل', default=True)
    footer_html = fields.Html('HTML التذييل / Footer HTML')
    footer_height = fields.Integer('ارتفاع التذييل (px)', default=80)
    show_page_number = fields.Boolean('إظهار رقم الصفحة', default=True)
    
    # ========== Multi-page Settings ==========
    repeat_header = fields.Boolean('تكرار الترويسة في كل صفحة', default=True)
    repeat_table_header = fields.Boolean('تكرار رأس الجدول في كل صفحة', default=True)
    max_rows_per_page = fields.Integer('عدد الصفوف لكل صفحة', default=20,
                                       help="0 = غير محدود")
    
    # ========== Sections ==========
    sections = fields.One2many('custom.report.section', 'template_id',
                              string='الأقسام الإضافية / Additional Sections')
    
    # ========== Custom CSS ==========
    custom_css = fields.Text('CSS مخصص / Custom CSS')
    
    # ========== Backgrounds ==========
    background_image = fields.Binary('صورة خلفية / Background Image')
    background_filename = fields.Char('اسم ملف الخلفية')
    background_opacity = fields.Float('شفافية الخلفية', default=0.1,
                                     help="0.0 = شفاف تماماً, 1.0 = غير شفاف")
    watermark_text = fields.Char('نص العلامة المائية / Watermark')
    watermark_angle = fields.Integer('زاوية العلامة المائية', default=45)
    
    # ========== Conditions ==========
    use_conditions = fields.Boolean('استخدام شروط', default=False)
    condition_field = fields.Char('حقل الشرط',
                                  help="مثل: state, amount_total")
    condition_operator = fields.Selection([
        ('==', 'يساوي'),
        ('!=', 'لا يساوي'),
        ('>', 'أكبر من'),
        ('<', 'أصغر من'),
        ('>=', 'أكبر من أو يساوي'),
        ('<=', 'أصغر من أو يساوي'),
        ('in', 'موجود في'),
    ], string='المعامل / Operator')
    condition_value = fields.Char('قيمة الشرط')
    
    # ========== Statistics ==========
    usage_count = fields.Integer('عدد مرات الاستخدام', readonly=True, default=0)
    last_used = fields.Datetime('آخر استخدام', readonly=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure code is unique"""
        for vals in vals_list:
            if vals.get('code'):
                existing = self.search([('code', '=', vals['code'])])
                if existing:
                    raise UserError(_(f"القالب برمز '{vals['code']}' موجود مسبقاً!"))
        return super(CustomReportTemplate, self).create(vals_list)
    
    def generate_report(self, record_id, model_name):
        """توليد التقرير لسجل معين"""
        self.ensure_one()
        
        # زيادة عداد الاستخدام
        self.sudo().write({
            'usage_count': self.usage_count + 1,
            'last_used': fields.Datetime.now()
        })
        
        # الحصول على السجل
        record = self.env[model_name].browse(record_id)
        
        # توليد HTML
        html = self._generate_html(record)
        
        # تحويل إلى PDF
        pdf = self.env['ir.actions.report']._run_wkhtmltopdf(
            [html],
            landscape=self.orientation == 'Landscape',
            specific_paperformat_args={
                'data-report-margin-top': self.margin_top,
                'data-report-margin-bottom': self.margin_bottom,
                'data-report-margin-left': self.margin_left,
                'data-report-margin-right': self.margin_right,
            }
        )
        
        return pdf
    
    def _generate_html(self, record):
        """توليد HTML من القالب"""
        self.ensure_one()
        
        # استخدام QWeb لتوليد HTML
        template_xml_id = f'custom_report_designer.report_template_{self.id}'
        
        # إذا لم يوجد قالب، إنشاء واحد ديناميكياً
        if not self.env.ref(template_xml_id, raise_if_not_found=False):
            self._create_qweb_template()
        
        return self.env['ir.qweb']._render(template_xml_id, {
            'doc': record,
            'template': self,
        })
    
    def _create_qweb_template(self):
        """إنشاء قالب QWeb ديناميكياً"""
        # سيتم تنفيذه في ملف منفصل
        pass
    
    def action_preview(self):
        """معاينة القالب"""
        self.ensure_one()
        
        # الحصول على أول سجل من النوع المحدد
        if self.report_type == 'sale_order':
            record = self.env['sale.order'].search([], limit=1)
        elif self.report_type == 'pos_order':
            record = self.env['pos.order'].search([], limit=1)
        # ... إلخ
        
        if not record:
            raise UserError(_('لا توجد سجلات لمعاينة التقرير!'))
        
        # توليد PDF
        pdf = self.generate_report(record.id, record._name)
        
        # حفظ PDF مؤقت
        attachment = self.env['ir.attachment'].create({
            'name': f'Preview_{self.name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf),
            'mimetype': 'application/pdf',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
    
    def action_duplicate(self):
        """نسخ القالب"""
        self.ensure_one()
        
        new_template = self.copy({
            'name': f'{self.name} (نسخة)',
            'code': f'{self.code}_COPY',
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'custom.report.template',
            'res_id': new_template.id,
            'view_mode': 'form',
            'target': 'current',
        }


class CustomReportField(models.Model):
    """حقول التقرير المخصص"""
    _name = 'custom.report.field'
    _description = 'Custom Report Field'
    _order = 'sequence, name'
    
    name = fields.Char('اسم الحقل / Field Name', required=True, translate=True)
    technical_name = fields.Char('الاسم التقني / Technical Name', required=True,
                                 help="مثل: partner_id.name, amount_total")
    field_type = fields.Selection([
        ('char', 'نص'),
        ('text', 'نص طويل'),
        ('integer', 'رقم صحيح'),
        ('float', 'رقم عشري'),
        ('monetary', 'مبلغ مالي'),
        ('date', 'تاريخ'),
        ('datetime', 'تاريخ ووقت'),
        ('boolean', 'صح/خطأ'),
        ('selection', 'اختيار'),
        ('many2one', 'علاقة'),
    ], string='نوع الحقل', required=True, default='char')
    
    sequence = fields.Integer('الترتيب', default=10)
    required = fields.Boolean('مطلوب', default=False)
    width = fields.Integer('العرض (%)', default=100)
    
    # Formatting
    format_string = fields.Char('نمط التنسيق',
                                help="مثل: %Y-%m-%d للتاريخ، {:.2f} للأرقام")
    prefix = fields.Char('بادئة', help="مثل: $, IQD")
    suffix = fields.Char('لاحقة')
    
    # Alignment
    alignment = fields.Selection([
        ('left', 'يسار'),
        ('center', 'وسط'),
        ('right', 'يمين'),
    ], default='left')
    
    # Style
    font_size = fields.Integer('حجم الخط', default=11)
    font_weight = fields.Selection([
        ('normal', 'عادي'),
        ('bold', 'عريض'),
    ], default='normal')
    color = fields.Char('اللون', default='#333333')


class CustomReportColumn(models.Model):
    """أعمدة جدول التقرير"""
    _name = 'custom.report.column'
    _description = 'Custom Report Table Column'
    _order = 'sequence, name'
    
    template_id = fields.Many2one('custom.report.template', 'القالب', required=True, ondelete='cascade')
    name = fields.Char('اسم العمود / Column Name', required=True, translate=True)
    technical_name = fields.Char('الاسم التقني', required=True,
                                 help="مثل: product_id.name, product_uom_qty")
    sequence = fields.Integer('الترتيب', default=10)
    width = fields.Integer('العرض (%)', default=10)
    visible = fields.Boolean('مرئي', default=True)
    
    # Alignment
    alignment = fields.Selection([
        ('left', 'يسار'),
        ('center', 'وسط'),
        ('right', 'يمين'),
    ], default='left')
    
    # Formatting
    is_monetary = fields.Boolean('مبلغ مالي', default=False)
    decimal_places = fields.Integer('الخانات العشرية', default=2)
    
    # Totals
    show_total = fields.Boolean('إظهار المجموع', default=False)
    total_function = fields.Selection([
        ('sum', 'مجموع'),
        ('avg', 'متوسط'),
        ('count', 'عدد'),
        ('min', 'أصغر قيمة'),
        ('max', 'أكبر قيمة'),
    ], string='دالة المجموع')


class CustomReportTotal(models.Model):
    """حقول المجاميع في التقرير"""
    _name = 'custom.report.total'
    _description = 'Custom Report Total Field'
    _order = 'sequence, name'
    
    template_id = fields.Many2one('custom.report.template', 'القالب', required=True, ondelete='cascade')
    name = fields.Char('الاسم / Label', required=True, translate=True)
    technical_name = fields.Char('الاسم التقني', required=True,
                                 help="مثل: amount_untaxed, amount_tax, amount_total")
    sequence = fields.Integer('الترتيب', default=10)
    visible = fields.Boolean('مرئي', default=True)
    
    # Style
    font_size = fields.Integer('حجم الخط', default=12)
    font_weight = fields.Selection([
        ('normal', 'عادي'),
        ('bold', 'عريض'),
    ], default='normal')
    color = fields.Char('اللون', default='#333333')


class CustomReportSection(models.Model):
    """أقسام إضافية في التقرير"""
    _name = 'custom.report.section'
    _description = 'Custom Report Section'
    _order = 'sequence, name'
    
    template_id = fields.Many2one('custom.report.template', 'القالب', required=True, ondelete='cascade')
    name = fields.Char('اسم القسم / Section Name', required=True, translate=True)
    sequence = fields.Integer('الترتيب', default=10)
    position = fields.Selection([
        ('before_table', 'قبل الجدول'),
        ('after_table', 'بعد الجدول'),
        ('before_totals', 'قبل المجاميع'),
        ('after_totals', 'بعد المجاميع'),
    ], string='الموضع', required=True, default='after_table')
    
    content_type = fields.Selection([
        ('html', 'HTML'),
        ('text', 'نص'),
        ('field', 'حقل'),
        ('table', 'جدول'),
    ], string='نوع المحتوى', required=True, default='text')
    
    content_html = fields.Html('محتوى HTML')
    content_text = fields.Text('محتوى نصي')
    content_field = fields.Char('حقل',
                                help="مثل: note, payment_term_id.note")
    
    visible = fields.Boolean('مرئي', default=True)
    height = fields.Integer('الارتفاع (px)', default=50)
    
    # Style
    background_color = fields.Char('لون الخلفية', default='#FFFFFF')
    border = fields.Boolean('حدود', default=False)
    border_color = fields.Char('لون الحدود', default='#DDDDDD')
    padding = fields.Integer('المسافة الداخلية (px)', default=10)

