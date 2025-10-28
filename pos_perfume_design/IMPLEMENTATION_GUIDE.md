# Odoo Implementation Guide
## دليل تنفيذ Odoo للنظام

---

## 📚 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Module Structure](#module-structure)
3. [Phase 1: Backend Models](#phase-1-backend-models)
4. [Phase 2: Views & Templates](#phase-2-views--templates)
5. [Phase 3: JavaScript & OWL](#phase-3-javascript--owl)
6. [Phase 4: Integration](#phase-4-integration)
7. [Phase 5: Reports & Printing](#phase-5-reports--printing)
8. [Testing](#testing)
9. [Deployment](#deployment)

---

## Prerequisites | المتطلبات

### Required Knowledge
- Odoo Framework (v17.0)
- Python 3.10+
- PostgreSQL
- JavaScript/OWL Framework
- QWeb Templates
- XML for Odoo views

### Development Environment
- Odoo 17.0 installed
- IDE (VS Code, PyCharm)
- PostgreSQL database
- Git for version control

---

## Module Structure | هيكل الوحدة

### Recommended Directory Structure

```
addons/
└── pos_perfume/
    ├── __init__.py
    ├── __manifest__.py
    │
    ├── models/
    │   ├── __init__.py
    │   ├── pos_perfume_order.py
    │   ├── pos_perfume_order_line.py
    │   ├── product_product.py (inherit)
    │   └── res_currency.py (inherit)
    │
    ├── views/
    │   ├── pos_perfume_order_views.xml
    │   ├── pos_perfume_templates.xml
    │   ├── pos_perfume_assets.xml
    │   └── pos_perfume_menu.xml
    │
    ├── static/
    │   ├── src/
    │   │   ├── app/
    │   │   │   ├── pos_perfume_app.js
    │   │   │   ├── order_table.js
    │   │   │   ├── product_search.js
    │   │   │   └── totals_section.js
    │   │   │
    │   │   ├── models/
    │   │   │   ├── pos_order.js
    │   │   │   ├── pos_order_line.js
    │   │   │   └── product.js
    │   │   │
    │   │   └── xml/
    │   │       ├── pos_perfume.xml
    │   │       ├── order_table.xml
    │   │       └── product_search.xml
    │   │
    │   └── scss/
    │       └── pos_perfume.scss
    │
    ├── security/
    │   ├── ir.model.access.csv
    │   └── pos_perfume_security.xml
    │
    ├── data/
    │   ├── pos_perfume_demo.xml
    │   └── pos_perfume_sequence.xml
    │
    ├── wizard/
    │   ├── __init__.py
    │   └── pos_whatsapp_send.py
    │
    ├── report/
    │   ├── __init__.py
    │   ├── pos_perfume_report.xml
    │   └── pos_perfume_report_templates.xml
    │
    └── i18n/
        ├── ar.po
        └── en_US.po
```

---

## Phase 1: Backend Models

### Step 1.1: Create Main Module

**File: `__manifest__.py`**
```python
{
    'name': 'POS Perfume Store',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Specialized POS for Perfume Store with Excel-like interface',
    'description': """
        Point of Sale system designed specifically for perfume stores.
        Features:
        - Excel-like order interface
        - Real-time product search
        - Multi-warehouse support
        - Dual currency (USD/IQD)
        - WhatsApp integration
    """,
    'author': 'Lugal-AI',
    'website': 'https://lugal-ai.com',
    'depends': [
        'base',
        'product',
        'stock',
        'account',
        'sale',
        'point_of_sale',
    ],
    'data': [
        'security/pos_perfume_security.xml',
        'security/ir.model.access.csv',
        'data/pos_perfume_sequence.xml',
        'views/pos_perfume_order_views.xml',
        'views/pos_perfume_templates.xml',
        'views/pos_perfume_menu.xml',
        'report/pos_perfume_report.xml',
        'report/pos_perfume_report_templates.xml',
    ],
    'demo': [
        'data/pos_perfume_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pos_perfume/static/src/app/**/*.js',
            'pos_perfume/static/src/models/**/*.js',
            'pos_perfume/static/src/xml/**/*.xml',
            'pos_perfume/static/scss/pos_perfume.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
```

### Step 1.2: Create Order Model

**File: `models/pos_perfume_order.py`**
```python
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PosPerfumeOrder(models.Model):
    _name = 'pos.perfume.order'
    _description = 'POS Perfume Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Order Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        tracking=True
    )
    
    date = fields.Datetime(
        string='Order Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        required=True,
        default=lambda self: self.env.user,
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True
    )
    
    order_line_ids = fields.One2many(
        'pos.perfume.order.line',
        'order_id',
        string='Order Lines',
        copy=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('quotation', 'Quotation'),
        ('sale', 'Sale Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Totals
    amount_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_amounts',
        store=True
    )
    
    amount_discount = fields.Monetary(
        string='Total Discount',
        compute='_compute_amounts',
        store=True
    )
    
    amount_tax = fields.Monetary(
        string='Taxes',
        compute='_compute_amounts',
        store=True
    )
    
    amount_total = fields.Monetary(
        string='Total',
        compute='_compute_amounts',
        store=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.ref('base.USD')
    )
    
    # IQD Currency
    amount_total_iqd = fields.Monetary(
        string='Total (IQD)',
        compute='_compute_amount_iqd',
        currency_field='currency_iqd_id'
    )
    
    currency_iqd_id = fields.Many2one(
        'res.currency',
        string='IQD Currency',
        default=lambda self: self.env.ref('base.IQD')
    )
    
    exchange_rate = fields.Float(
        string='Exchange Rate (USD to IQD)',
        default=1300.0,
        digits=(12, 2)
    )
    
    # Related Sale Order
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        readonly=True
    )
    
    @api.depends('order_line_ids.line_subtotal', 'order_line_ids.discount_amount')
    def _compute_amounts(self):
        for order in self:
            amount_subtotal = 0.0
            amount_discount = 0.0
            amount_tax = 0.0
            
            for line in order.order_line_ids:
                amount_subtotal += line.line_subtotal
                amount_discount += line.discount_amount
            
            order.amount_subtotal = amount_subtotal
            order.amount_discount = amount_discount
            order.amount_tax = amount_tax
            order.amount_total = amount_subtotal - amount_discount + amount_tax
    
    @api.depends('amount_total', 'exchange_rate')
    def _compute_amount_iqd(self):
        for order in self:
            order.amount_total_iqd = order.amount_total * order.exchange_rate
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'pos.perfume.order'
                ) or 'New'
        return super().create(vals_list)
    
    def action_quotation(self):
        """Create quotation"""
        self.ensure_one()
        self.state = 'quotation'
        return True
    
    def action_confirm(self):
        """Confirm order and create sale order"""
        self.ensure_one()
        
        if not self.order_line_ids:
            raise UserError(_('Cannot confirm an order without lines.'))
        
        # Create Sale Order
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id,
            'date_order': self.date,
            'origin': self.name,
            'order_line': [(0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'price_unit': line.unit_price,
                'discount': line.discount_percent,
                'warehouse_id': line.warehouse_id.id,
            }) for line in self.order_line_ids]
        })
        
        self.write({
            'state': 'sale',
            'sale_order_id': sale_order.id,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_cancel(self):
        """Cancel order"""
        self.state = 'cancel'
        return True
    
    def action_draft(self):
        """Set to draft"""
        self.state = 'draft'
        return True
    
    def action_send_whatsapp(self):
        """Open WhatsApp wizard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Send via WhatsApp',
            'res_model': 'pos.whatsapp.send',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id}
        }
```

### Step 1.3: Create Order Line Model

**File: `models/pos_perfume_order_line.py`**
```python
from odoo import models, fields, api

class PosPerfumeOrderLine(models.Model):
    _name = 'pos.perfume.order.line'
    _description = 'POS Perfume Order Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    
    order_id = fields.Many2one(
        'pos.perfume.order',
        string='Order Reference',
        required=True,
        ondelete='cascade'
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain=[('sale_ok', '=', True)]
    )
    
    product_code = fields.Char(
        related='product_id.default_code',
        string='Product Code',
        readonly=True
    )
    
    product_name_arabic = fields.Char(
        related='product_id.name_arabic',
        string='Arabic Name',
        readonly=True
    )
    
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True
    )
    
    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0,
        digits='Product Unit of Measure'
    )
    
    unit_price = fields.Float(
        string='Unit Price',
        required=True,
        digits='Product Price'
    )
    
    discount_percent = fields.Float(
        string='Discount %',
        default=0.0,
        digits=(5, 2)
    )
    
    # Computed fields
    price_after_discount = fields.Monetary(
        string='Price After Discount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    line_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    discount_amount = fields.Monetary(
        string='Discount Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    line_total = fields.Monetary(
        string='Total',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        related='order_id.currency_id',
        string='Currency'
    )
    
    # Stock availability
    available_qty = fields.Float(
        string='Available Qty',
        compute='_compute_available_qty'
    )
    
    @api.depends('quantity', 'unit_price', 'discount_percent')
    def _compute_amounts(self):
        for line in self:
            price_after_discount = line.unit_price * (1 - line.discount_percent / 100)
            line_subtotal = line.quantity * line.unit_price
            discount_amount = line_subtotal * (line.discount_percent / 100)
            line_total = line.quantity * price_after_discount
            
            line.update({
                'price_after_discount': price_after_discount,
                'line_subtotal': line_subtotal,
                'discount_amount': discount_amount,
                'line_total': line_total,
            })
    
    @api.depends('product_id', 'warehouse_id')
    def _compute_available_qty(self):
        for line in self:
            if line.product_id and line.warehouse_id:
                stock_quant = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id.warehouse_id', '=', line.warehouse_id.id),
                    ('location_id.usage', '=', 'internal'),
                ], limit=1)
                line.available_qty = stock_quant.quantity if stock_quant else 0.0
            else:
                line.available_qty = 0.0
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.unit_price = self.product_id.list_price
```

### Step 1.4: Extend Product Model

**File: `models/product_product.py`**
```python
from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    name_arabic = fields.Char(
        string='Arabic Name',
        translate=True
    )
    
    brand_id = fields.Many2one(
        'product.brand',
        string='Brand'
    )
    
    price_iqd = fields.Monetary(
        string='Price (IQD)',
        compute='_compute_price_iqd',
        currency_field='currency_iqd_id'
    )
    
    currency_iqd_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.ref('base.IQD')
    )
    
    def _compute_price_iqd(self):
        exchange_rate = 1300.0  # Could be from settings
        for product in self:
            product.price_iqd = product.list_price * exchange_rate
    
    def get_stock_by_warehouse(self):
        """Get stock quantities grouped by warehouse"""
        self.ensure_one()
        warehouses = self.env['stock.warehouse'].search([])
        stock_data = []
        
        for warehouse in warehouses:
            quants = self.env['stock.quant'].search([
                ('product_id', '=', self.id),
                ('location_id.warehouse_id', '=', warehouse.id),
                ('location_id.usage', '=', 'internal'),
            ])
            total_qty = sum(quants.mapped('quantity'))
            
            if total_qty > 0:
                stock_data.append({
                    'warehouse_code': warehouse.code,
                    'warehouse_name': warehouse.name,
                    'quantity': total_qty,
                })
        
        return stock_data
```

### Step 1.5: Create Security Rules

**File: `security/ir.model.access.csv`**
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_pos_perfume_order_user,pos.perfume.order.user,model_pos_perfume_order,base.group_user,1,1,1,0
access_pos_perfume_order_manager,pos.perfume.order.manager,model_pos_perfume_order,base.group_system,1,1,1,1
access_pos_perfume_order_line_user,pos.perfume.order.line.user,model_pos_perfume_order_line,base.group_user,1,1,1,1
```

**File: `security/pos_perfume_security.xml`**
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="module_category_pos_perfume" model="ir.module.category">
        <field name="name">POS Perfume</field>
        <field name="sequence">50</field>
    </record>

    <record id="group_pos_perfume_user" model="res.groups">
        <field name="name">User</field>
        <field name="category_id" ref="module_category_pos_perfume"/>
    </record>

    <record id="group_pos_perfume_manager" model="res.groups">
        <field name="name">Manager</field>
        <field name="category_id" ref="module_category_pos_perfume"/>
        <field name="implied_ids" eval="[(4, ref('group_pos_perfume_user'))]"/>
    </record>
</odoo>
```

### Step 1.6: Create Sequence

**File: `data/pos_perfume_sequence.xml`**
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <record id="sequence_pos_perfume_order" model="ir.sequence">
            <field name="name">POS Perfume Order</field>
            <field name="code">pos.perfume.order</field>
            <field name="prefix">POS/%(range_y)s/</field>
            <field name="padding">4</field>
            <field name="number_increment">1</field>
        </record>
    </data>
</odoo>
```

---

## Phase 2: Views & Templates

### Step 2.1: Create Form View

**File: `views/pos_perfume_order_views.xml`**
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Form View -->
    <record id="view_pos_perfume_order_form" model="ir.ui.view">
        <field name="name">pos.perfume.order.form</field>
        <field name="model">pos.perfume.order</field>
        <field name="arch" type="xml">
            <form string="POS Perfume Order">
                <header>
                    <button name="action_quotation" string="Quotation" 
                            type="object" states="draft" 
                            class="btn-primary"/>
                    <button name="action_confirm" string="Confirm Sale" 
                            type="object" states="draft,quotation" 
                            class="btn-primary"/>
                    <button name="action_send_whatsapp" string="Send WhatsApp" 
                            type="object" 
                            icon="fa-whatsapp"
                            class="btn-success"/>
                    <button name="action_cancel" string="Cancel" 
                            type="object" states="draft,quotation"/>
                    <field name="state" widget="statusbar" 
                           statusbar_visible="draft,quotation,sale,done"/>
                </header>
                <sheet>
                    <div class="oe_title">
                        <h1>
                            <field name="name" readonly="1"/>
                        </h1>
                    </div>
                    <group>
                        <group>
                            <field name="partner_id"/>
                            <field name="date"/>
                        </group>
                        <group>
                            <field name="user_id"/>
                            <field name="sale_order_id" readonly="1"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="Order Lines">
                            <field name="order_line_ids">
                                <tree editable="bottom">
                                    <field name="sequence" widget="handle"/>
                                    <field name="product_id"/>
                                    <field name="product_code"/>
                                    <field name="warehouse_id"/>
                                    <field name="available_qty"/>
                                    <field name="quantity"/>
                                    <field name="unit_price"/>
                                    <field name="discount_percent"/>
                                    <field name="price_after_discount"/>
                                    <field name="line_total"/>
                                    <field name="currency_id" invisible="1"/>
                                </tree>
                            </field>
                            <group class="oe_subtotal_footer oe_right">
                                <field name="amount_subtotal"/>
                                <field name="amount_discount"/>
                                <field name="amount_tax"/>
                                <div class="oe_subtotal_footer_separator oe_inline">
                                    <label for="amount_total"/>
                                </div>
                                <field name="amount_total" class="oe_subtotal_footer_separator"/>
                                <field name="exchange_rate"/>
                                <field name="amount_total_iqd" class="oe_subtotal_footer_separator"/>
                                <field name="currency_id" invisible="1"/>
                                <field name="currency_iqd_id" invisible="1"/>
                            </group>
                        </page>
                    </notebook>
                </sheet>
                <div class="oe_chatter">
                    <field name="message_follower_ids"/>
                    <field name="activity_ids"/>
                    <field name="message_ids"/>
                </div>
            </form>
        </field>
    </record>

    <!-- Tree View -->
    <record id="view_pos_perfume_order_tree" model="ir.ui.view">
        <field name="name">pos.perfume.order.tree</field>
        <field name="model">pos.perfume.order</field>
        <field name="arch" type="xml">
            <tree string="POS Orders">
                <field name="name"/>
                <field name="date"/>
                <field name="partner_id"/>
                <field name="user_id"/>
                <field name="amount_total"/>
                <field name="state"/>
            </tree>
        </field>
    </record>

    <!-- Search View -->
    <record id="view_pos_perfume_order_search" model="ir.ui.view">
        <field name="name">pos.perfume.order.search</field>
        <field name="model">pos.perfume.order</field>
        <field name="arch" type="xml">
            <search string="POS Orders">
                <field name="name"/>
                <field name="partner_id"/>
                <field name="user_id"/>
                <filter name="draft" string="Draft" domain="[('state','=','draft')]"/>
                <filter name="quotation" string="Quotation" domain="[('state','=','quotation')]"/>
                <filter name="sale" string="Sales" domain="[('state','=','sale')]"/>
                <group expand="0" string="Group By">
                    <filter name="group_by_partner" string="Customer" context="{'group_by':'partner_id'}"/>
                    <filter name="group_by_user" string="Salesperson" context="{'group_by':'user_id'}"/>
                    <filter name="group_by_state" string="Status" context="{'group_by':'state'}"/>
                </group>
            </search>
        </field>
    </record>

    <!-- Action -->
    <record id="action_pos_perfume_order" model="ir.actions.act_window">
        <field name="name">POS Orders</field>
        <field name="res_model">pos.perfume.order</field>
        <field name="view_mode">tree,form</field>
        <field name="search_view_id" ref="view_pos_perfume_order_search"/>
    </record>
</odoo>
```

### Step 2.2: Create POS Interface Template

**File: `views/pos_perfume_templates.xml`**
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <template id="pos_perfume_main" name="POS Perfume Main">
        <t t-call="web.layout">
            <t t-set="head">
                <script type="text/javascript" src="/pos_perfume/static/src/app/pos_perfume_app.js"/>
            </t>
            <div class="pos-perfume-container">
                <!-- Header -->
                <div class="pos-header">
                    <h1>🛒 Point of Sale - Perfume Store</h1>
                    <div class="header-info">
                        <span class="user-info">
                            👤 User: <t t-esc="user.name"/>
                        </span>
                        <span class="date-info">
                            📅 Date: <t t-esc="current_date"/>
                        </span>
                        <span class="time-info">
                            🕐 Time: <t t-esc="current_time"/>
                        </span>
                    </div>
                </div>

                <!-- Main Content (will be loaded via JS) -->
                <div class="pos-main-content">
                    <div id="pos-perfume-app"/>
                </div>
            </div>
        </t>
    </template>

    <!-- Menu Item -->
    <menuitem id="menu_pos_perfume_root"
              name="POS Perfume"
              sequence="10"/>

    <menuitem id="menu_pos_perfume_interface"
              name="POS Interface"
              parent="menu_pos_perfume_root"
              action="action_pos_perfume_interface"
              sequence="1"/>

    <menuitem id="menu_pos_perfume_orders"
              name="Orders"
              parent="menu_pos_perfume_root"
              action="action_pos_perfume_order"
              sequence="2"/>
</odoo>
```

---

## Phase 3: JavaScript & OWL

This section will detail the OWL components needed. Due to space constraints, I'll provide the structure and key components.

### Component Structure

```javascript
// Main App Component
// File: static/src/app/pos_perfume_app.js

import { Component } from "@odoo/owl";
import { OrderTable } from "./order_table";
import { ProductSearch } from "./product_search";
import { TotalsSection } from "./totals_section";
import { ActionButtons } from "./action_buttons";

export class PosPerfumeApp extends Component {
    static template = "pos_perfume.PosPerfumeApp";
    static components = { OrderTable, ProductSearch, TotalsSection, ActionButtons };
    
    setup() {
        this.state = useState({
            order: {
                id: null,
                partner_id: null,
                lines: [],
                totals: {
                    subtotal: 0,
                    discount: 0,
                    tax: 0,
                    total_usd: 0,
                    total_iqd: 0,
                }
            }
        });
    }
    
    // Methods for order management
    addProduct(product) {
        // Add product to order
    }
    
    updateLine(lineIndex, field, value) {
        // Update order line
    }
    
    deleteLine(lineIndex) {
        // Delete order line
    }
    
    calculateTotals() {
        // Calculate all totals
    }
    
    confirmOrder() {
        // Confirm and save order
    }
}
```

---

## Phase 4: Integration

### WhatsApp Integration

**File: `wizard/pos_whatsapp_send.py`**
```python
from odoo import models, fields, api
import requests

class PosWhatsappSend(models.TransientModel):
    _name = 'pos.whatsapp.send'
    _description = 'Send Order via WhatsApp'

    order_id = fields.Many2one('pos.perfume.order', required=True)
    phone = fields.Char(string='Phone Number', required=True)
    message = fields.Text(string='Message', required=True)
    
    @api.onchange('order_id')
    def _onchange_order_id(self):
        if self.order_id:
            self.phone = self.order_id.partner_id.phone or ''
            self.message = self._prepare_message()
    
    def _prepare_message(self):
        order = self.order_id
        message = f"""
*Order {order.name}*
Customer: {order.partner_id.name}
Date: {order.date.strftime('%Y-%m-%d')}

*Order Details:*
"""
        for line in order.order_line_ids:
            message += f"\n• {line.product_id.name}"
            message += f"\n  Qty: {line.quantity} x ${line.unit_price}"
            if line.discount_percent:
                message += f" (- {line.discount_percent}%)"
            message += f" = ${line.line_total}"
        
        message += f"""

*Total: ${order.amount_total}*
*Total (IQD): {order.amount_total_iqd:,.0f} IQD*

Thank you for your business!
"""
        return message
    
    def action_send(self):
        # Implement WhatsApp API call
        # This depends on your WhatsApp integration method
        pass
```

---

## Phase 5: Reports & Printing

### Invoice/Receipt Template

**File: `report/pos_perfume_report_templates.xml`**
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <template id="report_pos_perfume_order">
        <t t-call="web.html_container">
            <t t-foreach="docs" t-as="o">
                <t t-call="web.external_layout">
                    <div class="page">
                        <h2>
                            <span t-if="o.state == 'quotation'">Quotation</span>
                            <span t-else="">Order</span>
                            <span t-field="o.name"/>
                        </h2>
                        
                        <div class="row mt32 mb32">
                            <div class="col-6">
                                <strong>Customer:</strong>
                                <div t-field="o.partner_id" 
                                     t-options='{"widget": "contact", "fields": ["address", "name", "phone"], "no_marker": True}'/>
                            </div>
                            <div class="col-6">
                                <strong>Order Date:</strong> <span t-field="o.date"/><br/>
                                <strong>Salesperson:</strong> <span t-field="o.user_id.name"/><br/>
                            </div>
                        </div>

                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Product</th>
                                    <th class="text-right">Warehouse</th>
                                    <th class="text-right">Qty</th>
                                    <th class="text-right">Unit Price</th>
                                    <th class="text-right">Disc %</th>
                                    <th class="text-right">Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr t-foreach="o.order_line_ids" t-as="line">
                                    <td>
                                        <span t-field="line.product_id.name"/>
                                        <br/>
                                        <small t-field="line.product_name_arabic" class="text-muted"/>
                                    </td>
                                    <td class="text-right"><span t-field="line.warehouse_id.code"/></td>
                                    <td class="text-right"><span t-field="line.quantity"/></td>
                                    <td class="text-right"><span t-field="line.unit_price"/></td>
                                    <td class="text-right"><span t-field="line.discount_percent"/>%</td>
                                    <td class="text-right"><span t-field="line.line_total"/></td>
                                </tr>
                            </tbody>
                        </table>

                        <div class="clearfix">
                            <div class="row">
                                <div class="col-6 offset-6">
                                    <table class="table table-sm">
                                        <tr>
                                            <td><strong>Subtotal:</strong></td>
                                            <td class="text-right"><span t-field="o.amount_subtotal"/></td>
                                        </tr>
                                        <tr>
                                            <td><strong>Discount:</strong></td>
                                            <td class="text-right" style="color: red;">-<span t-field="o.amount_discount"/></td>
                                        </tr>
                                        <tr>
                                            <td><strong>Tax:</strong></td>
                                            <td class="text-right"><span t-field="o.amount_tax"/></td>
                                        </tr>
                                        <tr class="border-top">
                                            <td><strong>Total (USD):</strong></td>
                                            <td class="text-right"><strong><span t-field="o.amount_total"/></strong></td>
                                        </tr>
                                        <tr>
                                            <td><strong>Total (IQD):</strong></td>
                                            <td class="text-right"><strong><span t-field="o.amount_total_iqd"/> IQD</strong></td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <p class="text-center mt-5">
                            Thank you for your business!
                        </p>
                    </div>
                </t>
            </t>
        </t>
    </template>
</odoo>
```

---

## Testing

### Unit Tests
Create tests in `tests/` directory:
- `test_pos_perfume_order.py`
- `test_calculations.py`
- `test_stock_integration.py`

### Manual Testing Checklist
- [ ] Create new order
- [ ] Add products
- [ ] Calculate discounts
- [ ] Check stock availability
- [ ] Confirm order
- [ ] Create sale order
- [ ] Print receipt
- [ ] Send WhatsApp
- [ ] Cancel order

---

## Deployment

### Installation Steps
1. Copy module to `addons/` directory
2. Update app list: `odoo-bin -u base -d your_database`
3. Install module from Apps menu
4. Configure settings
5. Load demo data (optional)
6. Test functionality

### Configuration
- Set exchange rate
- Configure warehouses
- Set up product data
- Configure users and permissions

---

## Next Steps

1. Review and customize models
2. Implement JavaScript components
3. Style with SCSS
4. Test thoroughly
5. Deploy to production

---

**Document Version**: 1.0  
**Last Updated**: October 22, 2025

---

**End of Implementation Guide**









