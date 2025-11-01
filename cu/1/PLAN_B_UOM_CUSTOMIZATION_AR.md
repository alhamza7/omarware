# 🎯 الخطة الكاملة: UoM Customization في Pricelists

## 📊 **نظرة عامة:**

### **الهدف:**
إضافة حقل **UoM** إلى `product.pricelist.item` بحيث يمكن تحديد سعر مختلف لكل وحدة قياس.

### **النتيجة المتوقعة:**
```
Pricelist Item:
├─ Product: عطر الورد
├─ UoM: كيلو → السعر: $40
│
├─ Product: عطر الورد
├─ UoM: نصف كيلو → السعر: $20
│
└─ Product: عطر الورد
    ├─ UoM: ربع كيلو → السعر: $10
```

---

## 🏗️ **المتطلبات التقنية:**

### **1️⃣ تعديلات على Models:**

#### **A) تعديل `product.pricelist.item`:**
```python
# إضافة حقل UoM
uom_id = fields.Many2one(
    'uom.uom',
    string='Unit of Measure',
    domain="[('category_id', '=', product_uom_category_id)]",
    help='Specific UoM for this price rule'
)

# حقل مساعد للتحقق من الفئة
product_uom_category_id = fields.Many2one(
    related='product_id.uom_id.category_id',
    store=False
)
```

#### **B) تعديل منطق حساب السعر:**
```python
def _compute_price(self):
    # الكود الحالي
    price = super()._compute_price()
    
    # الإضافة: التحقق من UoM
    if self.uom_id and order_line.product_uom != self.uom_id:
        # تحويل السعر حسب UoM
        price = self.uom_id._compute_price(
            price, 
            order_line.product_uom
        )
    
    return price
```

### **2️⃣ تعديلات على Views:**

#### **A) Form View:**
```xml
<field name="product_id"/>
<field name="uom_id" 
       attrs="{'invisible': [('applied_on', '!=', '0_product_variant')]}"/>
<field name="min_quantity"/>
<field name="fixed_price"/>
```

#### **B) Tree View:**
```xml
<tree>
    <field name="product_tmpl_id"/>
    <field name="product_id"/>
    <field name="uom_id"/>
    <field name="min_quantity"/>
    <field name="fixed_price"/>
</tree>
```

### **3️⃣ Domain وConstraints:**

```python
@api.constrains('product_id', 'uom_id')
def _check_uom_category(self):
    for item in self:
        if item.uom_id and item.product_id:
            if item.uom_id.category_id != item.product_id.uom_id.category_id:
                raise ValidationError(
                    "UoM must be in the same category as product UoM"
                )

@api.constrains('product_id', 'uom_id', 'pricelist_id')
def _check_unique_uom_per_product(self):
    # التحقق من عدم تكرار نفس المنتج + UoM في نفس Pricelist
    for item in self:
        if item.product_id and item.uom_id:
            duplicate = self.search([
                ('pricelist_id', '=', item.pricelist_id.id),
                ('product_id', '=', item.product_id.id),
                ('uom_id', '=', item.uom_id.id),
                ('id', '!=', item.id)
            ])
            if duplicate:
                raise ValidationError(
                    f"Price already defined for {item.product_id.name} "
                    f"with UoM {item.uom_id.name}"
                )
```

---

## 📁 **هيكل الـ Module:**

```
addons/
└── product_pricelist_uom/
    ├── __init__.py
    ├── __manifest__.py
    ├── models/
    │   ├── __init__.py
    │   ├── product_pricelist_item.py
    │   └── sale_order_line.py
    ├── views/
    │   └── product_pricelist_views.xml
    ├── security/
    │   └── ir.model.access.csv
    ├── data/
    │   └── demo_data.xml (optional)
    └── README.md
```

---

## 🔧 **الملفات المطلوبة:**

### **1️⃣ `__manifest__.py`:**
```python
{
    'name': 'Product Pricelist UoM',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Add UoM support to Pricelist Items',
    'depends': ['product', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_pricelist_views.xml',
    ],
    'installable': True,
    'application': False,
}
```

### **2️⃣ `models/product_pricelist_item.py`:**
```python
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'
    
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        domain="[('category_id', '=', product_uom_category_id)]",
        help='If set, this price will only apply for this specific UoM'
    )
    
    product_uom_category_id = fields.Many2one(
        'uom.category',
        related='product_id.uom_id.category_id',
        store=False,
        string='Product UoM Category'
    )
    
    @api.constrains('product_id', 'uom_id')
    def _check_uom_category(self):
        for item in self:
            if item.uom_id and item.product_id:
                if item.uom_id.category_id != item.product_id.uom_id.category_id:
                    raise ValidationError(
                        f"The UoM '{item.uom_id.name}' must be in the same "
                        f"category as the product's UoM"
                    )
    
    def _compute_price(self, product_id, quantity, uom, date=False, currency=False):
        """Override to consider UoM in price calculation"""
        # Find matching rule with UoM
        matching_rule = self._find_matching_rule_with_uom(
            product_id, quantity, uom, date
        )
        
        if matching_rule:
            return matching_rule._compute_base_price(
                product_id, quantity, uom, date, currency
            )
        
        # Fallback to standard behavior
        return super()._compute_price(
            product_id, quantity, uom, date, currency
        )
    
    def _find_matching_rule_with_uom(self, product_id, quantity, uom, date):
        """Find pricelist item that matches product and UoM"""
        domain = [
            ('product_id', '=', product_id.id),
            ('uom_id', '=', uom.id if uom else False),
        ]
        
        return self.search(domain, limit=1, order='fixed_price desc')
```

### **3️⃣ `views/product_pricelist_views.xml`:**
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Inherit Form View -->
    <record id="product_pricelist_item_form_view_inherit" model="ir.ui.view">
        <field name="name">product.pricelist.item.form.uom</field>
        <field name="model">product.pricelist.item</field>
        <field name="inherit_id" ref="product.product_pricelist_item_form_view"/>
        <field name="arch" type="xml">
            
            <!-- Add UoM field after product_id -->
            <field name="product_id" position="after">
                <field name="product_uom_category_id" invisible="1"/>
                <field name="uom_id" 
                       attrs="{'invisible': [('applied_on', '!=', '0_product_variant')],
                               'required': [('applied_on', '=', '0_product_variant')]}"
                       options="{'no_create': True}"/>
            </field>
            
        </field>
    </record>
    
    <!-- Inherit Tree View -->
    <record id="product_pricelist_item_tree_view_inherit" model="ir.ui.view">
        <field name="name">product.pricelist.item.tree.uom</field>
        <field name="model">product.pricelist.item</field>
        <field name="inherit_id" ref="product.product_pricelist_item_tree_view"/>
        <field name="arch" type="xml">
            
            <field name="product_id" position="after">
                <field name="uom_id" optional="show"/>
            </field>
            
        </field>
    </record>
</odoo>
```

---

## ⏱️ **خطة التنفيذ (أسبوع عمل):**

### **اليوم 1-2: التحليل والتصميم**
```
✅ مراجعة كود Odoo الحالي
✅ تحديد نقاط التعديل بالضبط
✅ تصميم البنية التقنية
✅ إنشاء هيكل الـ module
✅ كتابة الـ models الأساسية
```

### **اليوم 3-4: التطوير**
```
✅ تعديل product.pricelist.item
✅ تعديل منطق حساب السعر
✅ إنشاء Views
✅ إضافة Constraints
✅ كتابة Helper Methods
```

### **اليوم 5: الاختبار**
```
✅ Unit Tests
✅ Integration Tests
✅ اختبار في بيئة Development
✅ اختبار سيناريوهات مختلفة:
   • منتج + UoM واحد
   • منتج + UoM متعددة
   • Pricelists متعددة
   • تحويل UoM تلقائي
```

### **اليوم 6: Migration**
```
✅ Migration script لتحديث البيانات الحالية
✅ نقل الأسعار من SAP إلى النظام الجديد
✅ التحقق من البيانات
```

### **اليوم 7: Documentation والتسليم**
```
✅ كتابة Documentation
✅ تدريب المستخدمين
✅ Deploy على Production
✅ المتابعة والدعم
```

---

## 💰 **التكلفة المقدرة:**

### **تطوير:**
```
Developer Rate: $50-100/hour (متوسط عالمي)
أو
Developer Rate: 50,000-100,000 IQD/hour (عراقي)

إجمالي الوقت: 40-50 ساعة

التكلفة الإجمالية:
• عالمي: $2,000 - $5,000
• محلي: حسب السوق العراقي
```

### **بدائل:**
```
Option A: تطوير داخلي (إذا عندك developer)
          → تكلفة = الوقت فقط
          
Option B: Freelancer
          → $30-60/hour
          → إجمالي: $1,200 - $3,000
          
Option C: شركة تطوير
          → $80-150/hour
          → إجمالي: $3,200 - $7,500
```

---

## ⚠️ **المخاطر والتحديات:**

### **1️⃣ التحديات التقنية:**

```
⚠️ تعقيد منطق Pricelist في Odoo
   → الحل: دراسة الكود جيداً قبل التعديل
   
⚠️ تأثير على الأداء
   → الحل: Indexing صحيح + Caching
   
⚠️ تعارض مع modules أخرى
   → الحل: اختبار شامل مع جميع الـ modules
```

### **2️⃣ مخاطر البيانات:**

```
⚠️ Migration البيانات الحالية
   → الحل: Backup كامل + اختبار على نسخة
   
⚠️ فقدان أسعار أثناء التحويل
   → الحل: Migration script محكم + تحقق مزدوج
```

### **3️⃣ مخاطر الاستخدام:**

```
⚠️ تعقيد للمستخدمين
   → الحل: تدريب جيد + واجهة واضحة
   
⚠️ أخطاء في إدخال البيانات
   → الحل: Constraints قوية + Validation
```

---

## ✅ **المزايا النهائية:**

### **قصيرة المدى:**
```
✅ نظام احترافي من البداية
✅ مرونة كاملة
✅ تكامل تام مع Odoo
```

### **طويلة المدى:**
```
✅ صيانة صفر
✅ قابل للتوسع
✅ متوافق مع الترقيات
✅ استثمار لمرة واحدة
```

---

## 🎯 **نقاط للمناقشة:**

### **1️⃣ الوقت:**
```
❓ هل أسبوع واحد مقبول؟
❓ أم تحتاج أسرع؟
❓ هل يمكن التأجيل لوقت أقل ضغط؟
```

### **2️⃣ الموارد:**
```
❓ هل عندك developer داخلي؟
❓ أم نحتاج freelancer/شركة؟
❓ ما هو الـ budget المتاح؟
```

### **3️⃣ النطاق:**
```
❓ هل نطبقه على جميع المنتجات؟
❓ أم فقط فئة معينة؟
❓ كم عدد UoMs المتوقع لكل منتج؟
```

### **4️⃣ البيانات:**
```
❓ هل SAP لديه أسعار UoM فعلاً؟
❓ أم نحتاج إدخالها يدوياً؟
❓ كم عدد الأسعار المتوقع؟
```

### **5️⃣ الاختبار:**
```
❓ هل عندك بيئة Test منفصلة؟
❓ من سيقوم بالاختبار؟
❓ ما هي السيناريوهات الحرجة؟
```

---

## 📋 **Checklist قبل البدء:**

### **متطلبات:**
```
☐ Odoo 19 Enterprise/Community
☐ بيئة Development منفصلة
☐ Backup كامل للبيانات
☐ Developer متفرغ (أو budget للتعاقد)
☐ وقت للاختبار (أسبوع على الأقل)
☐ خطة للتدريب
```

### **معلومات مطلوبة:**
```
☐ عدد المنتجات
☐ عدد UoMs المختلفة
☐ عدد Pricelists
☐ مصدر البيانات (SAP؟ يدوي؟)
☐ المستخدمون المتوقعون
```

---

## 🚀 **الخطوة التالية:**

### **إذا قررت المتابعة:**

1. **نناقش التفاصيل:**
   - الوقت المتاح
   - الموارد (developer/budget)
   - النطاق بالضبط

2. **أبدأ التطوير:**
   - يمكنني كتابة الكود الكامل
   - مع شرح كل جزء
   - واختباره معك

3. **التنفيذ والتسليم:**
   - Installation
   - Migration
   - Testing
   - Training

---

## ❓ **أسئلتي لك:**

1. **متى تريد البدء؟**
2. **هل عندك developer أم نحتاج نبحث؟**
3. **ما هو الـ budget المتاح؟**
4. **كم عدد المنتجات تقريباً؟**
5. **هل SAP لديه بيانات UoM Prices؟**

**أخبرني وسنتناقش في التفاصيل!** 🎯

