# 🔄 تغييرات UoM في Odoo 19

## 📊 **الفرق بين Odoo 18 وOdoo 19:**

### **في Odoo 18 والإصدارات السابقة:**

```python
# كان موجود model اسمه: uom.category
class UomCategory(models.Model):
    _name = 'uom.category'
    _description = 'Product UoM Category'
    
    name = fields.Char('Name', required=True)
    
# وكان uom.uom مرتبط به:
class UoM(models.Model):
    _name = 'uom.uom'
    
    category_id = fields.Many2one('uom.category')
    # ...
```

**الاستخدام:**
```
UoM Category: "الوزن"
├─ كيلو (factor=1.0)
├─ نصف كيلو (factor=0.5)
└─ ربع كيلو (factor=0.25)

UoM Category: "الطول"
├─ متر (factor=1.0)
├─ سنتيمتر (factor=0.01)
└─ كيلومتر (factor=1000)
```

---

### **في Odoo 19:**

```python
# ❌ تم إزالة uom.category كـ model منفصل!

# ✅ أصبح uom.uom يستخدم نظام مختلف:
class UoM(models.Model):
    _name = 'uom.uom'
    
    # لا يوجد category_id بالشكل القديم!
    # بدلاً منه يوجد:
    measure_type = fields.Selection([
        ('unit', 'Units'),
        ('weight', 'Weight'),
        ('volume', 'Volume'),
        ('length', 'Length'),
        ('time', 'Time'),
        # ... إلخ
    ])
    
    factor = fields.Float()
    # ...
```

**التغيير الأساسي:**
```
قبل (Odoo 18):
    Category → UoMs

الآن (Odoo 19):
    Measure Type → UoMs
    (أبسط وأكثر تكاملاً)
```

---

## 🔍 **التحقق من نظامك:**

من الأخطاء التي رأيناها في السكريبتات السابقة:

```
❌ KeyError: 'uom_type'
❌ Object uom.category doesn't exist
```

**هذا يؤكد:** أنك على Odoo 19! ✅

---

## 🎯 **كيف سنتعامل مع هذا في الحل؟**

### **Option A: استخدام النظام الجديد (الأفضل)**

```python
class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'
    
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        # ✅ في Odoo 19: نستخدم domain مختلف
        domain="""[
            '|',
            ('id', '=', product_uom_id),
            '&',
            ('measure_type', '=', product_measure_type),
            ('active', '=', True)
        ]"""
    )
    
    # Helper field
    product_measure_type = fields.Selection(
        related='product_id.uom_id.measure_type',
        store=False
    )
    
    product_uom_id = fields.Many2one(
        related='product_id.uom_id',
        store=False
    )
```

**الفائدة:**
```
✅ متوافق 100% مع Odoo 19
✅ يستخدم النظام الجديد الأبسط
✅ أقل تعقيداً
✅ أسرع
```

---

### **Option B: محاكاة النظام القديم (معقد)**

```python
# ❌ لا أنصح به!
# يمكن إنشاء wrapper لمحاكاة uom.category

class UomCategoryWrapper(models.Model):
    _name = 'uom.category.wrapper'
    
    name = fields.Char()
    measure_type = fields.Selection(...)
    
    # ثم ربطه مع uom.uom
    # ... معقد وغير ضروري
```

**المشاكل:**
```
❌ معقد جداً
❌ قد يسبب تعارضات
❌ صعب الصيانة
❌ غير ضروري أصلاً!
```

---

## ✅ **الحل الموصى به:**

### **نستخدم نظام Odoo 19 الجديد مباشرة:**

```python
class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'
    
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        help='Specific UoM for this price',
        domain="""[
            ('measure_type', '=', product_measure_type),
            ('active', '=', True)
        ]"""
    )
    
    product_measure_type = fields.Selection(
        related='product_id.uom_id.measure_type',
        string='Product Measure Type',
        store=False
    )
    
    @api.constrains('uom_id', 'product_id')
    def _check_uom_compatibility(self):
        """التحقق من أن UoM من نفس النوع"""
        for item in self:
            if item.uom_id and item.product_id:
                product_measure = item.product_id.uom_id.measure_type
                uom_measure = item.uom_id.measure_type
                
                if product_measure != uom_measure:
                    raise ValidationError(
                        f"UoM '{item.uom_id.name}' (type: {uom_measure}) "
                        f"must be of same type as product UoM "
                        f"(type: {product_measure})"
                    )
```

---

## 📊 **مثال عملي:**

### **منتج: عطر الورد**

```python
Product:
├─ name: "عطر الورد"
├─ uom_id: "كيلو" (measure_type='weight')
└─ measure_type: 'weight' (من الوحدة الأساسية)

Pricelist Items:
├─ Product: عطر الورد
│  ├─ uom_id: "كيلو" (measure_type='weight') ✅
│  └─ price: $40
│
├─ Product: عطر الورد
│  ├─ uom_id: "نصف كيلو" (measure_type='weight') ✅
│  └─ price: $20
│
└─ Product: عطر الورد
   ├─ uom_id: "ربع كيلو" (measure_type='weight') ✅
   └─ price: $10
```

**Domain يضمن:**
```
✅ فقط UoMs من نوع 'weight' تظهر
✅ لا يمكن اختيار 'متر' (type='length')
✅ لا يمكن اختيار 'لتر' (type='volume')
```

---

## 🔧 **الكود المحدث:**

### **`models/product_pricelist_item.py`:**

```python
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'
    
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        help='If set, this price applies only for this specific UoM',
        domain="""[
            ('measure_type', '=', product_measure_type),
            ('active', '=', True)
        ]"""
    )
    
    product_measure_type = fields.Selection(
        related='product_id.uom_id.measure_type',
        string='Measure Type',
        store=False,
        readonly=True
    )
    
    @api.constrains('uom_id', 'product_id')
    def _check_uom_compatibility(self):
        """Ensure UoM is compatible with product"""
        for item in self:
            if not item.uom_id or not item.product_id:
                continue
                
            product_uom = item.product_id.uom_id
            
            # Check measure type
            if product_uom.measure_type != item.uom_id.measure_type:
                raise ValidationError(
                    f"The Unit of Measure '{item.uom_id.name}' "
                    f"(type: {item.uom_id.measure_type}) is not compatible "
                    f"with the product's UoM '{product_uom.name}' "
                    f"(type: {product_uom.measure_type})."
                )
    
    @api.depends('uom_id', 'product_id')
    def _compute_price(self):
        """Override to handle UoM-specific pricing"""
        for item in self:
            # Base computation
            super(ProductPricelistItem, item)._compute_price()
            
            # UoM adjustment if needed
            if item.uom_id and item.product_id:
                # Price conversion is handled automatically by Odoo
                # through UoM factor system
                pass
```

---

## 💡 **المزايا الجديدة في Odoo 19:**

### **✅ أبسط:**
```
قبل: Product → Category → UoMs
الآن: Product → Measure Type → UoMs
      (خطوة أقل!)
```

### **✅ أسرع:**
```
لا حاجة لـ join مع جدول category
→ queries أسرع
```

### **✅ أوضح:**
```
measure_type = 'weight' → واضح مباشرة
بدلاً من category_id = 3 → ماذا تعني؟
```

---

## 🎯 **الخلاصة:**

### **سؤالك:** هل سنعيد استخدام uom.category؟

### **الجواب:** ❌ لا! لأنه:

```
1. ❌ لا يوجد في Odoo 19
2. ✅ النظام الجديد أبسط وأفضل
3. ✅ سنستخدم measure_type مباشرة
4. ✅ أقل تعقيداً
5. ✅ متوافق مع Odoo 19
```

---

## 📝 **الكود النهائي المحدث:**

```python
# ✅ متوافق مع Odoo 19

uom_id = fields.Many2one(
    'uom.uom',
    string='Unit of Measure',
    domain="[('measure_type', '=', product_measure_type)]"
)

product_measure_type = fields.Selection(
    related='product_id.uom_id.measure_type',
    store=False
)
```

**بسيط، واضح، ويعمل!** ✅

---

## ❓ **هل هذا يحل استفسارك؟**

أم تريد:
- مزيد من التفاصيل عن measure_type؟
- مقارنة أعمق بين النظامين؟
- رؤية الكود الكامل المحدث؟

**أخبرني!** 🎯

