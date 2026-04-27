# أمثلة متقدمة - مصمم التقارير
# Advanced Examples - Custom Report Designer

## 🎨 قوالب جاهزة متقدمة

### 1. فاتورة احترافية بالدينار العراقي

**الميزات:**
- ✅ ترويسة ملونة مع تدرج
- ✅ معلومات تفصيلية للعميل
- ✅ جدول بألوان متناوبة
- ✅ أيقونات للحقول
- ✅ خلفية شفافة
- ✅ علامة مائية "نسخة أصلية"

**الإعدادات:**
```python
{
    'name': 'فاتورة احترافية (دينار)',
    'code': 'PROF_INV_IQD',
    'report_type': 'sale_order',
    'language': 'ar_SA',
    'currency_id': IQD,
    
    # الترويسة
    'header_height': 120,
    'header_html': '''
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 20px; border-radius: 10px;">
            <div class="row">
                <div class="col-8">
                    <h2 style="margin: 0; color: white;">
                        <i class="fa fa-building"></i> 
                        <span t-field="doc.company_id.name"/>
                    </h2>
                    <p style="margin: 5px 0;">
                        <i class="fa fa-phone"></i> <span t-field="doc.company_id.phone"/>
                    </p>
                </div>
                <div class="col-4 text-right">
                    <img t-att-src="..." style="max-height: 80px; border-radius: 5px;"/>
                </div>
            </div>
        </div>
    ''',
    
    # العنوان
    'title_text': '🧾 فاتورة مبيعات',
    'title_font_size': 28,
    'title_color': '#667eea',
    
    # الجدول
    'table_header_bg': '#667eea',
    'table_header_color': '#FFFFFF',
    'alternate_row_colors': True,
    'row_color_1': '#FFFFFF',
    'row_color_2': '#F8F9FA',
    
    # العلامة المائية
    'watermark_text': 'نسخة أصلية',
    'watermark_angle': 45,
}
```

**الأعمدة:**
```
| # | 📦 المنتج | 📊 الكمية | 💰 السعر | 🏷️ الخصم | ✅ المجموع |
```

**قسم إضافي (بعد الجدول):**
```html
<div class="alert alert-info">
    <h5>📝 ملاحظات:</h5>
    <div t-field="doc.note"/>
</div>
```

---

### 2. عرض سعر أنيق بالدولار

**الميزات:**
- ✅ تصميم نظيف وأنيق
- ✅ صفحة أولى مختلفة عن الباقي
- ✅ QR Code للعرض
- ✅ شروط وأحكام
- ✅ صلاحية العرض

```python
{
    'name': 'Elegant Quotation (USD)',
    'code': 'ELEGANT_QUOTE_USD',
    'report_type': 'quotation',
    'language': 'en_US',
    'currency_id': USD,
    
    'title_text': '💼 Sales Quotation',
    'title_font_size': 32,
    'title_color': '#2C3E50',
    
    # Background
    'background_opacity': 0.03,
    'watermark_text': 'QUOTATION',
}
```

**أقسام إضافية:**

1. **قبل الجدول - Validity:**
```html
<div class="card" style="background: #E8F5E9; border-left: 4px solid #4CAF50; padding: 15px;">
    <strong>⏰ Validity:</strong> 
    <span t-field="doc.validity_date"/>
</div>
```

2. **بعد المجاميع - Terms:**
```html
<div class="mt-4" style="border-top: 2px dashed #ddd; padding-top: 15px;">
    <h5>📋 Terms &amp; Conditions</h5>
    <ul>
        <li>Payment: 50% advance, 50% on delivery</li>
        <li>Delivery: 7-14 business days</li>
        <li>Prices are subject to change without notice</li>
    </ul>
</div>
```

---

### 3. فاتورة POS مبسطة (إيصال حراري 80mm)

```python
{
    'name': 'إيصال POS حراري',
    'code': 'POS_THERMAL_80MM',
    'report_type': 'pos_order',
    'language': 'ar_SA',
    
    # ورق حراري 80mm
    'page_width': 80,
    'page_height': 210,  # طويل
    'margin_top': 5,
    'margin_bottom': 5,
    'margin_left': 5,
    'margin_right': 5,
    
    # بدون شعار (للسرعة)
    'show_logo': False,
    
    # عنوان صغير
    'title_font_size': 16,
    
    # جدول مبسط
    'table_font_size': 9,
    'table_row_height': 20,
}
```

**الأعمدة (مبسطة):**
```
| المنتج | الكمية | المبلغ |
```

---

### 4. تقرير شامل ثنائي اللغة (صفحات متعددة)

**الميزات:**
- ✅ ترويسة تتكرر في كل صفحة
- ✅ جدول طويل (100+ منتج)
- ✅ تقسيم تلقائي للصفحات
- ✅ أرقام صفحات
- ✅ معلومات تفصيلية

```python
{
    'name': 'تقرير شامل / Comprehensive Report',
    'code': 'COMPREHENSIVE_BILINGUAL',
    'report_type': 'sale_order',
    'language': 'both',
    
    # صفحات متعددة
    'repeat_header': True,
    'repeat_table_header': True,
    'max_rows_per_page': 25,  # 25 منتج لكل صفحة
    
    # ترويسة في كل صفحة
    'header_html': '''
        <div class="page-header">
            <table style="width: 100%;">
                <tr>
                    <td><img .../></td>
                    <td class="text-right">
                        <div t-field="doc.company_id.name"/>
                        <small t-field="doc.company_id.street"/>
                    </td>
                </tr>
            </table>
        </div>
    ''',
    
    # تذييل في كل صفحة
    'show_page_number': True,
    'footer_html': '''
        <div style="text-align: center; font-size: 10px; color: #888;">
            <div>صفحة <span class="page"/> من <span class="topage"/></div>
            <div>شكراً لتعاملكم معنا / Thank you for your business</div>
        </div>
    ''',
}
```

---

## 💰 تقارير متعددة العملات

### تقرير بالدولار والدينار معاً

```python
# قالب 1: بالدولار
template_usd = env['custom.report.template'].create({
    'name': 'Sales Invoice (USD)',
    'code': 'INV_USD',
    'currency_id': env.ref('base.USD').id,
})

# قالب 2: بالدينار
template_iqd = env['custom.report.template'].create({
    'name': 'فاتورة مبيعات (دينار)',
    'code': 'INV_IQD',
    'currency_id': env.ref('base.IQD').id,
})

# الاستخدام
if order.currency_id.name == 'USD':
    order.custom_report_template_id = template_usd
else:
    order.custom_report_template_id = template_iqd

order.action_print_custom_report()
```

---

## 🎯 حالات استخدام متقدمة

### 1. تقرير مختلف حسب الحالة

```python
# Quotation (Draft)
if order.state == 'draft':
    template = env['custom.report.template'].search([
        ('code', '=', 'QUOTE_DRAFT')
    ])
    # خلفية: شفافة
    # علامة مائية: "مسودة"

# Confirmed Order
elif order.state == 'sale':
    template = env['custom.report.template'].search([
        ('code', '=', 'ORDER_CONFIRMED')
    ])
    # خلفية: عادية
    # علامة مائية: بدون

order.custom_report_template_id = template
```

### 2. تقرير حسب العميل

```python
# عميل VIP - تقرير فاخر
if order.partner_id.category_id.name == 'VIP':
    template = env['custom.report.template'].search([
        ('code', '=', 'VIP_INVOICE')
    ])
    # شعار ذهبي
    # خلفية فاخرة
    # خط أكبر

# عميل عادي
else:
    template = env['custom.report.template'].search([
        ('code', '=', 'STANDARD_INVOICE')
    ])
```

### 3. تقرير حسب نوع الفاتورة

```python
# بناءً على invoice_type
invoice_types_templates = {
    '1': 'INV_STORE',       # زبون محل
    '2': 'INV_DELIVERY',    # شركات توصيل
    '3': 'INV_TRANSPORT',   # نقليات
    '6': 'INV_WHOLESALE',   # شورجة
}

template_code = invoice_types_templates.get(
    order.invoice_type, 
    'INV_DEFAULT'
)

template = env['custom.report.template'].search([
    ('code', '=', template_code)
])
```

---

## 📊 أمثلة CSS متقدمة

### تصميم حديث بالظلال

```css
.page {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.card {
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}

.product-table {
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-radius: 8px;
    overflow: hidden;
}

.product-table thead {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.totals {
    background: linear-gradient(to right, #f5f5f5, #ffffff);
    padding: 20px;
    border-radius: 8px;
    border-left: 4px solid #4A90E2;
}
```

### تصميم كلاسيكي رسمي

```css
.page {
    font-family: 'Times New Roman', serif;
    border: 2px solid #333;
    padding: 30px;
}

.header {
    border-bottom: 3px double #333;
    padding-bottom: 20px;
}

.product-table {
    border: 2px solid #333;
}

.product-table th {
    background: #333;
    color: white;
    font-weight: bold;
    text-transform: uppercase;
}

.footer {
    border-top: 3px double #333;
    padding-top: 20px;
    font-style: italic;
}
```

### تصميم ملون ومبهج

```css
:root {
    --primary: #FF6B6B;
    --secondary: #4ECDC4;
    --success: #95E1D3;
    --warning: #FFE66D;
}

.header {
    background: linear-gradient(45deg, var(--primary), var(--secondary));
    color: white;
    padding: 30px;
    border-radius: 15px 15px 0 0;
}

.product-table thead {
    background: var(--secondary);
}

.product-table tbody tr:hover {
    background: var(--success) !important;
    transform: scale(1.01);
    transition: all 0.3s;
}

.totals {
    background: linear-gradient(to bottom, var(--warning), #FFF);
    border-radius: 0 0 15px 15px;
}
```

---

## 🔧 أمثلة برمجية

### مثال 1: إنشاء قالب برمجياً

```python
# إنشاء القالب
template = env['custom.report.template'].create({
    'name': 'فاتورة مخصصة',
    'code': 'CUSTOM_INV_001',
    'report_type': 'sale_order',
    'language': 'ar_SA',
    'currency_id': env.ref('base.IQD').id,
    
    'title_text': 'فاتورة مبيعات رقم {doc.name}',
    'title_font_size': 26,
    'title_alignment': 'center',
    
    'show_header': True,
    'show_footer': True,
    'show_table': True,
    'show_totals': True,
    
    'watermark_text': 'نسخة أصلية',
    'watermark_angle': 45,
})

# إضافة الأعمدة
columns_data = [
    {'name': '#', 'technical_name': 'sequence', 'width': 5, 'alignment': 'center'},
    {'name': 'المنتج', 'technical_name': 'product_id.name', 'width': 35},
    {'name': 'الباركود', 'technical_name': 'product_id.barcode', 'width': 15},
    {'name': 'الكمية', 'technical_name': 'product_uom_qty', 'width': 10, 'alignment': 'center'},
    {'name': 'الوحدة', 'technical_name': 'product_uom.name', 'width': 10},
    {'name': 'السعر', 'technical_name': 'price_unit', 'width': 10, 'is_monetary': True},
    {'name': 'الخصم %', 'technical_name': 'discount', 'width': 8},
    {'name': 'المجموع', 'technical_name': 'price_subtotal', 'width': 12, 'is_monetary': True, 'show_total': True},
]

for seq, col_data in enumerate(columns_data, 1):
    env['custom.report.column'].create({
        'template_id': template.id,
        'sequence': seq,
        **col_data
    })

# إضافة المجاميع
totals_data = [
    {'name': 'المجموع الجزئي', 'technical_name': 'amount_untaxed'},
    {'name': 'الضريبة', 'technical_name': 'amount_tax'},
    {'name': 'الإجمالي', 'technical_name': 'amount_total', 'font_size': 16, 'font_weight': 'bold'},
]

for seq, total_data in enumerate(totals_data, 1):
    env['custom.report.total'].create({
        'template_id': template.id,
        'sequence': seq,
        **total_data
    })
```

### مثال 2: قالب ديناميكي حسب المبلغ

```python
def get_template_by_amount(order):
    """اختيار قالب حسب المبلغ"""
    
    if order.amount_total >= 100000:  # أكثر من 100,000
        # تقرير فاخر للصفقات الكبيرة
        code = 'HIGH_VALUE_INV'
    elif order.amount_total >= 10000:
        # تقرير متوسط
        code = 'MEDIUM_VALUE_INV'
    else:
        # تقرير بسيط
        code = 'STANDARD_INV'
    
    return env['custom.report.template'].search([('code', '=', code)])

# الاستخدام
template = get_template_by_amount(order)
order.custom_report_template_id = template
pdf = order.action_print_custom_report()
```

### مثال 3: معاينة جميع القوالب

```python
# الحصول على جميع القوالب
templates = env['custom.report.template'].search([('active', '=', True)])

# معاينة كل قالب
for template in templates:
    print(f"\n{'='*50}")
    print(f"القالب: {template.name}")
    print(f"الرمز: {template.code}")
    print(f"{'='*50}")
    
    # معاينة
    result = template.action_preview()
    print(f"✅ تم إنشاء PDF: {result['url']}")
```

---

## 📐 أمثلة للصفحات المتعددة

### تقرير بـ 50 منتج (صفحتين)

```python
template = env['custom.report.template'].create({
    'name': 'تقرير طويل',
    'code': 'LONG_REPORT',
    'max_rows_per_page': 25,  # 25 منتج لكل صفحة
    'repeat_header': True,    # تكرار الترويسة
    'repeat_table_header': True,  # تكرار رأس الجدول
})

# CSS للصفحات
template.custom_css = '''
@media print {
    .page {
        page-break-after: always;
    }
    
    .page:last-child {
        page-break-after: auto;
    }
    
    thead {
        display: table-header-group;
    }
}
'''
```

**النتيجة:**
```
صفحة 1:
- الترويسة
- العنوان
- معلومات العميل
- رأس الجدول
- المنتجات 1-25
- التذييل (صفحة 1 من 2)

صفحة 2:
- الترويسة (مكررة)
- رأس الجدول (مكرر)
- المنتجات 26-50
- المجاميع
- التذييل (صفحة 2 من 2)
```

---

## 🎨 تخصيصات متقدمة

### 1. شرط عرض (Conditions)

```python
# إظهار قسم "الخصم" فقط إذا كان هناك خصم
template.sections.create({
    'name': 'تفاصيل الخصم',
    'position': 'before_totals',
    'content_html': '''
        <div t-if="doc.amount_total != doc.amount_untaxed" 
             class="alert alert-success">
            <strong>🎉 تم تطبيق خصم!</strong>
            <div>نسبة الخصم: <t t-esc="((doc.amount_untaxed - doc.amount_total) / doc.amount_untaxed * 100)"/>%</div>
        </div>
    ''',
})
```

### 2. جدول مخصص (Products Grid)

```html
<!-- عرض المنتجات كـ Grid بدلاً من جدول -->
<div class="products-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
    <t t-foreach="doc.order_line" t-as="line">
        <div class="product-card" style="border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
            <img t-if="line.product_id.image_128" 
                 t-att-src="'data:image/png;base64,%s' % line.product_id.image_128.decode('utf-8')"
                 style="width: 100%; height: 150px; object-fit: cover;"/>
            <h6 t-field="line.product_id.name"/>
            <div>الكمية: <strong t-field="line.product_uom_qty"/></div>
            <div class="text-right" style="color: #4A90E2; font-size: 16px;">
                <strong t-field="line.price_subtotal"/>
            </div>
        </div>
    </t>
</div>
```

### 3. رسم بياني للمبيعات

```html
<div class="chart-section">
    <h5>📊 توزيع المبيعات</h5>
    <div class="progress" style="height: 30px;">
        <t t-foreach="doc.order_line[:5]" t-as="line">
            <div class="progress-bar" 
                 t-att-style="'width: %s%%;' % (line.price_subtotal / doc.amount_untaxed * 100)"
                 t-att-title="line.product_id.name">
                <t t-esc="'%.1f%%' % (line.price_subtotal / doc.amount_untaxed * 100)"/>
            </div>
        </t>
    </div>
</div>
```

---

## 🚀 نشر القوالب

### تصدير قالب

```python
# تصدير قالب كـ XML
template = env['custom.report.template'].browse(template_id)

# يمكن استخدام Odoo Export
# Settings → Technical → Database Structure → Export
```

### استيراد قالب

```python
# استيراد من XML أو CSV
# Settings → Technical → Database Structure → Import
```

---

**الآن لديك نظام كامل لإنشاء تقارير احترافية!** 🎉

**الملفات:** 6 ملفات Python + 2 XML + وثائق شاملة

