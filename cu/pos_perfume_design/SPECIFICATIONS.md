# POS Perfume System - Detailed Specifications
## المواصفات التفصيلية لنظام نقاط البيع للعطور

---

## 📐 Layout Specifications | مواصفات التخطيط

### Screen Division
```
┌─────────────────────────────────────────────────────────────────┐
│                    Header (100% width)                          │
│  🛒 Point of Sale - Perfume Store    [User | Date | Time]      │
├──────────────────────────────┬──────────────────────────────────┤
│   LEFT SECTION (50%)         │   RIGHT SECTION (50%)            │
│   Order Management           │   Product Search                 │
│                              │                                  │
│  [Customer] [Order #]        │  [Filters: 100ml 50ml...]       │
│                              │                                  │
│  ┌─────────────────────┐    │  [Search Bar with Icon]         │
│  │  ORDER TABLE        │    │                                  │
│  │  Excel-like Grid    │    │  ┌──────────────────────┐       │
│  │  - Product          │    │  │  PRODUCTS TABLE      │       │
│  │  - Warehouse        │    │  │  - Code              │       │
│  │  - Quantity         │    │  │  - English Name      │       │
│  │  - Price            │    │  │  - Arabic Name       │       │
│  │  - Discount         │    │  │  - Brand             │       │
│  │  - Totals           │    │  │  - Unit              │       │
│  └─────────────────────┘    │  │  - Prices            │       │
│                              │  │  - Stock             │       │
│  [Subtotal]  [$XXX.XX]      │  │  - Warehouses        │       │
│  [Discount]  [-$XX.XX]      │  └──────────────────────┘       │
│  [Tax]       [$0.00]         │                                  │
│  [Total USD] [$XXX.XX]       │  (Scrollable)                   │
│  [Total IQD] [X,XXX IQD]     │                                  │
│                              │                                  │
│  [📋 Quote] [✅ Sale]        │                                  │
│  [💾 Draft] [🚫 Cancel]      │                                  │
│  [📱 WhatsApp (full width)]  │                                  │
└──────────────────────────────┴──────────────────────────────────┘
```

### Dimensions
- **Total Height**: 100vh (minus header ~52px)
- **Header Height**: 52px
- **Section Width**: 50% each
- **Section Padding**: 20px
- **Gap Between Elements**: 15px

---

## 🎨 Color Palette | لوحة الألوان

### Primary Colors
- **Primary Purple**: `#714B67`
- **Secondary Purple**: `#8B5A8E`
- **Dark Purple**: `#5a3a52`
- **Light Purple**: `#875F84`

### Functional Colors
- **Success Green**: `#4CAF50`
- **Info Blue**: `#2196F3`
- **Warning Orange**: `#FF9800`
- **Error Red**: `#f44336`
- **WhatsApp Green**: `#25D366`

### Background Colors
- **Main BG**: `#f9f9f9`
- **Section BG**: `#fafafa`
- **White**: `#ffffff`
- **Light Gray**: `#f0f0f0`
- **Border Gray**: `#e0e0e0`
- **Dark Border**: `#d0d0d0`

### Highlight Colors
- **Excel Focus**: `#217346` (Green outline)
- **Excel Selection**: `#fffacd` (Light yellow)
- **Discount BG**: `#e8f5e9` (Light green)
- **Total BG**: `#fff3e0` (Light orange)
- **Hover**: `#f8f3f7` (Light purple)
- **Selected**: `#e8d9e5` (Purple tint)

---

## 📝 Typography | الخطوط

### Font Family
```css
font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
```

### Font Sizes
- **Header Title**: 20px (bold 600)
- **Header Info**: 13px
- **Table Headers**: 13px (bold 600)
- **Table Content**: 13px
- **Buttons**: 15px (bold 600)
- **Totals Regular**: 14px
- **Grand Total**: 18px (bold)
- **IQD Total**: 16px (bold)
- **Filter Buttons**: 13px (medium 500)
- **Search Input**: 16px
- **Product Code**: 13px (bold 600)
- **Warehouse Badge**: 11px

---

## 📊 Table Specifications

### Order Table (Left Section)

#### Columns
| Column | Width | Type | Editable | Description |
|--------|-------|------|----------|-------------|
| # | 40px | Number | No | Row number (auto) |
| Product | 200px | Text | Yes | Product name |
| Warehouse | 100px | Select | Yes | WH1/WH2/WH3 |
| Quantity | 80px | Number | Yes | Order quantity |
| Unit Price | 100px | Number | Yes | Price per unit |
| Discount % | 90px | Number | Yes | 0-100% |
| After Disc | 100px | Number | No | Calculated |
| Total | 110px | Number | No | Calculated |
| ❌ | 50px | Button | No | Delete row |

#### Calculations
```javascript
After Discount = Unit Price × (1 - Discount% / 100)
Total = Quantity × After Discount
```

#### Row Styling
- **Header**: `#875F84` background, white text
- **Row Number**: `#f0f0f0` background, gray text, 2px border-right
- **Normal Cell**: White background, `#d0d0d0` border
- **Focus**: `#217346` outline, `#fffacd` background
- **Hover**: `#f9f9f9` background
- **Readonly (After Disc)**: `#e8f5e9` background
- **Readonly (Total)**: `#fff3e0` background, bold text

### Products Table (Right Section)

#### Columns
| Column | Width | Searchable | Sortable | Description |
|--------|-------|------------|----------|-------------|
| Code | 80px | Yes | Yes | Product code |
| Product Name | Auto | Yes | Yes | English name |
| Arabic Name | Auto | Yes | No | Arabic name |
| Brand | 100px | Yes | Yes | Givaudan/Royal Essence |
| Unit | 90px | Yes | Yes | 100ml, 50ml, etc. |
| Price (USD) | 90px | No | Yes | USD price |
| Price (IQD) | 110px | No | Yes | IQD price |
| Available | 80px | No | Yes | Total stock |
| Warehouses | 200px | No | No | Stock per warehouse |

#### Row Styling
- **Header**: `#714B67` background, white text, sticky
- **Row**: White background, `#f0f0f0` bottom border
- **Hover**: `#f8f3f7` background
- **Selected**: `#e8d9e5` background
- **Product Code**: `#714B67` color, bold

---

## 🔢 Calculations & Formulas

### Line Item Calculations
```javascript
// Per Line
quantity = user_input
unit_price = user_input
discount_percent = user_input (0-100)

after_discount = unit_price * (1 - discount_percent / 100)
line_total = quantity * after_discount
```

### Order Totals
```javascript
// Order Level
subtotal = sum(quantity * unit_price for all lines)
total_discount = sum((quantity * unit_price * discount_percent / 100) for all lines)
tax = 0  // Currently no tax
grand_total_usd = subtotal - total_discount + tax

// Exchange Rate
exchange_rate = 1300  // 1 USD = 1,300 IQD
grand_total_iqd = grand_total_usd * exchange_rate
```

---

## 🔍 Search & Filter Logic

### Search Algorithm
```javascript
search_term = user_input.toLowerCase()

for each product:
    searchable_text = concat(
        product.code,
        product.name_english,
        product.name_arabic,
        product.brand
    ).toLowerCase()
    
    if searchable_text.includes(search_term):
        show_product()
    else:
        hide_product()
```

### Filter Logic
```javascript
active_filter = clicked_filter

if active_filter == "All Products":
    show_all_products()
else if active_filter in ["100ml", "50ml", "1 Kilo", "100gm"]:
    filter_by_unit(active_filter)
else if active_filter in ["Givaudan", "Royal Essence"]:
    filter_by_brand(active_filter)
```

---

## ⌨️ Keyboard Navigation Map

### Order Table Navigation
```
     Tab →
┌────┬────────┬─────────┬──────┬───────┐
│ #  │ Name   │ Whse    │ Qty  │ Price │
├────┼────────┼─────────┼──────┼───────┤
│ 1  │ Prod A │ WH1 ←─→ │ 10   │ 45.00 │
│    │   ↕    │    ↕    │  ↕   │   ↕   │
│ 2  │ Prod B │ WH2     │ 5    │ 68.00 │
│    │        │         │      │       │
└────┴────────┴─────────┴──────┴───────┘
     ← Shift+Tab
     Enter = Move Down ↓
```

### Products Table Navigation
```
Search Bar: Type → ↓Arrow → ↑Arrow → Enter
```

---

## 🎯 Interactive Elements

### Buttons

#### Filter Buttons
```css
Default State:
  background: #f8f8f8
  border: 2px solid #e0e0e0
  padding: 10px 20px
  border-radius: 6px

Hover State:
  background: #714B67
  color: white

Active State:
  background: #714B67
  color: white
  border-color: #714B67
```

#### Action Buttons
```css
Base Style:
  padding: 15px
  border-radius: 8px
  font-size: 15px
  font-weight: 600

Hover Effect:
  transform: translateY(-2px)
  box-shadow: 0 4px 12px rgba(0,0,0,0.15)

Active Effect:
  transform: translateY(0)
```

### Input Fields

#### Text Input
```css
border: 1px solid #d0d0d0
padding: 8px
font-size: 13px
background: transparent

Focus:
  outline: 2px solid #217346
  background: #fffacd
```

#### Number Input
```css
text-align: right
(same as text input otherwise)
```

#### Select Dropdown
```css
width: 100%
padding: 8px
border: none
font-size: 13px
```

---

## 📱 Responsive Behavior

### Desktop (Primary Target)
- **Min Width**: 1280px
- **Optimal Width**: 1920px
- **Layout**: 50/50 split

### Tablet (Future)
- **Width**: 768px - 1279px
- **Layout**: Stack vertically
- **Order**: Search on top, Order below

### Mobile (Future)
- **Width**: < 768px
- **Layout**: Full-width tabs
- **Order**: Tab navigation

---

## 🔐 Data Validation

### Quantity Field
- **Type**: Positive integer
- **Min**: 1
- **Max**: 999,999
- **Step**: 1

### Unit Price Field
- **Type**: Decimal
- **Min**: 0.01
- **Max**: 999,999.99
- **Step**: 0.01
- **Decimals**: 2

### Discount Field
- **Type**: Decimal
- **Min**: 0
- **Max**: 100
- **Step**: 0.1
- **Decimals**: 1

### Product Name Field
- **Type**: Text
- **Max Length**: 200 characters
- **Required**: Yes

---

## 🔄 State Management

### Order States
1. **New**: Empty order, no lines
2. **Draft**: Order with lines, not confirmed
3. **Quotation**: Price quote created
4. **Sale Order**: Confirmed order
5. **Cancelled**: Order cancelled

### Row States
1. **Empty**: Placeholder row with empty fields
2. **Filled**: Row with product data
3. **Editing**: User is editing a cell
4. **Calculated**: After discount and total computed

---

## 📦 Data Models

### Product
```javascript
{
  code: String,        // "PF001"
  name_en: String,     // "Vanilla Absolute"
  name_ar: String,     // "فانيليا مطلقة"
  brand: String,       // "Givaudan"
  unit: String,        // "100ml"
  price_usd: Decimal,  // 45.00
  price_iqd: Integer,  // 58500
  stock_total: Integer, // 250
  warehouses: [
    {code: "WH1", qty: 120},
    {code: "WH2", qty: 80},
    {code: "WH3", qty: 50}
  ]
}
```

### Order Line
```javascript
{
  row_number: Integer,     // 1
  product_name: String,    // "Vanilla Absolute"
  warehouse: String,       // "WH1"
  quantity: Integer,       // 10
  unit_price: Decimal,     // 45.00
  discount_percent: Decimal, // 5.0
  after_discount: Decimal, // 42.75 (calculated)
  line_total: Decimal      // 427.50 (calculated)
}
```

### Order
```javascript
{
  order_number: String,    // "POS/2025/0001"
  customer: String,        // "Walk-in Customer"
  date: DateTime,          // 2025-10-22
  user: String,            // "John Smith"
  lines: [OrderLine],
  subtotal: Decimal,       // 1177.50
  total_discount: Decimal, // 66.75
  tax: Decimal,            // 0.00
  grand_total_usd: Decimal, // 1110.75
  grand_total_iqd: Integer, // 1443975
  state: String            // "draft", "quotation", "sale", "cancelled"
}
```

---

## 🌐 Internationalization

### Currency Display
- **USD**: `$XXX.XX` (2 decimals)
- **IQD**: `X,XXX IQD` (no decimals, comma separators)

### Number Formatting
- **Thousands Separator**: Comma (,)
- **Decimal Separator**: Period (.)

### Date Format
- **Display**: `YYYY-MM-DD`
- **Example**: `2025-10-22`

### Time Format
- **Display**: `HH:MM` (24-hour)
- **Example**: `14:30`

---

## 🚨 Error Handling

### Input Validation Errors
- **Negative Quantity**: Show alert "Quantity must be positive"
- **Invalid Price**: Show alert "Price must be greater than 0"
- **Discount > 100%**: Show alert "Discount cannot exceed 100%"

### System Errors
- **Product Not Found**: Highlight search bar in red
- **Row Deletion**: Require confirmation dialog
- **Order Cancellation**: Require confirmation dialog

---

## ⚡ Performance Specs

### Target Performance
- **Initial Load**: < 2 seconds
- **Search Response**: < 100ms
- **Calculation Update**: < 50ms
- **Row Addition**: < 100ms
- **Filter Toggle**: < 50ms

### Optimization Techniques
- Fixed table headers with `position: sticky`
- Virtual scrolling for large product lists (future)
- Debounced search input (future)
- Lazy loading of images (if added)

---

## 🔧 Browser Requirements

### Minimum Requirements
- **Chrome**: 90+
- **Firefox**: 88+
- **Edge**: 90+
- **Safari**: 14+

### Required Features
- CSS Grid & Flexbox support
- ES6 JavaScript
- LocalStorage (for future persistence)
- Keyboard events
- Mouse events

---

## 📋 Testing Checklist

### Functional Tests
- [ ] Search filters products correctly
- [ ] Filters work independently
- [ ] Double-click adds product to order
- [ ] Keyboard navigation works (Tab, Enter, Arrows)
- [ ] Calculations are accurate
- [ ] Row deletion works
- [ ] Order cancellation clears all fields
- [ ] All buttons respond correctly

### UI/UX Tests
- [ ] Layout renders correctly
- [ ] Colors match specifications
- [ ] Fonts are readable
- [ ] Hover effects work
- [ ] Focus states are visible
- [ ] Tables scroll smoothly
- [ ] Headers remain fixed on scroll

### Cross-Browser Tests
- [ ] Chrome functionality
- [ ] Firefox functionality
- [ ] Edge functionality
- [ ] Safari functionality

---

## 🎓 Accessibility

### Keyboard Access
- All interactive elements accessible via Tab
- Logical tab order
- Visible focus indicators
- Enter key activates buttons

### Screen Reader Support
- Semantic HTML5 elements
- ARIA labels (to be added in Odoo version)
- Table headers properly associated

### Visual
- High contrast ratios (WCAG AA compliant)
- Clear focus indicators
- Adequate font sizes
- Color is not the only indicator

---

## 🔮 Future Enhancements

### Phase 1 (Odoo Integration)
- Database connectivity
- User authentication
- Session management
- Order persistence

### Phase 2 (Advanced Features)
- Barcode scanner integration
- Receipt printing
- Multi-currency support
- Tax calculations
- Customer loyalty program

### Phase 3 (Mobile)
- Responsive mobile layout
- Touch gestures
- Mobile payment integration
- Offline mode with sync

---

**Document Version**: 1.0  
**Last Updated**: October 22, 2025  
**Status**: Complete - Ready for Development

---

**End of Specifications**











