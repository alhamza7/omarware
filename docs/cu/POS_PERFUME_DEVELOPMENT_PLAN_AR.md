# 📋 خطة تطوير واجهة POS PERFUME الشاملة
# Complete Development Plan for POS PERFUME Interface

## 🎯 الهدف الرئيسي / Main Objective

تطوير واجهة POS PERFUME لتكون **متكاملة تماماً** مع Sale Order مع الإبقاء على التصميم الحالي وإضافة:
1. ✅ اختيار **وحدة القياس (UoM)** لكل منتج
2. ✅ اختيار **مكان التخزين (Storage Location)** 
3. ✅ البحث والاختيار من **قائمة العملاء**
4. ✅ الربط الكامل مع بيانات Sale Order

---

## 📊 التحليل الحالي / Current Analysis

### ✅ ما هو موجود حالياً:

```
pos_perfume_custom/
├── Backend (Python):
│   ├── ✓ pos.perfume.order (model)
│   ├── ✓ pos.perfume.order.line (model)
│   ├── ✓ Warehouse support (warehouse_id)
│   ├── ✓ Customer support (partner_id)
│   └── ✗ UoM support (MISSING)
│
├── Frontend (OWL JS):
│   ├── ✓ Excel-like table with arrow navigation
│   ├── ✓ Product search
│   ├── ✓ Customer field
│   └── ✗ Advanced features (MISSING)
│
└── Views:
    ├── ✓ Form views
    ├── ✓ Tree views
    └── ✓ Menu structure
```

### ❌ ما هو مفقود / What's Missing:

1. **UoM Support**: لا يوجد حقل لوحدة القياس
2. **Storage Location**: warehouse_id موجود لكن غير متكامل
3. **Customer Search**: موجود بشكل بسيط، يحتاج تحسين
4. **Product Details**: لا يظهر معلومات SAP الكاملة
5. **Price by UoM**: لا يجلب السعر حسب وحدة القياس

---

## 🏗️ خطة التطوير / Development Plan

### المرحلة 1️⃣: تطوير Backend (Python Models)

#### 1.1 إضافة دعم UoM

**الملف**: `models/pos_perfume_order.py`

```python
# في PosPerfumeOrderLine:

product_uom_id = fields.Many2one(
    'uom.uom',
    string='Unit of Measure',
    required=True,
    help='Unit of measure for this product'
)

# إضافة onchange للحصول على السعر الصحيح
@api.onchange('product_id', 'product_uom_id', 'warehouse_id')
def _onchange_product_uom(self):
    """Get price based on UoM from pricelist"""
    if self.product_id and self.product_uom_id:
        # Get price from uom_in_pricelist
        pricelist = self.order_id.pricelist_id or self.env.ref('product.list0')
        price = self._get_uom_price(pricelist, self.product_uom_id)
        self.unit_price = price

def _get_uom_price(self, pricelist, uom):
    """Get price for specific UoM from pricelist items"""
    # البحث في pricelist items عن السعر المناسب
    item = self.env['product.pricelist.item'].search([
        ('pricelist_id', '=', pricelist.id),
        ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
        ('product_packaging_id', '=', uom.id),
        ('compute_price', '=', 'fixed'),
    ], limit=1)
    
    if item:
        return item.fixed_price
    return self.product_id.list_price
```

#### 1.2 تحسين Storage Location

```python
# إضافة حقول إضافية للموقع
location_id = fields.Many2one(
    'stock.location',
    string='Storage Location',
    help='Specific storage location within warehouse'
)

# حساب الكمية المتاحة حسب الموقع المحدد
@api.depends('product_id', 'warehouse_id', 'location_id')
def _compute_available_qty(self):
    for line in self:
        if not line.product_id:
            line.available_qty = 0
            continue
            
        # إذا كان هناك موقع محدد
        if line.location_id:
            location = line.location_id
        elif line.warehouse_id:
            location = line.warehouse_id.lot_stock_id
        else:
            line.available_qty = 0
            continue
        
        # جلب الكمية من SAP warehouse info
        warehouse_info = self.env['sap.product.warehouse.info'].search([
            ('product_id', '=', line.product_id.id),
            ('warehouse_code', '=', line.warehouse_id.code),
        ], limit=1)
        
        if warehouse_info:
            line.available_qty = warehouse_info.on_hand
        else:
            # fallback to Odoo stock
            quants = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('location_id', '=', location.id),
            ])
            line.available_qty = sum(quants.mapped('quantity'))
```

#### 1.3 إضافة Pricelist Support

```python
# في PosPerfumeOrder:
pricelist_id = fields.Many2one(
    'product.pricelist',
    string='Pricelist',
    required=True,
    default=lambda self: self.env.ref('product.list0', raise_if_not_found=False)
)

# ربط مع partner
@api.onchange('partner_id')
def _onchange_partner_pricelist(self):
    if self.partner_id and self.partner_id.property_product_pricelist:
        self.pricelist_id = self.partner_id.property_product_pricelist
```

---

### المرحلة 2️⃣: تطوير Frontend (JavaScript/OWL)

#### 2.1 تحسين Product Search مع UoM

**ملف جديد**: `static/src/app/product_search_uom.js`

```javascript
import { Component, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ProductSearchWithUoM extends Component {
    static template = "pos_perfume_custom.ProductSearchWithUoM";
    
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            searchTerm: '',
            products: [],
            selectedProduct: null,
            availableUoms: [],
            selectedUom: null,
            priceInfo: null,
        });
    }
    
    async searchProducts(term) {
        // البحث عن المنتجات
        const products = await this.orm.searchRead(
            'product.product',
            [
                ['sale_ok', '=', true],
                '|', '|',
                ['name', 'ilike', term],
                ['default_code', 'ilike', term],
                ['foreign_name', 'ilike', term],
            ],
            ['id', 'name', 'default_code', 'foreign_name', 'list_price'],
            { limit: 50 }
        );
        this.state.products = products;
    }
    
    async selectProduct(product) {
        this.state.selectedProduct = product;
        
        // جلب وحدات القياس المتاحة من pricelist
        const uoms = await this.orm.call(
            'product.product',
            'get_available_uoms_with_prices',
            [product.id],
            {
                pricelist_id: this.props.pricelist_id,
            }
        );
        
        this.state.availableUoms = uoms;
        this.state.selectedUom = uoms[0] || null;
    }
    
    async selectUom(uom) {
        this.state.selectedUom = uom;
        
        // جلب معلومات السعر
        const priceInfo = await this.orm.call(
            'product.pricelist',
            'get_price_for_uom',
            [this.props.pricelist_id],
            {
                product_id: this.state.selectedProduct.id,
                uom_id: uom.id,
            }
        );
        
        this.state.priceInfo = priceInfo;
    }
    
    addToOrder() {
        // إضافة المنتج إلى الطلب
        this.props.onAddProduct({
            product_id: this.state.selectedProduct.id,
            product_name: this.state.selectedProduct.name,
            product_code: this.state.selectedProduct.default_code,
            uom_id: this.state.selectedUom.id,
            uom_name: this.state.selectedUom.name,
            price: this.state.priceInfo.price,
        });
        
        // إعادة تعيين
        this.state.selectedProduct = null;
        this.state.availableUoms = [];
        this.state.searchTerm = '';
    }
}
```

#### 2.2 Customer Search Component

**ملف جديد**: `static/src/app/customer_search.js`

```javascript
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CustomerSearch extends Component {
    static template = "pos_perfume_custom.CustomerSearch";
    
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            searchTerm: '',
            customers: [],
            selectedCustomer: null,
            showDropdown: false,
        });
    }
    
    async searchCustomers(term) {
        if (!term || term.length < 2) {
            this.state.customers = [];
            this.state.showDropdown = false;
            return;
        }
        
        const customers = await this.orm.searchRead(
            'res.partner',
            [
                ['customer_rank', '>', 0],
                '|', '|', '|',
                ['name', 'ilike', term],
                ['phone', 'ilike', term],
                ['mobile', 'ilike', term],
                ['email', 'ilike', term],
            ],
            ['id', 'name', 'phone', 'mobile', 'email', 'property_product_pricelist'],
            { limit: 20 }
        );
        
        this.state.customers = customers;
        this.state.showDropdown = true;
    }
    
    selectCustomer(customer) {
        this.state.selectedCustomer = customer;
        this.state.showDropdown = false;
        this.state.searchTerm = customer.name;
        
        // Notify parent
        this.props.onSelectCustomer(customer);
    }
}
```

#### 2.3 Location Selector Component

**ملف جديد**: `static/src/app/location_selector.js`

```javascript
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class LocationSelector extends Component {
    static template = "pos_perfume_custom.LocationSelector";
    
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            warehouses: [],
            selectedWarehouse: null,
            locations: [],
            selectedLocation: null,
            stockInfo: null,
        });
    }
    
    async loadWarehouses() {
        const warehouses = await this.orm.searchRead(
            'stock.warehouse',
            [],
            ['id', 'name', 'code'],
            { order: 'name' }
        );
        this.state.warehouses = warehouses;
    }
    
    async selectWarehouse(warehouse) {
        this.state.selectedWarehouse = warehouse;
        
        // جلب المواقع التابعة للمستودع
        const locations = await this.orm.searchRead(
            'stock.location',
            [['location_id', 'child_of', warehouse.lot_stock_id]],
            ['id', 'name', 'complete_name'],
            { order: 'complete_name' }
        );
        
        this.state.locations = locations;
        
        // جلب معلومات المخزون من SAP
        if (this.props.product_id) {
            await this.loadStockInfo();
        }
        
        this.props.onSelectWarehouse(warehouse);
    }
    
    async loadStockInfo() {
        // جلب معلومات المخزون من SAP
        const stockInfo = await this.orm.searchRead(
            'sap.product.warehouse.info',
            [
                ['product_id', '=', this.props.product_id],
                ['warehouse_code', '=', this.state.selectedWarehouse.code],
            ],
            ['on_hand', 'committed', 'available'],
            { limit: 1 }
        );
        
        this.state.stockInfo = stockInfo[0] || null;
    }
}
```

#### 2.4 تحديث Order Table

**تحديث**: `static/src/app/pos_perfume_screen.js`

```javascript
// إضافة أعمدة جديدة للجدول
createEmptyLines(count) {
    const lines = [];
    for (let i = 0; i < count; i++) {
        lines.push({
            id: `line_${i}`,
            product_id: null,
            product_code: '',
            product_name: '',
            uom_id: null,          // ⭐ جديد
            uom_name: '',          // ⭐ جديد
            warehouse_id: null,    // ⭐ جديد
            warehouse_name: '',    // ⭐ جديد
            location_id: null,     // ⭐ جديد
            location_name: '',     // ⭐ جديد
            quantity: 1,
            unit_price: 0,
            discount_percent: 0,
            available_qty: 0,      // ⭐ من SAP
            line_total: 0,
        });
    }
    return lines;
}

// معالج لإضافة منتج مع UoM
onAddProduct(productData) {
    // البحث عن أول سطر فارغ
    const emptyLine = this.state.currentOrder.lines.find(l => !l.product_id);
    
    if (emptyLine) {
        Object.assign(emptyLine, {
            product_id: productData.product_id,
            product_code: productData.product_code,
            product_name: productData.product_name,
            uom_id: productData.uom_id,
            uom_name: productData.uom_name,
            unit_price: productData.price,
            quantity: 1,
        });
        
        this.calculateLineTotals(emptyLine);
    } else {
        // إضافة سطر جديد
        this.state.currentOrder.lines.push({
            id: `line_${Date.now()}`,
            ...productData,
            quantity: 1,
            discount_percent: 0,
        });
    }
    
    this.calculateOrderTotals();
}
```

---

### المرحلة 3️⃣: XML Templates

#### 3.1 Product Search Template

**ملف جديد**: `static/src/xml/product_search_uom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates id="template" xml:space="preserve">
    
    <t t-name="pos_perfume_custom.ProductSearchWithUoM">
        <div class="product-search-uom-container">
            <!-- بحث المنتج -->
            <div class="search-section">
                <input 
                    type="text" 
                    class="form-control product-search-input"
                    placeholder="🔍 ابحث عن منتج (الاسم، الكود، الاسم الأجنبي)"
                    t-model="state.searchTerm"
                    t-on-input="() => this.searchProducts(state.searchTerm)"
                />
            </div>
            
            <!-- نتائج البحث -->
            <div class="products-list" t-if="state.products.length > 0">
                <t t-foreach="state.products" t-as="product" t-key="product.id">
                    <div class="product-card" 
                         t-on-click="() => this.selectProduct(product)"
                         t-att-class="{'selected': state.selectedProduct?.id === product.id}">
                        <div class="product-code">
                            <t t-esc="product.default_code or 'N/A'"/>
                        </div>
                        <div class="product-name">
                            <t t-esc="product.name"/>
                        </div>
                        <t t-if="product.foreign_name">
                            <div class="product-foreign-name">
                                <t t-esc="product.foreign_name"/>
                            </div>
                        </t>
                    </div>
                </t>
            </div>
            
            <!-- اختيار وحدة القياس -->
            <div class="uom-section" t-if="state.selectedProduct">
                <h4>اختر وحدة القياس:</h4>
                <div class="uom-list">
                    <t t-foreach="state.availableUoms" t-as="uom" t-key="uom.id">
                        <div class="uom-card"
                             t-on-click="() => this.selectUom(uom)"
                             t-att-class="{'selected': state.selectedUom?.id === uom.id}">
                            <div class="uom-name">
                                <t t-esc="uom.name"/>
                            </div>
                            <div class="uom-price">
                                <t t-esc="uom.price"/> USD
                            </div>
                            <t t-if="uom.quantity_info">
                                <div class="uom-info">
                                    <t t-esc="uom.quantity_info"/>
                                </div>
                            </t>
                        </div>
                    </t>
                </div>
                
                <!-- معلومات السعر -->
                <div class="price-info" t-if="state.priceInfo">
                    <div class="price-detail">
                        <span>السعر:</span>
                        <strong><t t-esc="state.priceInfo.price"/> USD</strong>
                    </div>
                    <div class="price-detail" t-if="state.priceInfo.price_iqd">
                        <span>السعر (دينار):</span>
                        <strong><t t-esc="state.priceInfo.price_iqd"/> IQD</strong>
                    </div>
                </div>
                
                <!-- زر الإضافة -->
                <button class="btn btn-primary btn-lg btn-add-to-order"
                        t-on-click="addToOrder"
                        t-att-disabled="!state.selectedUom">
                    ➕ إضافة إلى الطلب
                </button>
            </div>
        </div>
    </t>
    
</templates>
```

#### 3.2 Customer Search Template

```xml
<t t-name="pos_perfume_custom.CustomerSearch">
    <div class="customer-search-container">
        <div class="customer-search-input-group">
            <input 
                type="text"
                class="form-control customer-search-input"
                placeholder="🔍 ابحث عن عميل (الاسم، الهاتف، البريد)"
                t-model="state.searchTerm"
                t-on-input="() => this.searchCustomers(state.searchTerm)"
                t-on-focus="() => state.showDropdown = true"
            />
            <t t-if="state.selectedCustomer">
                <div class="selected-customer-badge">
                    ✅ <t t-esc="state.selectedCustomer.name"/>
                </div>
            </t>
        </div>
        
        <!-- قائمة العملاء -->
        <div class="customer-dropdown" t-if="state.showDropdown and state.customers.length > 0">
            <t t-foreach="state.customers" t-as="customer" t-key="customer.id">
                <div class="customer-item" t-on-click="() => this.selectCustomer(customer)">
                    <div class="customer-name">
                        <strong><t t-esc="customer.name"/></strong>
                    </div>
                    <t t-if="customer.phone or customer.mobile">
                        <div class="customer-phone">
                            📞 <t t-esc="customer.phone or customer.mobile"/>
                        </div>
                    </t>
                    <t t-if="customer.email">
                        <div class="customer-email">
                            ✉️ <t t-esc="customer.email"/>
                        </div>
                    </t>
                </div>
            </t>
        </div>
    </div>
</t>
```

---

### المرحلة 4️⃣: Backend Methods Support

#### 4.1 إضافة Methods للمنتج

**ملف جديد**: `models/product_product_extended.py`

```python
from odoo import models, api

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    @api.model
    def get_available_uoms_with_prices(self, product_id, pricelist_id=None):
        """
        Get all available UoMs with their prices from pricelist
        """
        product = self.browse(product_id)
        if not pricelist_id:
            pricelist_id = self.env.ref('product.list0').id
        
        pricelist = self.env['product.pricelist'].browse(pricelist_id)
        
        # Get all pricelist items for this product
        items = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist_id),
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('compute_price', '=', 'fixed'),
        ])
        
        uoms = []
        seen_uom_ids = set()
        
        for item in items:
            if item.product_packaging_id:
                uom = self.env['uom.uom'].browse(item.product_packaging_id.id)
                if uom.id not in seen_uom_ids:
                    uoms.append({
                        'id': uom.id,
                        'name': uom.name,
                        'price': item.fixed_price,
                        'quantity_info': f"{uom.factor_inv} {product.uom_id.name}" if hasattr(uom, 'factor_inv') else '',
                    })
                    seen_uom_ids.add(uom.id)
        
        # Add base UoM
        if product.uom_id.id not in seen_uom_ids:
            uoms.insert(0, {
                'id': product.uom_id.id,
                'name': product.uom_id.name,
                'price': product.list_price,
                'quantity_info': 'الوحدة الأساسية',
            })
        
        return uoms
```

#### 4.2 Methods للـ Pricelist

```python
class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'
    
    @api.model
    def get_price_for_uom(self, pricelist_id, product_id, uom_id):
        """
        Get price for specific product and UoM
        """
        pricelist = self.browse(pricelist_id)
        product = self.env['product.product'].browse(product_id)
        uom = self.env['uom.uom'].browse(uom_id)
        
        # Search for exact match
        item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist_id),
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('product_packaging_id', '=', uom_id),
            ('compute_price', '=', 'fixed'),
        ], limit=1)
        
        if item:
            price = item.fixed_price
        else:
            # Use base price
            price = product.list_price
            # Convert if needed
            if uom != product.uom_id:
                price = product.uom_id._compute_price(price, uom)
        
        # Calculate IQD
        iqd_currency = self.env.ref('base.IQD', raise_if_not_found=False)
        usd_currency = self.env.ref('base.USD', raise_if_not_found=False)
        
        price_iqd = 0
        if iqd_currency and usd_currency:
            price_iqd = usd_currency._convert(
                price, iqd_currency, 
                self.env.company, 
                fields.Date.today()
            )
        
        return {
            'price': price,
            'price_iqd': price_iqd,
            'currency': 'USD',
            'uom': uom.name,
        }
```

---

### المرحلة 5️⃣: Integration & Testing

#### 5.1 تحديث __manifest__.py

```python
'depends': [
    'point_of_sale',
    'product',
    'stock',
    'sale',
    'mail',
    'uom',                        # ⭐ جديد
    'uom_in_pricelist',          # ⭐ جديد
    'sap_integration',           # ⭐ جديد
],
```

#### 5.2 Security Updates

```csv
# security/ir.model.access.csv
access_product_pricelist_item_user,access_product_pricelist_item_user,product.model_product_pricelist_item,base.group_user,1,0,0,0
access_uom_uom_user,access_uom_uom_user,uom.model_uom_uom,base.group_user,1,0,0,0
access_sap_warehouse_info_user,access_sap_warehouse_info_user,sap_integration.model_sap_product_warehouse_info,base.group_user,1,0,0,0
```

---

## 📋 ملخص التعديلات / Summary of Changes

### Backend (Python):
1. ✅ إضافة `product_uom_id` إلى `pos.perfume.order.line`
2. ✅ إضافة `location_id` لدعم مواقع محددة
3. ✅ إضافة `pricelist_id` إلى `pos.perfume.order`
4. ✅ Methods لجلب UoMs مع الأسعار
5. ✅ Methods لجلب معلومات المخزون من SAP
6. ✅ تحديث `_compute_available_qty` للربط مع SAP

### Frontend (JavaScript/OWL):
1. ✅ Component جديد: `ProductSearchWithUoM`
2. ✅ Component جديد: `CustomerSearch`
3. ✅ Component جديد: `LocationSelector`
4. ✅ تحديث `PosPerfumeScreen` لدعم الميزات الجديدة
5. ✅ إضافة أعمدة UoM و Location للجدول

### XML Templates:
1. ✅ Template لبحث المنتجات مع UoM
2. ✅ Template لبحث العملاء
3. ✅ Template لاختيار المواقع
4. ✅ تحديث جدول الطلب

### SCSS Styles:
1. ✅ تنسيقات للـ Components الجديدة
2. ✅ تحسين UX للـ dropdowns
3. ✅ دعم RTL للنصوص العربية

---

## 🚀 خطوات التنفيذ / Implementation Steps

### الخطوة 1: Backend
```bash
1. تحديث models/pos_perfume_order.py
2. إضافة models/product_product_extended.py
3. تحديث security/ir.model.access.csv
4. تحديث __init__.py
```

### الخطوة 2: Frontend Components
```bash
1. إضافة static/src/app/product_search_uom.js
2. إضافة static/src/app/customer_search.js
3. إضافة static/src/app/location_selector.js
4. تحديث static/src/app/pos_perfume_screen.js
```

### الخطوة 3: Templates
```bash
1. إضافة static/src/xml/product_search_uom.xml
2. إضافة static/src/xml/customer_search.xml
3. إضافة static/src/xml/location_selector.xml
4. تحديث static/src/xml/pos_perfume_screen.xml
```

### الخطوة 4: Styles
```bash
1. تحديث static/src/scss/perfume_pos.scss
2. إضافة تنسيقات الـ Components الجديدة
```

### الخطوة 5: Manifest & Dependencies
```bash
1. تحديث __manifest__.py
2. إضافة dependencies
3. تحديث assets
```

### الخطوة 6: Testing
```bash
1. Upgrade module
2. Test product search with UoM
3. Test customer search
4. Test location selection
5. Test order creation
6. Test Sale Order integration
```

---

## 🎯 النتيجة المتوقعة / Expected Result

بعد تنفيذ هذه الخطة، ستكون واجهة POS PERFUME:

✅ **متكاملة تماماً** مع Sale Order
✅ تدعم **اختيار وحدة القياس** لكل منتج
✅ تدعم **اختيار الموقع** (Warehouse + Location)
✅ تدعم **بحث متقدم عن العملاء**
✅ تجلب **الأسعار الصحيحة** من Pricelist حسب UoM
✅ تعرض **المخزون المتاح** من SAP
✅ تحافظ على **التصميم الحالي** (Excel-like table)
✅ تدعم **التنقل بالأسهم** الموجود

---

## 📝 ملاحظات مهمة / Important Notes

1. **الربط مع SAP**: سيتم استخدام `sap.product.warehouse.info` لجلب المخزون الفعلي
2. **UoM Pricing**: سيتم استخدام `uom_in_pricelist` للحصول على الأسعار
3. **Customer Pricelist**: سيتم جلب pricelist العميل تلقائياً عند اختياره
4. **Real-time Stock**: عرض المخزون المتاح في الوقت الفعلي
5. **Validation**: التحقق من الكمية المتاحة قبل الحفظ

---

## 🔄 الخطوات التالية / Next Steps

هل تريد:
1. ✅ **البدء بالتنفيذ** خطوة بخطوة؟
2. 📊 **مراجعة الخطة** وإضافة تفاصيل؟
3. 🎨 **رؤية mockup** للواجهة الجديدة؟
4. 📝 **قائمة Tasks** تفصيلية؟

أخبرني وسأبدأ فوراً! 🚀

