# POS System Design - Perfume Store
## نظام نقاط البيع - متجر العطور

---

## 📋 Overview | نظرة عامة

This is a complete Point of Sale (POS) system design specifically tailored for a perfume store business. The design features a modern, Excel-like interface for order management and a comprehensive product search system.

هذا تصميم كامل لنظام نقاط البيع (POS) مُصمم خصيصاً لمتجر عطور. يتميز التصميم بواجهة حديثة شبيهة بالإكسل لإدارة الطلبات ونظام بحث شامل للمنتجات.

---

## 🎯 Key Features | الميزات الرئيسية

### Left Section - Order Management (50%)
### القسم الأيسر - إدارة الطلبات (50%)

1. **Excel-like Order Table**
   - جدول طلبات شبيه بالإكسل
   - Fully editable cells (Product, Warehouse, Quantity, Price, Discount)
   - Auto-calculation of discounts and totals
   - Keyboard navigation (Tab, Enter, Arrow keys)
   - Row deletion with automatic renumbering
   - Real-time total calculations

2. **Order Header**
   - Customer selection dropdown
   - Automatic order number generation
   - Date and user information display

3. **Totals Section**
   - Subtotal calculation
   - Total discount display
   - Grand total in USD
   - Automatic conversion to Iraqi Dinar (IQD)

4. **Action Buttons**
   - 📋 Quotation - Create price quote
   - ✅ Sale Order - Confirm and invoice
   - 💾 Draft - Save as draft
   - 🚫 Cancel - Clear current order
   - 📱 WhatsApp - Send invoice via WhatsApp

### Right Section - Product Search (50%)
### القسم الأيمن - البحث عن المنتجات (50%)

1. **Filter Buttons**
   - Unit filters: 100ml, 50ml, 1 Kilo, 100gm
   - Brand filters: Givaudan, Royal Essence
   - All Products view

2. **Search Bar**
   - Real-time search as you type
   - Search by: Product name, Code, Barcode, Arabic name

3. **Product Table**
   - Displays: Code, Name (English & Arabic), Brand, Unit, Prices (USD & IQD)
   - Available stock quantity
   - Warehouse breakdown with quantities
   - Click to select, Double-click to add to order
   - Keyboard navigation (Arrow keys + Enter)

---

## 🛠️ Technical Specifications | المواصفات التقنية

### Design
- **Layout**: 50/50 split screen
- **Direction**: LTR (Left-to-Right) for English
- **Color Scheme**: Purple gradient theme (#714B67, #8B5A8E)
- **Responsive**: Fixed layout optimized for desktop POS terminals

### Technologies Used
- Pure HTML5
- CSS3 (Flexbox, Grid, Custom Scrollbars)
- Vanilla JavaScript (No frameworks)

### Browser Compatibility
- Chrome 90+
- Firefox 88+
- Edge 90+
- Safari 14+

---

## 💾 Demo Data | البيانات التجريبية

### Products (12 Perfume Items)
1. **PF001** - Vanilla Absolute | فانيليا مطلقة - Givaudan - 100ml - $45.00
2. **PF002** - Oud Wood Oriental | عود خشبي شرقي - Royal Essence - 50ml - $125.00
3. **PF003** - Rose Bulgarian Premium | ورد بلغاري فاخر - Givaudan - 100ml - $68.50
4. **PF004** - Musk White Crystal | مسك أبيض كريستال - Royal Essence - 1 Kilo - $280.00
5. **PF005** - Lavender French Pure | خزامى فرنسي نقي - Givaudan - 100ml - $32.75
6. **PF006** - Sandalwood Indian | صندل هندي - Royal Essence - 100gm - $95.00
7. **PF007** - Jasmine Egyptian Absolute | ياسمين مصري مطلق - Givaudan - 50ml - $78.50
8. **PF008** - Amber Golden Oriental | عنبر ذهبي شرقي - Royal Essence - 100ml - $58.25
9. **PF009** - Bergamot Italian Fresh | برغموت إيطالي طازج - Givaudan - 100ml - $42.00
10. **PF010** - Patchouli Dark Indonesia | باتشولي إندونيسي داكن - Royal Essence - 1 Kilo - $195.00
11. **PF011** - Citrus Lemon Fresh | حمضيات ليمون طازج - Givaudan - 100ml - $28.50
12. **PF012** - Frankincense Omani Pure | لبان عماني نقي - Royal Essence - 100gm - $115.00

### Warehouses
- **WH1** - Main Warehouse
- **WH2** - Secondary Warehouse
- **WH3** - Retail Store

### Exchange Rate
- **USD to IQD**: 1 USD = 1,300 IQD

---

## 🎮 How to Use | طريقة الاستخدام

### Opening the Design
1. Open `pos_design_mockup.html` in any modern web browser
2. The interface loads with demo data pre-filled

### Adding Products to Order
**Method 1: Double-Click**
- Double-click any product in the right table
- Product automatically fills the first empty row in order table

**Method 2: Keyboard**
1. Focus on search bar
2. Use ↑↓ arrow keys to select product
3. Press Enter to add to order

**Method 3: Manual Entry**
- Click any cell in the order table
- Type product name manually
- Enter quantity, price, and discount

### Editing Order Lines
- Click any cell to edit
- Press **Tab** to move to next cell
- Press **Enter** to move down to same column
- All calculations update automatically

### Calculations
- **After Discount** = Unit Price × (1 - Discount% / 100)
- **Total** = Quantity × After Discount
- **Grand Total** = Sum of all Totals - Total Discounts
- **IQD Total** = Grand Total × 1,300

### Deleting Rows
- Click the 🗑️ icon in the row
- Confirm deletion
- Row numbers automatically update

### Finalizing Order
1. Review all items and totals
2. Select customer from dropdown
3. Click appropriate action button:
   - **Quotation**: Save as price quote
   - **Sale Order**: Create confirmed order
   - **Draft**: Save for later
   - **Cancel**: Clear and start over
   - **WhatsApp**: Send to customer

---

## 🔄 Search & Filter

### Search Functionality
- Type in search bar
- Searches in: Product Code, English Name, Arabic Name, Brand
- Results filter in real-time
- Case-insensitive

### Filter Buttons
- Click any filter to show only matching products
- Active filter highlighted in purple
- "All Products" shows everything

---

## ⌨️ Keyboard Shortcuts

### In Order Table
- **Tab**: Next cell (horizontal)
- **Shift + Tab**: Previous cell (horizontal)
- **Enter**: Next row (vertical, same column)

### In Product Search
- **↑ (Up Arrow)**: Previous product
- **↓ (Down Arrow)**: Next product
- **Enter**: Add selected product to order

### General
- **Ctrl + F**: Focus search bar (browser default)
- **Esc**: Cancel current action

---

## 📱 Action Buttons Explained

### 📋 Quotation
- Creates a price quote document
- Order saved but not confirmed
- Can be edited later
- Usually sent to customer for approval

### ✅ Sale Order
- Confirms the order
- Generates invoice
- Updates inventory
- Creates accounting entries

### 💾 Draft
- Saves current order without confirming
- Can resume later
- Good for interrupted transactions
- Preserves all line items

### 🚫 Cancel
- Clears all order lines
- Resets to empty state
- Requires confirmation
- Cannot be undone

### 📱 WhatsApp
- Sends order/invoice to customer
- Opens WhatsApp interface
- Requires customer phone number
- Can send as PDF or text

---

## 🎨 Design Philosophy

### Color Coding
- **Purple (#714B67)**: Headers, primary actions
- **Green (#e8f5e9)**: Calculated discounts (After Disc)
- **Orange (#fff3e0)**: Total amounts
- **Gray (#f0f0f0)**: Row numbers (Excel-style)
- **Red (#f44336)**: Discounts, cancel actions
- **Blue (#2196F3)**: Quotation
- **Green (#4CAF50)**: Sale order confirmation
- **WhatsApp Green (#25D366)**: WhatsApp button

### Excel-like Features
- ✅ Grid layout with visible borders
- ✅ Row and column headers
- ✅ Cell focus with green highlight (#217346)
- ✅ Readonly cells with colored backgrounds
- ✅ Tab/Enter navigation
- ✅ Auto-calculation formulas
- ✅ Fixed header row
- ✅ Row numbering

---

## 🚀 Next Steps for Odoo Implementation

### Phase 1: Backend Models
1. Create `pos.perfume.order` model
2. Create `pos.perfume.order.line` model
3. Define product relationships
4. Set up warehouse stock integration

### Phase 2: Views
1. Convert HTML/CSS to Odoo QWeb templates
2. Create form views for order management
3. Implement search and filter views
4. Add kanban/list views for order overview

### Phase 3: JavaScript/OWL
1. Convert vanilla JS to Odoo OWL components
2. Implement real-time calculations
3. Add keyboard navigation handlers
4. Integrate with Odoo's POS framework

### Phase 4: Integration
1. Connect with inventory (stock) module
2. Link with accounting for invoicing
3. Integrate WhatsApp API
4. Set up customer management
5. Configure exchange rates

### Phase 5: Reports
1. Order/Invoice PDF templates
2. Sales reports
3. Inventory movement reports
4. Customer purchase history

---

## 📄 Files Included

```
pos_perfume_design/
├── pos_design_mockup.html          # Main design file (standalone demo)
├── README.md                        # This file (documentation)
├── SPECIFICATIONS.md               # Detailed technical specifications
├── IMPLEMENTATION_GUIDE.md         # Step-by-step Odoo implementation guide
└── TECHNICAL_NOTES.md              # Developer notes and considerations
```

---

## 🐛 Known Limitations (Demo Version)

1. **No Database**: All data is hardcoded in HTML
2. **No Persistence**: Refresh loses all changes
3. **No Authentication**: No user login system
4. **No Printing**: Print functionality not implemented
5. **Fixed Exchange Rate**: USD-IQD rate is hardcoded
6. **Limited Products**: Only 12 demo products
7. **No Stock Updates**: Adding to order doesn't reduce stock
8. **No Order History**: Can't view past orders

These will be resolved in the full Odoo implementation.

---

## 📞 Support & Questions

For questions about implementation or customization:
- Refer to `IMPLEMENTATION_GUIDE.md` for Odoo development
- Check `TECHNICAL_NOTES.md` for code explanations
- Review `SPECIFICATIONS.md` for detailed requirements

---

## 📝 Version History

### Version 1.0 (2025-10-22)
- Initial design completion
- Excel-like order table with full editing
- Product search with filters
- Real-time calculations
- Keyboard navigation
- Demo data for 12 perfume products
- English interface (LTR)
- Split-screen layout (50/50)

---

## 📜 License

This design is created for Lugal-AI Odoo implementation.
All rights reserved.

---

**Created**: October 22, 2025  
**Designer**: AI Assistant (Claude)  
**Client**: Lugal-AI  
**Purpose**: POS System for Perfume Store  
**Status**: Design Complete - Ready for Odoo Implementation

---

## 🌟 Design Highlights

> "An Excel-like interface that makes order entry feel natural and efficient."

> "Dual-language support (English/Arabic) for product names ensures accessibility."

> "Real-time calculations eliminate errors and speed up checkout."

> "Keyboard-first navigation allows experienced users to work quickly."

---

**End of README**









