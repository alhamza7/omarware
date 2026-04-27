# شرح جلب التسعيرات حسب وحدة القياس من SAP

## ✅ **الإجابة المختصرة: نعم، يتم جلب التسعيرات حسب وحدة القياس**

النظام مُجهَّز بالكامل لجلب وإدارة الأسعار المختلفة لكل وحدة قياس من SAP وإضافتها إلى المنتجات في Odoo.

---

## 📋 **كيف يعمل النظام؟**

### **1. هيكل البيانات من SAP**

عند جلب منتج من SAP، تأتي البيانات بهذا الشكل:

```json
{
  "ItemCode": "ITEM001",
  "ItemPrices": [
    {
      "PriceList": 1,
      "Price": 100.00,
      "Currency": "USD",
      "UoMCode": "PC",              // وحدة القياس الأساسية
      "UoMPrices": [                // 🔥 الأسعار حسب وحدة القياس
        {
          "UoMEntry": 1,            // معرف وحدة القياس في SAP
          "Price": 85.00,           // السعر لهذه الوحدة
          "UoMCode": "BOX"          // كود الوحدة (صندوق)
        },
        {
          "UoMEntry": 2,
          "Price": 1000.00,
          "UoMCode": "CARTON"       // كود الوحدة (كرتونة)
        }
      ]
    }
  ]
}
```

### **2. عملية الاستيراد - المرحلة 3**

في المعالج `sap.product.complete.migration`:

```python
# السطر 282-293
if self.stage3_pricelists:
    stage3_result = self._stage3_import_pricelists()
    self.total_pricelists = stage3_result.get('pricelists', 0)
    self.total_prices = stage3_result.get('prices', 0)
```

### **3. معالجة الأسعار الأساسية**

في `sap_product_pricelist_sync.py` - الدالة `sync_product_prices_from_sap`:

```python
# السطور 173-226
for price_data in sap_prices_data:
    # جلب السعر الأساسي
    pricelist_num = int(price_data.get('PriceList', 0))
    price = float(price_data.get('Price'))
    uom_code = price_data.get('UoMCode', '')
    
    # إنشاء سجل في قاعدة البيانات
    sync_record = self.create({
        'product_id': product.id,
        'sap_pricelist_num': pricelist_num,
        'price': price,
        'uom_code': uom_code,
        # ... باقي الحقول
    })
    
    # إنشاء قاعدة سعر في قائمة الأسعار
    self._create_or_update_pricelist_item(
        sync_record, product, odoo_pricelist, price, uom
    )
```

### **4. معالجة الأسعار حسب وحدة القياس** 🔥

الجزء الأهم - السطور 227-281:

```python
# ========== معالجة الأسعار الخاصة بكل وحدة قياس ==========
uom_prices = price_data.get('UoMPrices', [])
if uom_prices:
    _logger.info(f"Processing {len(uom_prices)} UoM-specific prices")
    
    for uom_price_data in uom_prices:
        # الحصول على معرف وحدة القياس من SAP
        uom_entry = uom_price_data.get('UoMEntry')
        uom_price_value = uom_price_data.get('Price')
        
        # البحث عن وحدة القياس المطابقة في Odoo
        uom_sync = self.env['sap.uom.sync'].search([
            ('backend_id', '=', backend.id),
            ('sap_uom_entry', '=', uom_entry)  # الربط بين SAP و Odoo
        ], limit=1)
        
        if uom_sync and uom_sync.odoo_uom_id:
            uom_specific = uom_sync.odoo_uom_id
            uom_price = float(uom_price_value)
            
            # إنشاء سجل سعر منفصل لهذه الوحدة
            uom_sync_record = self.create({
                'product_id': product.id,
                'sap_pricelist_num': pricelist_num,
                'price': uom_price,           # 🔥 السعر الخاص بهذه الوحدة
                'uom_id': uom_specific.id,    # 🔥 وحدة القياس المحددة
                # ... باقي الحقول
            })
            
            # إنشاء قاعدة سعر في قائمة الأسعار لهذه الوحدة
            self._create_or_update_pricelist_item(
                uom_sync_record, product, odoo_pricelist, 
                uom_price, uom_specific  # 🔥 السعر والوحدة الخاصة
            )
```

---

## 🗄️ **التخزين في قاعدة البيانات**

### **جدول `sap_product_pricelist_sync`**

يحتوي على سجل منفصل لكل سعر حسب وحدة القياس:

| product_id | sap_pricelist_num | uom_id | uom_code | price | currency |
|------------|-------------------|--------|----------|-------|----------|
| 123        | 1                 | NULL   | PC       | 100.00| USD      |
| 123        | 1                 | 45     | BOX      | 85.00 | USD      |
| 123        | 1                 | 46     | CARTON   | 1000.00| USD     |

**الحقول المهمة:**

```python
# السطور 83-92 من sap_product_pricelist_sync.py
uom_id = fields.Many2one(
    'uom.uom',
    string='Unit of Measure',
    help="Specific UoM for this price (if applicable)"  # 🔥 وحدة قياس محددة
)
uom_code = fields.Char(
    string='SAP UoM Code',
    help="SAP UoM code for this price"
)
```

### **جدول `product_pricelist_item`**

يتم إنشاء قاعدة سعر منفصلة لكل وحدة قياس:

```python
# السطور 376-426
def _create_or_update_pricelist_item(self, sync_record, product, 
                                      pricelist, price, uom=None):
    """إنشاء أو تحديث عنصر في قائمة الأسعار"""
    
    item_vals = {
        'pricelist_id': pricelist.id,
        'product_id': product.id,
        'applied_on': '0_product_variant',
        'compute_price': 'fixed',
        'fixed_price': price,        # 🔥 السعر الخاص
        'min_quantity': 1,
        # وحدة القياس تُضاف هنا إذا كانت محددة
    }
    
    pricelist_item = self.env['product.pricelist.item'].create(item_vals)
```

---

## 🔗 **ربط وحدات القياس**

### **جدول `sap.uom.sync`**

يربط بين وحدات القياس في SAP ووحدات القياس في Odoo:

```python
# من sap_uom.py
class SapUomSync(models.Model):
    _name = 'sap.uom.sync'
    
    sap_uom_entry = fields.Integer('SAP UoM Entry')  # 🔥 المعرف في SAP
    sap_uom_id = fields.Char('SAP UoM Code')         # الكود في SAP
    odoo_uom_id = fields.Many2one('uom.uom')         # 🔥 الوحدة في Odoo
```

**مثال:**

| sap_uom_entry | sap_uom_id | odoo_uom_id | odoo_uom_name |
|---------------|------------|-------------|---------------|
| 1             | BOX        | 45          | صندوق         |
| 2             | CARTON     | 46          | كرتونة        |
| 3             | PC         | 1           | قطعة          |

---

## 📊 **مثال عملي كامل**

### **البيانات من SAP:**

```json
{
  "ItemCode": "PERFUME001",
  "ItemPrices": [
    {
      "PriceList": 1,
      "PriceListName": "Retail",
      "Price": 50.00,
      "Currency": "USD",
      "UoMCode": "PC",
      "UoMPrices": [
        {
          "UoMEntry": 10,
          "UoMCode": "BOX",
          "Price": 45.00
        },
        {
          "UoMEntry": 11,
          "UoMCode": "DOZEN",
          "Price": 500.00
        }
      ]
    }
  ]
}
```

### **النتيجة في Odoo:**

**في `sap_product_pricelist_sync`:**
- سجل 1: المنتج PERFUME001، قائمة 1، بدون وحدة محددة، السعر 50.00$
- سجل 2: المنتج PERFUME001، قائمة 1، وحدة صندوق، السعر 45.00$
- سجل 3: المنتج PERFUME001، قائمة 1، وحدة درزن، السعر 500.00$

**في `product_pricelist_item`:**
- قاعدة 1: PERFUME001 في قائمة Retail = 50.00$ (للوحدة الأساسية)
- قاعدة 2: PERFUME001 في قائمة Retail = 45.00$ (للصندوق)
- قاعدة 3: PERFUME001 في قائمة Retail = 500.00$ (للدرزن)

---

## ⚙️ **كيفية التشغيل**

### **1. استيراد كامل (مع الأسعار)**

```python
# من واجهة Odoo:
# SAP > Product Migration > Complete Migration
# تأكد من تفعيل: ✅ Stage 3: Import Pricelists
```

### **2. استيراد الأسعار فقط**

```python
# من Python:
pricelist_sync = env['sap.product.pricelist.sync']
result = pricelist_sync.import_all_pricelists_from_sap(backend, batch_size=100)
```

### **3. استيراد أسعار منتج واحد**

```python
# من Python:
product = env['product.product'].search([('default_code', '=', 'ITEM001')])
sap_prices = [...]  # البيانات من SAP
pricelist_sync.sync_product_prices_from_sap(product, backend, sap_prices)
```

---

## 📝 **السجلات في قاعدة البيانات**

### **القيد الفريد:**

```sql
-- السطور 145-148
CONSTRAINT unique_product_pricelist_uom 
UNIQUE(product_id, backend_id, sap_pricelist_num, uom_id)
```

هذا يضمن عدم تكرار السعر لنفس المنتج في نفس قائمة الأسعار لنفس وحدة القياس.

---

## ✅ **الخلاصة**

| السؤال | الإجابة |
|---------|---------|
| **هل يتم جلب التسعيرات حسب وحدة القياس؟** | ✅ **نعم** |
| **هل يتم إضافتها إلى المنتجات؟** | ✅ **نعم** - كسجلات منفصلة |
| **هل يتم إنشاء قواعد في قوائم الأسعار؟** | ✅ **نعم** - في `product.pricelist.item` |
| **هل يتم ربط وحدات القياس بين SAP و Odoo؟** | ✅ **نعم** - عبر `sap.uom.sync` |
| **كم سجل لكل منتج؟** | سجل لكل سعر × وحدة قياس × قائمة أسعار |

---

## 🔍 **الكود المرجعي**

| الملف | السطور | الوظيفة |
|-------|--------|---------|
| `sap_product_pricelist_sync.py` | 227-281 | معالجة `UoMPrices` |
| `sap_product_pricelist_sync.py` | 152-293 | `sync_product_prices_from_sap()` |
| `sap_product_pricelist_sync.py` | 376-426 | `_create_or_update_pricelist_item()` |
| `sap_product_complete_migration.py` | 720-735 | `_stage3_import_pricelists()` |
| `sap_uom.py` | 1-465 | إدارة وحدات القياس |

---

## 📌 **ملاحظات مهمة**

1. ✅ **يتم جلب الأسعار تلقائياً** في المرحلة 3 من عملية الاستيراد الكامل
2. ✅ **كل وحدة قياس لها سجل منفصل** في قاعدة البيانات
3. ✅ **يتم إنشاء قواعد أسعار منفصلة** في Odoo لكل وحدة
4. ✅ **الربط تلقائي** بين وحدات القياس في SAP و Odoo
5. ⚠️ **يجب استيراد وحدات القياس أولاً** (المرحلة 1) قبل الأسعار

---

**📅 تاريخ التوثيق:** أكتوبر 2024  
**✍️ التوثيق:** مكتمل وشامل


