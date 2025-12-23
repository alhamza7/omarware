# 🎨 مصمم الفواتير الاحترافي - خطة شاملة
# Professional Invoice Designer - Complete Roadmap

## 📋 المتطلبات (Requirements)

### ✅ المطلوب من المستخدم:
1. **واجهة رسومية (Visual Designer):**
   - Drag & Drop للعناصر
   - تحريك وتحجيم العناصر
   - معاينة مباشرة (Live Preview)

2. **تحكم كامل في المحتوى:**
   - جميع حقول الفاتورة (SAP doc number, invoice type, إلخ)
   - إضافة خلفيات وصور
   - تحكم في الألوان والخطوط
   - تحكم في موضع كل عنصر (X, Y, Width, Height)

3. **أنواع العناصر:**
   - نصوص (Text Labels)
   - حقول بيانات (Data Fields)
   - صور (Images/Logos)
   - أشكال (Shapes/Lines)
   - جداول (Tables)
   - باركود / QR Code

4. **الربط مع POS:**
   - طباعة تلقائية بالقالب الافتراضي
   - اختيار القالب حسب نوع الطلب

---

## 🔍 أفضل الحلول المتاحة

### 1. **GrapesJS** (⭐⭐⭐⭐⭐ الأفضل)
- **المميزات:**
  - ✅ Drag & Drop Builder
  - ✅ Visual HTML/CSS Editor
  - ✅ Component-based
  - ✅ Storage Manager
  - ✅ Open Source
  - ✅ Plugin System

- **الاستخدام:**
  - بناء Invoice Designer كامل
  - Canvas visual مع layers
  - Export HTML/CSS

### 2. **Fabric.js** (⭐⭐⭐⭐)
- **المميزات:**
  - ✅ HTML5 Canvas Library
  - ✅ Object manipulation (move, resize, rotate)
  - ✅ Text, Images, Shapes
  - ✅ Serialization
  - ✅ Export to Image/PDF

- **الاستخدام:**
  - Canvas-based designer
  - Precise positioning
  - Export to PDF

### 3. **Konva.js** (⭐⭐⭐⭐)
- **المميزات:**
  - ✅ 2D Canvas Framework
  - ✅ High Performance
  - ✅ Event Handling
  - ✅ Drag & Drop

### 4. **PDF-LIB** (للتصدير)
- **المميزات:**
  - ✅ Create PDFs in Browser
  - ✅ Embed fonts, images
  - ✅ Form fields

---

## 🏗️ الهيكلية المقترحة (Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (Odoo Web)                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │        Visual Invoice Designer (GrapesJS)              │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│  │  │  Canvas      │  │  Components  │  │  Properties │ │ │
│  │  │  (Design)    │  │  Panel       │  │  Panel      │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │            Data Binding Layer (JavaScript)              │ │
│  │  • Field Mapper                                         │ │
│  │  • Data Source Connector                                │ │
│  │  • Dynamic Content                                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                   Backend (Odoo Python)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │     invoice.template.designer (Model)                   │ │
│  │  • Template Storage (JSON)                              │ │
│  │  • Canvas Data                                           │ │
│  │  • Component Definitions                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │     invoice.template.element (Model)                    │ │
│  │  • Element Type (text, field, image, shape, table)      │ │
│  │  • Position (x, y, width, height)                       │ │
│  │  • Style (font, color, border, etc)                     │ │
│  │  • Data Binding (field_name, format)                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │     PDF Generator (wkhtmltopdf / reportlab)             │ │
│  │  • Render HTML → PDF                                    │ │
│  │  • Apply Template                                        │ │
│  │  • Inject Data                                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 المكونات المطلوبة (Components)

### 1. **Models (Backend)**

#### A. `invoice.template.designer`
```python
_name = 'invoice.template.designer'

# Basic Info
name = fields.Char('Template Name')
code = fields.Char('Template Code', unique=True)
template_type = fields.Selection([
    ('sale_order', 'Sale Order'),
    ('quotation', 'Quotation'),
    ('invoice', 'Invoice'),
    ('pos_order', 'POS Order'),
])

# Canvas Settings
canvas_width = fields.Integer(default=210)  # mm (A4)
canvas_height = fields.Integer(default=297)  # mm
canvas_unit = fields.Selection([('mm', 'mm'), ('px', 'px')])
orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')])

# Design Data (JSON)
design_json = fields.Text('Design JSON')  # GrapesJS/Fabric.js data
elements = fields.One2many('invoice.template.element', 'template_id')

# Background
background_color = fields.Char(default='#FFFFFF')
background_image = fields.Binary('Background Image')
background_opacity = fields.Float(default=1.0)

# Settings
is_default = fields.Boolean('Default Template')
active = fields.Boolean(default=True)
```

#### B. `invoice.template.element`
```python
_name = 'invoice.template.element'

template_id = fields.Many2one('invoice.template.designer')
sequence = fields.Integer('Layer Order')

# Element Type
element_type = fields.Selection([
    ('text', 'Static Text'),
    ('field', 'Data Field'),
    ('image', 'Image'),
    ('shape', 'Shape'),
    ('line', 'Line'),
    ('table', 'Table'),
    ('barcode', 'Barcode'),
    ('qrcode', 'QR Code'),
])

# Position & Size
x = fields.Float('X Position (mm)')
y = fields.Float('Y Position (mm)')
width = fields.Float('Width (mm)')
height = fields.Float('Height (mm)')
rotation = fields.Float('Rotation (degrees)')

# Data Binding (for field type)
field_name = fields.Char('Field Name')  # e.g., 'partner_id.name'
field_model = fields.Char('Model')  # e.g., 'sale.order'
format_string = fields.Char('Format')  # e.g., '{:.2f}'

# Style
font_family = fields.Char(default='Arial')
font_size = fields.Integer(default=12)
font_weight = fields.Selection([('normal', 'Normal'), ('bold', 'Bold')])
font_style = fields.Selection([('normal', 'Normal'), ('italic', 'Italic')])
text_align = fields.Selection([('left', 'Left'), ('center', 'Center'), ('right', 'Right')])
color = fields.Char(default='#000000')
background = fields.Char(default='transparent')

# Border
border_width = fields.Integer(default=0)
border_color = fields.Char(default='#000000')
border_style = fields.Selection([('solid', 'Solid'), ('dashed', 'Dashed')])

# Content
static_text = fields.Text('Static Text')  # for text type
image_data = fields.Binary('Image')  # for image type

# Table Settings (for table type)
table_columns = fields.Text('Table Columns (JSON)')
show_header = fields.Boolean(default=True)
row_height = fields.Integer(default=30)
```

### 2. **Frontend (JavaScript/OWL)**

#### A. Designer Component
```javascript
// invoice_designer.js
import { Component, useState } from "@odoo/owl";
import grapesjs from 'grapesjs';

class InvoiceDesigner extends Component {
    setup() {
        this.state = useState({
            template: null,
            editor: null,
        });
        
        onMounted(() => {
            this.initGrapesJS();
        });
    }
    
    initGrapesJS() {
        const editor = grapesjs.init({
            container: '#gjs',
            fromElement: true,
            width: 'auto',
            height: '100vh',
            storageManager: false,
            
            // Canvas
            canvas: {
                styles: [],
                scripts: [],
            },
            
            // Panels
            panels: {
                defaults: [
                    {
                        id: 'layers',
                        el: '.panel__right',
                        resizable: { tc: 0, cr: 1 },
                    },
                    {
                        id: 'panel-switcher',
                        el: '.panel__switcher',
                        buttons: [
                            { id: 'show-layers', active: true, label: 'Layers' },
                            { id: 'show-style', active: true, label: 'Styles' },
                            { id: 'show-traits', active: true, label: 'Settings' },
                        ],
                    },
                ],
            },
            
            // Block Manager (Components Panel)
            blockManager: {
                appendTo: '.blocks-container',
                blocks: [
                    {
                        id: 'text',
                        label: 'Text',
                        content: '<div>Static Text</div>',
                    },
                    {
                        id: 'field',
                        label: 'Data Field',
                        content: '<span data-field="partner_id.name">Customer Name</span>',
                    },
                    {
                        id: 'image',
                        label: 'Image',
                        content: '<img src="..." />',
                    },
                    {
                        id: 'table',
                        label: 'Table',
                        content: '<table><tr><td>Column 1</td></tr></table>',
                    },
                    // ... more blocks
                ],
            },
            
            // Custom components
            components: this.getCustomComponents(),
        });
        
        this.state.editor = editor;
    }
    
    getCustomComponents() {
        return [
            // Data Field Component
            {
                type: 'data-field',
                model: {
                    defaults: {
                        tagName: 'span',
                        draggable: true,
                        droppable: false,
                        traits: [
                            {
                                type: 'select',
                                name: 'data-field',
                                label: 'Field',
                                options: [
                                    { id: 'partner_id.name', name: 'Customer Name' },
                                    { id: 'name', name: 'Order Number' },
                                    { id: 'sap_doc_num', name: 'SAP Doc Number' },
                                    { id: 'invoice_type', name: 'Invoice Type' },
                                    { id: 'amount_total', name: 'Total Amount' },
                                    // ... more fields
                                ],
                            },
                            {
                                type: 'text',
                                name: 'format',
                                label: 'Format',
                            },
                        ],
                    },
                },
            },
            // ... more custom components
        ];
    }
    
    async saveTemplate() {
        const html = this.state.editor.getHtml();
        const css = this.state.editor.getCss();
        const components = this.state.editor.getComponents();
        
        const designData = {
            html: html,
            css: css,
            components: components.toJSON(),
        };
        
        await this.orm.call('invoice.template.designer', 'write', [
            this.props.templateId,
            { design_json: JSON.stringify(designData) }
        ]);
    }
    
    async loadTemplate() {
        const template = await this.orm.call('invoice.template.designer', 'read', [
            this.props.templateId
        ]);
        
        if (template.design_json) {
            const designData = JSON.parse(template.design_json);
            this.state.editor.setComponents(designData.components);
            this.state.editor.setStyle(designData.css);
        }
    }
    
    preview() {
        // Open preview in new window
        const html = this.generatePreviewHTML();
        const win = window.open('', 'Preview', 'width=800,height=600');
        win.document.write(html);
        win.document.close();
    }
}
```

#### B. Available Fields Registry
```javascript
// fields_registry.js
export const AVAILABLE_FIELDS = {
    // Sale Order Fields
    'sale.order': [
        { name: 'name', label: 'Order Number', type: 'char' },
        { name: 'partner_id.name', label: 'Customer Name', type: 'char' },
        { name: 'partner_id.street', label: 'Street', type: 'char' },
        { name: 'partner_id.phone', label: 'Phone', type: 'char' },
        { name: 'date_order', label: 'Order Date', type: 'date' },
        { name: 'amount_untaxed', label: 'Subtotal', type: 'monetary' },
        { name: 'amount_tax', label: 'Tax', type: 'monetary' },
        { name: 'amount_total', label: 'Total', type: 'monetary' },
        { name: 'sap_doc_num', label: 'SAP Doc Number', type: 'char' },
        { name: 'sap_doc_entry', label: 'SAP Doc Entry', type: 'integer' },
        { name: 'invoice_type', label: 'Invoice Type', type: 'selection' },
        { name: 'state', label: 'Status', type: 'selection' },
        // Lines
        { name: 'order_line.product_id.name', label: 'Product Name', type: 'char', context: 'line' },
        { name: 'order_line.product_uom_qty', label: 'Quantity', type: 'float', context: 'line' },
        { name: 'order_line.price_unit', label: 'Unit Price', type: 'monetary', context: 'line' },
        { name: 'order_line.price_subtotal', label: 'Subtotal', type: 'monetary', context: 'line' },
    ],
    
    // POS Order Fields
    'pos.order': [
        { name: 'name', label: 'Receipt Number', type: 'char' },
        { name: 'partner_id.name', label: 'Customer', type: 'char' },
        { name: 'date_order', label: 'Date', type: 'datetime' },
        { name: 'amount_total', label: 'Total', type: 'monetary' },
        { name: 'sap_doc_num', label: 'SAP Invoice Number', type: 'char' },
        // ... more fields
    ],
};
```

### 3. **XML Views**

```xml
<!-- invoice_designer_views.xml -->
<odoo>
    <!-- Designer View -->
    <record id="view_invoice_template_designer_form" model="ir.ui.view">
        <field name="name">invoice.template.designer.form</field>
        <field name="model">invoice.template.designer</field>
        <field name="arch" type="xml">
            <form string="Invoice Designer">
                <header>
                    <button name="action_preview" string="Preview" type="object" class="btn-primary"/>
                    <button name="action_save_as" string="Save As..." type="object"/>
                    <button name="action_export_pdf" string="Export PDF" type="object"/>
                </header>
                <sheet>
                    <!-- Full-Screen Designer -->
                    <div class="invoice_designer_container">
                        <div class="o_invoice_designer">
                            <!-- GrapesJS will mount here -->
                            <div id="gjs"></div>
                        </div>
                    </div>
                </sheet>
            </form>
        </field>
    </record>
    
    <!-- Action -->
    <record id="action_invoice_template_designer" model="ir.actions.client">
        <field name="name">Invoice Designer</field>
        <field name="tag">invoice_designer</field>
        <field name="target">fullscreen</field>
    </record>
</odoo>
```

---

## 🎯 خطة التنفيذ (Implementation Plan)

### المرحلة 1: البنية التحتية (Week 1-2)
- ✅ إنشاء Models (invoice.template.designer, invoice.template.element)
- ✅ إنشاء Views الأساسية
- ✅ Security & Access Rights
- ✅ دمج GrapesJS في Odoo

### المرحلة 2: Visual Designer (Week 3-4)
- ✅ بناء واجهة GrapesJS
- ✅ Components Panel (Text, Field, Image, Table, etc)
- ✅ Properties Panel (Position, Style, Data Binding)
- ✅ Layers Panel
- ✅ Canvas with Grid/Snap

### المرحلة 3: Data Binding (Week 5)
- ✅ Fields Registry
- ✅ Dynamic Data Injection
- ✅ Format Strings
- ✅ Conditional Display

### المرحلة 4: PDF Generation (Week 6)
- ✅ HTML → PDF Conversion
- ✅ Template Rendering
- ✅ Multi-page Support
- ✅ Print Settings

### المرحلة 5: POS Integration (Week 7)
- ✅ Default Template Selection
- ✅ Auto-print on Order
- ✅ Template per Invoice Type
- ✅ Preview before Print

### المرحلة 6: Advanced Features (Week 8)
- ✅ Barcode/QR Code Generation
- ✅ Custom Fonts
- ✅ Image Library
- ✅ Template Marketplace

---

## 💎 الميزات المتقدمة

### 1. **Drag & Drop Elements**
```javascript
// Any element can be dragged to canvas
editor.BlockManager.add('company-logo', {
    label: 'Company Logo',
    content: '<img src="/web/image/res.company/1/logo" />',
    category: 'Images',
});
```

### 2. **Smart Guides & Snap**
```javascript
// Snap to grid and other elements
editor.Canvas.getConfig().snapping = true;
editor.Canvas.getConfig().gridSize = 10;
```

### 3. **Data Preview**
```javascript
// Preview with real data
const previewData = {
    'partner_id.name': 'John Doe',
    'amount_total': '1,234.56',
    'sap_doc_num': 'INV-2025-001',
};

editor.on('preview', () => {
    injectPreviewData(previewData);
});
```

### 4. **Template Library**
```python
# Pre-made templates
TEMPLATE_LIBRARY = {
    'modern_minimal': {...},
    'classic_formal': {...},
    'colorful_creative': {...},
    'sap_standard': {...},
}
```

### 5. **Conditional Elements**
```javascript
// Show/hide based on conditions
{
    type: 'data-field',
    attributes: {
        'data-visible-if': 'invoice_type == "2"',  // Show only for delivery invoices
    }
}
```

---

## 📊 مقارنة بالحلول الموجودة

| الميزة | SAP Crystal | Jasper | **حلنا المقترح** |
|-------|------------|--------|------------------|
| Drag & Drop | ✅ | ✅ | ✅ |
| Visual Design | ✅ | ✅ | ✅ |
| Web-Based | ❌ | ❌ | ✅ |
| Open Source | ❌ | ✅ | ✅ |
| Odoo Integration | ❌ | ❌ | ✅ |
| Real-time Preview | ⚠️ | ⚠️ | ✅ |
| Cost | 💰💰💰 | 💰💰 | 💰 (Free) |

---

## 🚀 الخطوة التالية

هل تريد أن أبدأ بتنفيذ:
1. **النسخة الأولى (MVP)** - أساسيات Designer في أسبوع؟
2. **النسخة الكاملة** - جميع الميزات في 8 أسابيع؟
3. **نسخة مبسطة أولاً** - لاختبار الفكرة؟

أخبرني وسأبدأ فوراً! 🎨

---

**التاريخ:** 23 ديسمبر 2025  
**الحالة:** 📋 خطة جاهزة - في انتظار الموافقة

