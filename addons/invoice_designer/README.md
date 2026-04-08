# 🎨 Invoice Designer - Advanced Invoice Template Designer for Odoo

<div dir="rtl">

## نظام تصميم الفواتير المتقدم لـ Odoo

مصمم فواتير قوي وسهل الاستخدام يوفر واجهة مرئية كاملة (Visual Designer) لتصميم قوالب فواتير مخصصة بالكامل باستخدام تقنية السحب والإفلات (Drag & Drop).

</div>

---

## ✨ Key Features

### 🎯 Visual Drag & Drop Designer
- **Intuitive Interface**: Design invoices visually without writing code
- **Real-time Preview**: See changes instantly on the canvas
- **Zoom & Pan**: Navigate easily with zoom levels 50%-200%
- **Grid & Snap**: Precise alignment with grid guides and magnetic snap
- **Undo/Redo**: Full history support (up to 50 steps)

### 📦 10 Element Types
1. **Static Text**: Fixed text for titles and labels
2. **Dynamic Fields**: Data from system (customer name, date, totals, etc.)
3. **Images**: Logos, icons, and pictures
4. **Tables**: Product/order line tables
5. **Shapes**: Rectangles, circles, triangles, polygons
6. **Lines**: Separators and borders
7. **Barcodes**: Barcode generation from data
8. **QR Codes**: QR code generation
9. **Icons**: FontAwesome icons
10. **Gradient Boxes**: Colorful gradient backgrounds

### 🎨 Advanced Styling

#### Typography
- **9 Font Weights**: From Thin (100) to Black (900)
- **Multiple Fonts**: Including Arabic fonts (MCS Taybah, Cairo, Amiri)
- **Text Styles**: Normal, Italic, Oblique
- **Text Decoration**: Underline, Overline, Strike-through
- **Text Transform**: Uppercase, Lowercase, Capitalize
- **Text Alignment**: Left, Center, Right, Justify

#### Colors & Effects
- **Color Picker**: Hex color codes with visual picker
- **Transparency**: 0-100% opacity
- **Borders**: Width (0-20px), Style (solid, dashed, dotted, double)
- **Border Radius**: Rounded corners (0-100px)
- **Box Shadow**: Custom shadow effects
- **Gradients**: Linear and radial gradients

#### Position & Transform
- **Precise Positioning**: X, Y coordinates in millimeters
- **Sizing**: Width and height in millimeters
- **Rotation**: 0-360 degrees
- **Z-Index**: Layer ordering for overlapping elements

### 🔗 Full POS Perfume Integration
- **Direct Printing**: Print orders using custom templates
- **Template Selection**: Choose template per order
- **Quick Designer Access**: Open designer directly from order
- **Default Templates**: 2 ready-to-use templates included

---

## 📦 Installation

### Requirements
- Odoo 17.0+
- Python 3.10+
- Dependencies (automatically installed):
  - reportlab
  - qrcode
  - pillow

### Install via Odoo Apps

```bash
1. Copy module to Odoo addons folder
2. Update Apps List
3. Search for "Invoice Designer"
4. Click Install
```

### Install via Command Line

```bash
cd /path/to/odoo
./odoo-bin -c odoo.conf -d database_name -u invoice_designer
```

---

## 🚀 Quick Start

### 1. Open Designer

**From Invoice Designer Menu:**
```
Invoicing → Invoice Designer → Templates → [Select Template] → "Open Designer" Button
```

**From POS Perfume Order:**
```
POS Perfume → Orders → [Select Order] → "Open Designer" Button
```

### 2. Add Elements

Click **"Add"** button and choose:
- 📝 Static Text: For titles and labels
- 🔄 Dynamic Field: For data (e.g., customer name)
- 🖼️ Image: For logos
- 📊 Table: For product lists

### 3. Customize Properties

Use the **Properties Panel** on the right to adjust:
- Position (X, Y)
- Size (Width, Height)
- Font settings
- Colors
- Effects

### 4. Save & Print

Click **"Save"** button, then **"Print with Designer"** from the order.

---

## 📋 Available Dynamic Fields

### Order Information (POS Perfume)
```python
name                    # Invoice number
date                    # Date and time
partner_id.name         # Customer name
partner_id.street       # Customer address
partner_id.phone        # Customer phone
user_id.name            # User name
amount_subtotal         # Subtotal
amount_discount         # Discount
amount_tax              # Tax
amount_total            # Total
amount_total_iqd        # Total in IQD
exchange_rate           # Exchange rate
note                    # Notes
invoice_type            # Invoice type (1-8)
order_line_ids          # Order lines (for table)
```

### Company Information
```python
company_id.name         # Company name
company_id.logo         # Company logo
company_id.street       # Company address
company_id.phone        # Company phone
company_id.email        # Company email
company_id.website      # Company website
company_id.vat          # VAT number
```

### Field Formats
```python
# Numbers
%.2f                    # 2 decimal places (123.45)
%.0f                    # No decimals (123)
$%.2f                   # With dollar sign ($123.45)

# Dates
%Y-%m-%d                # 2024-12-24
%d/%m/%Y                # 24/12/2024
%Y-%m-%d %H:%M          # 2024-12-24 14:30
%d %B %Y                # 24 December 2024
```

---

## 🎨 Pre-built Templates

### 1. Classic Invoice Template ✨
- **Code**: `pos_perfume_classic`
- **Style**: Professional and elegant
- **Features**:
  - Company logo and info
  - Invoice title
  - Customer details
  - Product table
  - Totals section
  - Notes area
  - Footer

### 2. Modern Invoice Template 🎨
- **Code**: `pos_perfume_modern`
- **Style**: Contemporary with gradients
- **Features**:
  - Gradient header
  - Card-style information blocks
  - QR Code
  - Modern flat design
  - Shadow effects

---

## 🎓 Usage Examples

### Example 1: Add Company Logo

```python
1. Click "Add" → "Image"
2. In Properties Panel:
   - Name: "Company Logo"
   - X: 15mm, Y: 10mm
   - Width: 50mm, Height: 30mm
   - Field Name: company_id.logo
   - Object Fit: contain
```

### Example 2: Add Invoice Title

```python
1. Click "Add" → "Static Text"
2. Properties:
   - Content: "INVOICE"
   - X: 15mm, Y: 50mm
   - Width: 180mm
   - Font Size: 24pt
   - Font Weight: 700 (Bold)
   - Text Align: center
   - Color: #1a1a1a
```

### Example 3: Add Invoice Number (Dynamic)

```python
1. Click "Add" → "Dynamic Field"
2. Properties:
   - Field Name: name
   - X: 15mm, Y: 68mm
   - Font Size: 12pt
   - Font Weight: 600 (Semi Bold)
   - Color: #333333
```

### Example 4: Add Product Table

```python
1. Click "Add" → "Table"
2. Properties:
   - Field Name: order_line_ids
   - X: 15mm, Y: 95mm
   - Width: 180mm, Height: 120mm
   - Border Width: 1px
   - Border Style: solid
   - Border Color: #dddddd
```

### Example 5: Add Gradient Header

```python
1. Click "Add" → "Gradient Box"
2. Properties:
   - X: 0mm, Y: 0mm
   - Width: 210mm, Height: 60mm
   - Background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
   - Z-Index: 1
```

---

## 🛠️ Technical Details

### Architecture
```
invoice_designer/
├── models/
│   ├── invoice_template_designer.py    # Main template model
│   ├── invoice_template_element.py     # Element model (10 types)
│   ├── invoice_template_font.py        # Font management
│   └── sale_order_integration.py       # POS integration
├── static/
│   ├── src/
│   │   ├── js/
│   │   │   └── invoice_designer.js     # Visual designer (OWL)
│   │   ├── css/
│   │   │   └── invoice_designer.css    # Designer styles
│   │   └── xml/
│   │       └── invoice_designer.xml    # Designer template
│   └── description/
│       └── icon.png
├── views/
│   ├── invoice_designer_views.xml      # Backend views
│   └── invoice_designer_minimal.xml    # Action definitions
├── security/
│   ├── ir.model.access.csv
│   └── invoice_designer_security.xml
└── __manifest__.py
```

### Database Models

#### invoice.template.designer
- **Purpose**: Store template definitions
- **Key Fields**: name, code, template_type, page settings, background
- **Methods**: action_open_visual_designer(), generate_invoice_pdf()

#### invoice.template.element
- **Purpose**: Store template elements
- **Key Fields**: element_type, x, y, width, height, content, styling
- **Types**: text, field, image, table, shape, line, barcode, qr, icon, gradient_box

---

## 🔌 API Reference

### Generate PDF from Template

```python
# Get template
template = self.env['invoice.template.designer'].browse(template_id)

# Generate PDF for an order
pdf_data = template.generate_invoice_pdf(
    order_id=order.id,
    model_name='pos.perfume.order'
)

# Return as download
return {
    'type': 'ir.actions.act_url',
    'url': f'/web/content/...?download=true',
    'target': 'new',
}
```

### Open Designer Programmatically

```python
# From any model
template = self.env['invoice.template.designer'].browse(template_id)
return template.action_open_visual_designer()
```

---

## 🎨 Color Palette

### Professional Color Schemes

```css
Primary:       #667eea (Purple)
Secondary:     #764ba2 (Violet)
Success:       #5cb85c (Green)
Danger:        #d9534f (Red)
Text:          #1a1a1a (Almost Black)
Text Secondary:#666666 (Gray)
Border:        #dddddd (Light Gray)
Background:    #f8f9fa (Very Light Gray)
```

### Ready-to-use Gradients

```css
Purple → Violet:
  linear-gradient(135deg, #667eea 0%, #764ba2 100%)

Blue → Cyan:
  linear-gradient(135deg, #00b4db 0%, #0083b0 100%)

Orange → Pink:
  linear-gradient(135deg, #ff6a00 0%, #ee0979 100%)

Yellow → Orange:
  linear-gradient(135deg, #f7b733 0%, #fc4a1a 100%)
```

---

## 🐛 Troubleshooting

### Issue 1: Element Not Visible
**Solution:**
- Check Z-Index (may be behind another element)
- Check color (may match background)
- Check opacity

### Issue 2: Text Truncated
**Solution:**
- Increase element width or height
- Reduce font size
- Increase line height

### Issue 3: Image Not Showing
**Solution:**
- Verify image upload
- Check image URL
- Use Object Fit: contain or cover

### Issue 4: Table Empty
**Solution:**
- Field name must be: `order_line_ids`
- Ensure order has lines

### Issue 5: Dynamic Field Not Working
**Solution:**
- Check field name (case sensitive)
- Use dot notation for related fields: `partner_id.name`
- Verify field format

---

## 📚 Documentation

- **Complete Guide (Arabic)**: [INVOICE_DESIGNER_COMPLETE_GUIDE_AR.md](INVOICE_DESIGNER_COMPLETE_GUIDE_AR.md)
- **Quick Start (Arabic)**: [QUICK_START_AR.md](QUICK_START_AR.md)
- **Complete Features**: [COMPLETE_FEATURES_AR.md](COMPLETE_FEATURES_AR.md)

---

## 🔄 Updates & Roadmap

### Version 1.0 (Current)
- ✅ Visual drag & drop designer
- ✅ 10 element types
- ✅ Advanced styling options
- ✅ POS Perfume integration
- ✅ 2 pre-built templates
- ✅ Full Arabic support

### Version 1.1 (Planned)
- [ ] Import/Export templates (JSON/XML)
- [ ] Template library
- [ ] Direct HTML/CSS editing
- [ ] Live preview with real data
- [ ] Copy/Paste elements
- [ ] Element grouping
- [ ] Version control

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This module is licensed under LGPL-3.

---

## 👥 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the complete documentation
3. Contact technical support

---

## 📞 Contact

**Developer**: Capo Development Team  
**Email**: support@example.com  
**Website**: https://example.com

---

<div dir="rtl" align="center">

**صُنع بحب ❤️ في العراق 🇮🇶**

**Made with Love in Iraq**

</div>

---

## ⭐ If you like this module, please give it a star!


