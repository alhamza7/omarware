# Technical Notes & Developer Documentation
## الملاحظات التقنية ووثائق المطورين

---

## 📖 Introduction

This document contains technical notes, code explanations, and development considerations for the POS Perfume System.

---

## 🏗️ Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Frontend (Browser)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  OWL         │  │  JavaScript  │  │  CSS/SCSS    │         │
│  │  Components  │  │  Models      │  │  Styles      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ↕ HTTP/JSON-RPC
┌─────────────────────────────────────────────────────────────────┐
│                       Odoo Backend (Python)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Models      │  │  Controllers │  │  Services    │         │
│  │  (ORM)       │  │  (Routes)    │  │  (Business)  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ↕ SQL
┌─────────────────────────────────────────────────────────────────┐
│                       PostgreSQL Database                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Orders      │  │  Order Lines │  │  Products    │         │
│  │  Partners    │  │  Stock       │  │  ...more     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💾 Database Schema

### Main Tables

```sql
-- pos_perfume_order
CREATE TABLE pos_perfume_order (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    date TIMESTAMP NOT NULL,
    user_id INTEGER REFERENCES res_users(id),
    partner_id INTEGER REFERENCES res_partner(id),
    state VARCHAR(20),
    amount_subtotal NUMERIC(16, 2),
    amount_discount NUMERIC(16, 2),
    amount_tax NUMERIC(16, 2),
    amount_total NUMERIC(16, 2),
    amount_total_iqd NUMERIC(16, 2),
    exchange_rate NUMERIC(12, 2),
    sale_order_id INTEGER REFERENCES sale_order(id),
    create_date TIMESTAMP,
    write_date TIMESTAMP,
    create_uid INTEGER REFERENCES res_users(id),
    write_uid INTEGER REFERENCES res_users(id)
);

-- pos_perfume_order_line
CREATE TABLE pos_perfume_order_line (
    id SERIAL PRIMARY KEY,
    sequence INTEGER,
    order_id INTEGER REFERENCES pos_perfume_order(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES product_product(id),
    warehouse_id INTEGER REFERENCES stock_warehouse(id),
    quantity NUMERIC(16, 2),
    unit_price NUMERIC(16, 2),
    discount_percent NUMERIC(5, 2),
    price_after_discount NUMERIC(16, 2),
    line_subtotal NUMERIC(16, 2),
    discount_amount NUMERIC(16, 2),
    line_total NUMERIC(16, 2),
    create_date TIMESTAMP,
    write_date TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_pos_order_date ON pos_perfume_order(date);
CREATE INDEX idx_pos_order_state ON pos_perfume_order(state);
CREATE INDEX idx_pos_order_partner ON pos_perfume_order(partner_id);
CREATE INDEX idx_pos_line_order ON pos_perfume_order_line(order_id);
CREATE INDEX idx_pos_line_product ON pos_perfume_order_line(product_id);
```

---

## 🔄 Data Flow

### Creating a New Order

```
1. User opens POS interface
   ↓
2. Frontend loads product catalog
   ├─ GET /web/dataset/call_kw/product.product/search_read
   └─ Returns: Products with stock info
   ↓
3. User searches/selects products
   ├─ JavaScript filters products locally
   └─ Double-click adds to order
   ↓
4. Order lines updated in frontend state
   ├─ Calculations performed in JavaScript
   └─ Totals updated in real-time
   ↓
5. User clicks "Confirm Sale"
   ├─ POST /web/dataset/call_button
   ├─ Creates pos.perfume.order record
   ├─ Creates pos.perfume.order.line records
   ├─ Creates linked sale.order
   ├─ Updates stock (via sale order confirmation)
   └─ Returns: Order ID and Sale Order ID
   ↓
6. Success message displayed
   └─ Option to print/send WhatsApp
```

---

## 🧮 Calculation Logic

### Line Item Calculations

```python
# In pos_perfume_order_line.py
@api.depends('quantity', 'unit_price', 'discount_percent')
def _compute_amounts(self):
    for line in self:
        # Step 1: Calculate price after discount
        price_after_discount = line.unit_price * (1 - line.discount_percent / 100)
        
        # Step 2: Calculate line subtotal (before discount)
        line_subtotal = line.quantity * line.unit_price
        
        # Step 3: Calculate discount amount
        discount_amount = line_subtotal * (line.discount_percent / 100)
        
        # Step 4: Calculate line total (after discount)
        line_total = line.quantity * price_after_discount
        
        # Update fields
        line.update({
            'price_after_discount': price_after_discount,
            'line_subtotal': line_subtotal,
            'discount_amount': discount_amount,
            'line_total': line_total,
        })
```

### Order Totals Calculation

```python
# In pos_perfume_order.py
@api.depends('order_line_ids.line_subtotal', 'order_line_ids.discount_amount')
def _compute_amounts(self):
    for order in self:
        amount_subtotal = 0.0
        amount_discount = 0.0
        amount_tax = 0.0  # Currently not implemented
        
        # Sum all lines
        for line in order.order_line_ids:
            amount_subtotal += line.line_subtotal
            amount_discount += line.discount_amount
        
        # Calculate totals
        order.amount_subtotal = amount_subtotal
        order.amount_discount = amount_discount
        order.amount_tax = amount_tax
        order.amount_total = amount_subtotal - amount_discount + amount_tax

@api.depends('amount_total', 'exchange_rate')
def _compute_amount_iqd(self):
    for order in self:
        order.amount_total_iqd = order.amount_total * order.exchange_rate
```

---

## 🎨 Frontend JavaScript Logic

### State Management

```javascript
// Using OWL's useState hook
setup() {
    this.state = useState({
        order: {
            id: null,
            partner_id: null,
            date: new Date(),
            lines: [],
            totals: {
                subtotal: 0,
                discount: 0,
                tax: 0,
                total_usd: 0,
                total_iqd: 0,
            }
        },
        products: [],
        searchTerm: '',
        activeFilter: 'all',
    });
}
```

### Excel-like Navigation

```javascript
// Keyboard event handler
handleKeyDown(event) {
    const currentCell = event.target;
    const currentRow = currentCell.closest('tr');
    const allCells = Array.from(currentRow.querySelectorAll('td'));
    const currentIndex = allCells.indexOf(currentCell.closest('td'));
    
    switch(event.key) {
        case 'Tab':
            // Default browser behavior (horizontal navigation)
            break;
            
        case 'Enter':
            event.preventDefault();
            // Move to next row, same column
            const nextRow = currentRow.nextElementSibling;
            if (nextRow) {
                const nextCell = nextRow.querySelectorAll('td')[currentIndex];
                const input = nextCell.querySelector('input, select');
                if (input) input.focus();
            }
            break;
            
        case 'ArrowDown':
            event.preventDefault();
            // Move down
            this.moveVertical(currentRow, currentIndex, 1);
            break;
            
        case 'ArrowUp':
            event.preventDefault();
            // Move up
            this.moveVertical(currentRow, currentIndex, -1);
            break;
    }
}

moveVertical(currentRow, cellIndex, direction) {
    const targetRow = direction > 0 
        ? currentRow.nextElementSibling 
        : currentRow.previousElementSibling;
        
    if (targetRow) {
        const targetCell = targetRow.querySelectorAll('td')[cellIndex];
        const input = targetCell.querySelector('input, select');
        if (input) input.focus();
    }
}
```

### Real-time Calculations

```javascript
// Calculate line totals
calculateLineTotal(line) {
    const qty = parseFloat(line.quantity) || 0;
    const price = parseFloat(line.unit_price) || 0;
    const discount = parseFloat(line.discount_percent) || 0;
    
    line.price_after_discount = price * (1 - discount / 100);
    line.line_subtotal = qty * price;
    line.discount_amount = line.line_subtotal * (discount / 100);
    line.line_total = qty * line.price_after_discount;
    
    return line;
}

// Calculate order totals
calculateOrderTotals() {
    const totals = {
        subtotal: 0,
        discount: 0,
        tax: 0,
        total_usd: 0,
        total_iqd: 0,
    };
    
    this.state.order.lines.forEach(line => {
        totals.subtotal += line.line_subtotal;
        totals.discount += line.discount_amount;
    });
    
    totals.total_usd = totals.subtotal - totals.discount + totals.tax;
    totals.total_iqd = totals.total_usd * this.state.order.exchange_rate;
    
    this.state.order.totals = totals;
}

// Auto-update on any line change
onLineChange(lineIndex, field, value) {
    this.state.order.lines[lineIndex][field] = value;
    this.state.order.lines[lineIndex] = this.calculateLineTotal(
        this.state.order.lines[lineIndex]
    );
    this.calculateOrderTotals();
}
```

---

## 🔍 Search & Filter Implementation

### Product Search

```javascript
// Search functionality
filterProducts() {
    const searchTerm = this.state.searchTerm.toLowerCase();
    const filter = this.state.activeFilter;
    
    return this.state.products.filter(product => {
        // Text search
        const matchesSearch = !searchTerm || (
            product.code.toLowerCase().includes(searchTerm) ||
            product.name_en.toLowerCase().includes(searchTerm) ||
            product.name_ar.includes(searchTerm) ||
            product.brand.toLowerCase().includes(searchTerm)
        );
        
        // Filter by unit or brand
        let matchesFilter = true;
        if (filter !== 'all') {
            if (['100ml', '50ml', '1 Kilo', '100gm'].includes(filter)) {
                matchesFilter = product.unit === filter;
            } else if (['Givaudan', 'Royal Essence'].includes(filter)) {
                matchesFilter = product.brand === filter;
            }
        }
        
        return matchesSearch && matchesFilter;
    });
}
```

### Optimized Search with Debouncing

```javascript
// Debounce search input to avoid excessive filtering
import { debounce } from "@web/core/utils/timing";

setup() {
    this.debouncedSearch = debounce(this.performSearch, 300);
}

onSearchInput(event) {
    this.state.searchTerm = event.target.value;
    this.debouncedSearch();
}

performSearch() {
    // Actual search logic
    this.state.filteredProducts = this.filterProducts();
}
```

---

## 🔐 Security Considerations

### Input Validation

```python
# Server-side validation in models
@api.constrains('quantity')
def _check_quantity(self):
    for line in self:
        if line.quantity <= 0:
            raise ValidationError(_('Quantity must be positive.'))

@api.constrains('discount_percent')
def _check_discount(self):
    for line in self:
        if line.discount_percent < 0 or line.discount_percent > 100:
            raise ValidationError(_('Discount must be between 0 and 100%.'))

@api.constrains('unit_price')
def _check_price(self):
    for line in self:
        if line.unit_price < 0:
            raise ValidationError(_('Price cannot be negative.'))
```

### Access Rights

```xml
<!-- Record rules for multi-company -->
<record id="pos_perfume_order_rule" model="ir.rule">
    <field name="name">POS Order: see own orders</field>
    <field name="model_id" ref="model_pos_perfume_order"/>
    <field name="domain_force">[('user_id','=',user.id)]</field>
    <field name="groups" eval="[(4, ref('group_pos_perfume_user'))]"/>
</record>

<record id="pos_perfume_order_rule_manager" model="ir.rule">
    <field name="name">POS Order: managers see all</field>
    <field name="model_id" ref="model_pos_perfume_order"/>
    <field name="domain_force">[(1,'=',1)]</field>
    <field name="groups" eval="[(4, ref('group_pos_perfume_manager'))]"/>
</record>
```

---

## ⚡ Performance Optimization

### Database Optimization

```python
# Use read_group for better performance
@api.model
def get_orders_summary(self):
    """Get order statistics efficiently"""
    return self.read_group(
        domain=[],
        fields=['state', 'amount_total:sum'],
        groupby=['state']
    )

# Prefetch related records
orders = self.env['pos.perfume.order'].search([
    ('state', '=', 'draft')
]).with_context(prefetch_fields=True)

# Use lazy='load' for large datasets
order_lines = self.env['pos.perfume.order.line'].search([
    ('order_id', 'in', order_ids)
], order='sequence', lazy='load')
```

### Frontend Optimization

```javascript
// Virtual scrolling for large product lists
import { useVirtualScroll } from "@web/core/virtual_scroll";

setup() {
    this.virtualScroll = useVirtualScroll({
        itemHeight: 50,
        containerHeight: 600,
        items: computed(() => this.getFilteredProducts()),
    });
}

// Memoize expensive calculations
import { useMemo } from "@odoo/owl";

get filteredProducts() {
    return useMemo(() => {
        return this.filterProducts();
    }, [this.state.products, this.state.searchTerm, this.state.activeFilter]);
}
```

---

## 🐛 Debugging Tips

### Enable Debug Mode

```python
# In models
import logging
_logger = logging.getLogger(__name__)

def action_confirm(self):
    _logger.info(f"Confirming order {self.name}")
    _logger.debug(f"Order lines: {[(l.product_id.name, l.quantity) for l in self.order_line_ids]}")
    # ... rest of method
```

### JavaScript Console Debugging

```javascript
// Enable detailed logging
console.group('Order Calculation');
console.log('Lines:', this.state.order.lines);
console.log('Totals before:', this.state.order.totals);
this.calculateOrderTotals();
console.log('Totals after:', this.state.order.totals);
console.groupEnd();

// Breakpoint helper
debugger; // Pauses execution in browser
```

### SQL Query Debugging

```python
# Enable SQL logging in odoo.conf
[options]
log_level = debug_sql
log_handler = :DEBUG

# Or programmatically
self.env.cr.execute("SELECT * FROM pos_perfume_order WHERE id = %s", (order_id,))
_logger.debug("SQL: %s", self.env.cr.query)
```

---

## 📊 Performance Benchmarks

### Target Performance Metrics

| Operation | Target Time | Notes |
|-----------|-------------|-------|
| Load POS interface | < 2s | Initial page load |
| Product search (1000 items) | < 100ms | Client-side filtering |
| Add product to order | < 50ms | Pure JavaScript |
| Recalculate totals | < 20ms | 10 lines or less |
| Save order (backend) | < 500ms | Database write |
| Confirm & create sale | < 1s | Multiple DB operations |
| Load order history | < 300ms | With pagination |

### Optimization Checklist

- [x] Database indexes on frequently queried fields
- [x] Computed fields with `store=True` for heavy calculations
- [ ] Redis caching for product catalog (future)
- [ ] Lazy loading for order lines
- [x] Frontend state management to minimize re-renders
- [ ] Service Worker for offline capability (future)
- [x] Debounced search input
- [ ] Virtual scrolling for large lists (future)

---

## 🔄 State Machine Diagram

```
Order State Flow:

    ┌──────┐
    │ New  │
    └──┬───┘
       │
       v
   ┌───────┐     action_draft()
   │ Draft ├────────────┐
   └───┬───┘            │
       │                │
       │ action_quotation()
       │                │
       v                │
  ┌──────────┐          │
  │Quotation │<─────────┘
  └────┬─────┘
       │
       │ action_confirm()
       │
       v
   ┌──────┐
   │ Sale │
   └───┬──┘
       │
       │ (auto on delivery)
       │
       v
   ┌──────┐
   │ Done │
   └──────┘

  Any state can go to:
   ┌────────┐
   │ Cancel │ (via action_cancel())
   └────────┘
```

---

## 🌐 API Endpoints

### JSON-RPC Endpoints

```javascript
// Get products with stock
rpc.query({
    model: 'product.product',
    method: 'search_read',
    args: [],
    kwargs: {
        domain: [['sale_ok', '=', true]],
        fields: ['id', 'name', 'name_arabic', 'brand_id', 'list_price', 'uom_id'],
    }
});

// Create order
rpc.query({
    model: 'pos.perfume.order',
    method: 'create',
    args: [{
        partner_id: partnerId,
        order_line_ids: orderLines.map(line => [0, 0, line]),
    }]
});

// Confirm order
rpc.query({
    model: 'pos.perfume.order',
    method: 'action_confirm',
    args: [[orderId]],
});
```

---

## 🧪 Testing Examples

### Unit Test Example

```python
# tests/test_pos_perfume_order.py
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestPosPerfumeOrder(TransactionCase):
    
    def setUp(self):
        super().setUp()
        self.Order = self.env['pos.perfume.order']
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer'
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Perfume',
            'list_price': 100.0,
        })
        
    def test_order_creation(self):
        """Test basic order creation"""
        order = self.Order.create({
            'partner_id': self.partner.id,
            'order_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 2,
                'unit_price': 100.0,
                'discount_percent': 10.0,
            })]
        })
        
        self.assertEqual(order.state, 'draft')
        self.assertEqual(len(order.order_line_ids), 1)
        self.assertEqual(order.amount_subtotal, 200.0)
        self.assertEqual(order.amount_discount, 20.0)
        self.assertEqual(order.amount_total, 180.0)
    
    def test_order_confirm(self):
        """Test order confirmation creates sale order"""
        order = self.Order.create({
            'partner_id': self.partner.id,
            'order_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'unit_price': 100.0,
            })]
        })
        
        order.action_confirm()
        
        self.assertEqual(order.state, 'sale')
        self.assertTrue(order.sale_order_id)
        self.assertEqual(order.sale_order_id.partner_id, self.partner)
```

### Integration Test Example

```python
def test_full_order_flow(self):
    """Test complete order flow from draft to done"""
    # Create draft order
    order = self.Order.create({
        'partner_id': self.partner.id,
    })
    self.assertEqual(order.state, 'draft')
    
    # Add lines
    order.write({
        'order_line_ids': [(0, 0, {
            'product_id': self.product.id,
            'quantity': 5,
            'unit_price': 50.0,
            'discount_percent': 5.0,
        })]
    })
    
    # Create quotation
    order.action_quotation()
    self.assertEqual(order.state, 'quotation')
    
    # Confirm sale
    order.action_confirm()
    self.assertEqual(order.state, 'sale')
    self.assertTrue(order.sale_order_id)
    
    # Check sale order
    sale = order.sale_order_id
    self.assertEqual(len(sale.order_line), 1)
    self.assertEqual(sale.amount_total, order.amount_total)
```

---

## 📝 Code Style Guide

### Python (PEP 8 + Odoo Guidelines)

```python
# Good
class PosPerfumeOrder(models.Model):
    _name = 'pos.perfume.order'
    _description = 'POS Perfume Order'
    
    name = fields.Char(string='Order Reference', required=True)
    
    @api.depends('order_line_ids.line_total')
    def _compute_amount_total(self):
        for order in self:
            order.amount_total = sum(order.order_line_ids.mapped('line_total'))

# Bad
class PosPerfumeOrder(models.Model):
    _name='pos.perfume.order' # Missing space
    name=fields.Char('Order Reference',required=True) # Missing spaces
    
    def _compute_amount_total(self): # Missing @api.depends
        self.amount_total=sum(self.order_line_ids.mapped('line_total'))
```

### JavaScript (Odoo OWL Style)

```javascript
// Good
import { Component, useState } from "@odoo/owl";

export class OrderTable extends Component {
    static template = "pos_perfume.OrderTable";
    static props = {
        lines: Array,
        onLineChange: Function,
    };
    
    setup() {
        this.state = useState({ editingLine: null });
    }
    
    onQuantityChange(lineIndex, value) {
        this.props.onLineChange(lineIndex, 'quantity', value);
    }
}

// Bad
export class OrderTable extends Component {
    setup() {
        this.state={ editingLine:null }; // Use useState
    }
    onQuantityChange(lineIndex,value){ // Missing spaces
        this.props.onLineChange(lineIndex,'quantity',value);
    }
}
```

---

## 🔮 Future Enhancements

### Planned Features

1. **Offline Mode**
   - Use Service Workers
   - IndexedDB for local storage
   - Sync when online

2. **Barcode Scanner**
   - USB barcode scanner support
   - Mobile camera scanner
   - Auto-add products

3. **Advanced Reporting**
   - Sales analytics dashboard
   - Best-selling products
   - Customer purchase history
   - Inventory turnover

4. **Multi-Currency**
   - Real-time exchange rates
   - Multiple price lists
   - Currency conversion

5. **Loyalty Program**
   - Points system
   - Discount coupons
   - Member tiers

---

## 📚 References

### Odoo Documentation
- [Odoo 17 Developer Documentation](https://www.odoo.com/documentation/17.0/developer.html)
- [OWL Framework](https://github.com/odoo/owl)
- [QWeb Templates](https://www.odoo.com/documentation/17.0/developer/reference/frontend/qweb.html)

### Related Modules
- `point_of_sale`: Base POS module
- `stock`: Inventory management
- `sale`: Sales orders
- `account`: Accounting integration

---

## 👥 Contributors

- **Lead Developer**: AI Assistant (Claude)
- **Client**: Lugal-AI
- **Project**: POS Perfume Store System
- **Date**: October 2025

---

## 📄 License

This module is licensed under LGPL-3.
See LICENSE file for details.

---

## 🆘 Support

For issues or questions:
1. Check this technical documentation
2. Review Odoo official documentation
3. Contact development team

---

**Document Version**: 1.0  
**Last Updated**: October 22, 2025  
**Status**: Complete

---

**End of Technical Notes**











