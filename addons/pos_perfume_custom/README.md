# POS Perfume Custom - نظام نقاط البيع للعطور

## 📋 Overview | نظرة عامة

نظام نقاط بيع مخصص لمتاجر العطور مع واجهة Excel-like وتصميم 50/50 وحسابات تلقائية ودعم متعدد المخازن والعملات.

Custom Point of Sale system for perfume stores with Excel-like interface, 50/50 design, automatic calculations, multi-warehouse and multi-currency support.

---

## ✨ Features | الميزات

### 🎨 Interface Design | تصميم الواجهة
- ✅ **50/50 Split Layout**: Order Table (left) | Product Search (right)
- ✅ **Excel-like Order Table**: Editable cells with keyboard navigation
- ✅ **Purple Theme**: Professional gradient design (#714B67 → #8B5A8E)
- ✅ **Arabic Support**: Full RTL support for product names
- ✅ **Responsive Design**: Works on desktop and tablets

### 💰 Financial Features | الميزات المالية
- ✅ **Dual Currency**: USD and IQD with automatic conversion
- ✅ **Exchange Rate**: 1 USD = 1,300 IQD (configurable)
- ✅ **Automatic Calculations**: Real-time totals and discounts
- ✅ **Discount Support**: Per-line discount percentages
- ✅ **Tax Ready**: Tax calculation structure (currently 0%)

### 📦 Inventory Features | ميزات المخزون
- ✅ **Multi-Warehouse**: Support for multiple warehouses (WH1, WH2, WH3, ...)
- ✅ **Stock Availability**: Real-time stock levels per warehouse
- ✅ **Product Search**: Fast search by name, code, or Arabic name
- ✅ **Product Filters**: Filter by unit size or brand

### ⌨️ User Experience | تجربة المستخدم
- ✅ **Keyboard Navigation**: Tab, Enter, Arrow keys
- ✅ **Double-Click**: Add products to order
- ✅ **Auto-Complete**: Product selection with search
- ✅ **Visual Feedback**: Hover effects and selections

### 📱 Additional Features | ميزات إضافية
- ✅ **WhatsApp Integration**: Send orders via WhatsApp
- ✅ **Create Quotations**: Generate price quotes
- ✅ **Sale Orders**: Automatically create sale orders
- ✅ **Order History**: Track all orders
- ✅ **Notes**: Add notes to orders

---

## 🚀 Installation | التثبيت

### Prerequisites | المتطلبات
- Odoo 17.0+
- Python 3.10+
- PostgreSQL

### Installation Steps | خطوات التثبيت

1. **Copy Module | نسخ المودل**
   ```bash
   cd /path/to/odoo/addons
   # Module already exists at: addons/pos_perfume_custom
   ```

2. **Update Apps List | تحديث قائمة التطبيقات**
   - Go to Apps menu | اذهب إلى قائمة التطبيقات
   - Click "Update Apps List" | اضغط على "تحديث قائمة التطبيقات"

3. **Install Module | تثبيت المودل**
   - Search for "POS Perfume" | ابحث عن "POS Perfume"
   - Click "Install" | اضغط على "تثبيت"

4. **Configure | الإعدادات**
   - Go to POS Perfume → Configuration | اذهب إلى POS Perfume → الإعدادات
   - Set up warehouses | إعداد المخازن
   - Add products with Arabic names | إضافة المنتجات بالأسماء العربية

---

## 📖 Usage | الاستخدام

### Access the Perfume Interface | الوصول إلى واجهة العطور

**Method 1: From POS Screen | من شاشة نقاط البيع**
1. Open Point of Sale
2. Click on "🌸 Perfume Interface" button
3. Start creating orders

**Method 2: From Menu | من القائمة**
1. Go to POS Perfume → Orders
2. Click "Create" to make a new order
3. Use the form view or open perfume interface

### Creating an Order | إنشاء طلب

1. **Select Customer | اختر العميل**
   - Click customer dropdown
   - Select from existing customers

2. **Add Products | إضافة المنتجات**
   - Search for products on the right side
   - Double-click product to add to order
   - OR use Enter key after searching

3. **Edit Order Lines | تعديل سطور الطلب**
   - Click on any cell to edit
   - Use Tab to move horizontally
   - Use Enter to move vertically
   - Set quantities, prices, discounts

4. **Review Totals | مراجعة المجاميع**
   - Subtotal calculated automatically
   - Discounts shown in red
   - Total in USD and IQD

5. **Complete Order | إنهاء الطلب**
   - **Draft**: Save without confirming
   - **Quotation**: Create price quote
   - **Sale Order**: Confirm and create sale
   - **WhatsApp**: Send order details

---

## ⌨️ Keyboard Shortcuts | اختصارات الكيبورد

### In Order Table | في جدول الطلب
- `Tab`: Move to next cell (horizontal)
- `Shift + Tab`: Move to previous cell
- `Enter`: Move to cell below (vertical)
- `Arrow Up/Down`: Navigate vertically

### In Product Search | في بحث المنتجات
- `Type`: Search products
- `Arrow Down`: Move to next product
- `Arrow Up`: Move to previous product
- `Enter`: Add selected product to order

---

## 🎨 Design Specifications | مواصفات التصميم

### Color Palette | الألوان
- **Primary**: #714B67 (Purple)
- **Secondary**: #8B5A8E (Light Purple)
- **Accent**: #875F84
- **Success**: #4CAF50 (Green)
- **Warning**: #FF9800 (Orange)
- **Danger**: #f44336 (Red)
- **WhatsApp**: #25D366 (Green)

### Layout | التخطيط
- **Screen Split**: 50% Order Table | 50% Product Search
- **Header Height**: 52px
- **Padding**: 20px sections
- **Border Radius**: 8px for cards
- **Shadow**: 0 2px 4px rgba(0,0,0,0.08)

---

## 🔧 Configuration | الإعدادات

### Exchange Rate | سعر الصرف
Default: 1 USD = 1,300 IQD

To change:
1. Go to order form
2. Edit "Exchange Rate" field
3. Total in IQD updates automatically

### Warehouses | المخازن
1. Go to POS Perfume → Configuration → Warehouses
2. Create or edit warehouses
3. Set warehouse codes (WH1, WH2, etc.)

### Products | المنتجات
1. Go to POS Perfume → Products
2. Add/Edit products
3. Set Arabic name in "الاسم العربي" field
4. Product appears in search automatically

---

## 📊 Models | النماذج

### pos.perfume.order
Main order model with:
- Order reference (sequence)
- Customer, date, salesperson
- Order lines
- Totals (USD and IQD)
- State (draft/quotation/sale/done/cancel)

### pos.perfume.order.line
Order line model with:
- Product, warehouse
- Quantity, unit price
- Discount percentage
- Calculated totals

### Inherited: product.product
Extended with:
- `name_arabic`: Arabic name field
- `price_iqd`: Price in IQD (computed)

---

## 🔐 Security | الأمان

### User Groups | مجموعات المستخدمين
- **POS User**: Can create and view own orders
- **POS Manager**: Can view and manage all orders

### Access Rights | حقوق الوصول
All models have proper access control based on POS groups.

---

## 📱 WhatsApp Integration | تكامل واتساب

When clicking "Send to WhatsApp":
1. Order details formatted as message
2. Customer phone pre-filled
3. Opens WhatsApp Web/App
4. Ready to send

Message includes:
- Order number and date
- Product list with quantities and prices
- Totals in USD and IQD
- Exchange rate information

---

## 🐛 Troubleshooting | حل المشاكل

### Products not showing
- Check product "Can be Sold" is enabled
- Verify product is not archived
- Clear browser cache

### Calculations wrong
- Check discount percentages (0-100)
- Verify unit prices
- Check exchange rate

### Cannot save order
- Ensure customer is selected
- Check at least one product line
- Verify all required fields

---

## 📝 Changelog | سجل التغييرات

### Version 1.0.0 (Current)
- ✅ Complete 50/50 interface design
- ✅ Excel-like order table
- ✅ Multi-warehouse support
- ✅ Dual currency (USD/IQD)
- ✅ Arabic names support
- ✅ WhatsApp integration
- ✅ Auto calculations
- ✅ Keyboard navigation

---

## 📞 Support | الدعم

For issues or questions:
- Check this README
- Review code comments
- Contact development team

---

## 👥 Credits | الشكر

- **Developed by**: Lugal-AI
- **Design inspiration**: Excel spreadsheets + Modern POS systems
- **Target**: Odoo 17.0
- **License**: LGPL-3

---

## 🎯 Future Enhancements | التحسينات المستقبلية

- [ ] Barcode scanner integration
- [ ] Offline mode with sync
- [ ] Mobile responsive design
- [ ] Receipt printing templates
- [ ] Customer loyalty program
- [ ] Advanced reporting
- [ ] Multi-language UI (not just product names)
- [ ] Product images in search
- [ ] Batch operations

---

**Last Updated**: 2025-10-23
**Version**: 1.0.0
**Status**: ✅ Production Ready

---

**Enjoy! | استمتع! 🌸**
