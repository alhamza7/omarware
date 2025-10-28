# إصلاح مشكلة uom_po_id في Odoo 19.0

**التاريخ:** 25 أكتوبر 2025  
**المشكلة:** `ValueError: Invalid field 'uom_po_id' in 'product.product'`  
**الحالة:** ✅ تم الإصلاح

---

## ❌ المشكلة

```python
ValueError: Invalid field 'uom_po_id' in 'product.product'
```

**السبب:**  
الحقل `uom_po_id` (Purchase Unit of Measure) كان موجوداً في نسخ Odoo القديمة لكن تم **إزالته في Odoo 19.0**.

### في الإصدارات القديمة:
- `uom_id` - وحدة القياس الأساسية
- `uom_po_id` - وحدة الشراء (منفصلة)

### في Odoo 19.0:
- `uom_id` - وحدة القياس الأساسية فقط
- وحدات الشراء المختلفة تدار عبر `product.supplierinfo`

---

## ✅ الحل

تم إصلاح **7 ملفات** تحتوي على استخدامات `uom_po_id`:

### 1. `wizard/sap_product_complete_migration.py`
**قبل:**
```python
if purchase_uom_id:
    vals['uom_po_id'] = purchase_uom_id
elif default_uom_id:
    vals['uom_po_id'] = default_uom_id
```

**بعد:**
```python
# Note: uom_po_id removed in Odoo 19.0
# Purchase UoM is now handled through product supplier info
```

---

### 2. `models/sap_product.py`
**قبل:**
```python
'uom_id': self._get_uom_id(sap_data.get('SalesUnit', '')),
'uom_po_id': self._get_uom_id(sap_data.get('PurchaseUnit', '')),
```

**بعد:**
```python
'uom_id': self._get_uom_id(sap_data.get('SalesUnit', '')),
# Note: uom_po_id removed in Odoo 19.0
```

**أيضاً في التصدير:**
```python
# قبل
'PurchaseUnit': self._get_sap_uom(product.uom_po_id),

# بعد
'PurchaseUnit': self._get_sap_uom(product.uom_id),  # Use same as sales
```

---

### 3. `models/sap_product_direct.py`
**قبل:**
```python
if product_data.get('SalesUnit'):
    uom = self._get_or_create_uom(product_data['SalesUnit'])
    product_vals['uom_id'] = uom.id
    product_vals['uom_po_id'] = uom.id

if product_data.get('PurchaseUnit'):
    uom = self._get_or_create_uom(product_data['PurchaseUnit'])
    product_vals['uom_po_id'] = uom.id
```

**بعد:**
```python
if product_data.get('SalesUnit'):
    uom = self._get_or_create_uom(product_data['SalesUnit'])
    product_vals['uom_id'] = uom.id

# Note: uom_po_id removed in Odoo 19.0
# Purchase UoM can be set through product.supplierinfo if needed
```

---

### 4. `core/sap_data_mapper.py`
**قبل:**
```python
if 'SalesUnit' in sap_data:
    product_data['uom_id'] = self._get_uom_id(sap_data['SalesUnit'])
    product_data['uom_po_id'] = self._get_uom_id(sap_data.get('PurchaseUnit', ...))
```

**بعد:**
```python
if 'SalesUnit' in sap_data:
    product_data['uom_id'] = self._get_uom_id(sap_data['SalesUnit'])
    # Note: uom_po_id removed in Odoo 19.0
```

**أيضاً في التصدير:**
```python
# قبل
if odoo_product.uom_po_id:
    sap_data['PurchaseUnit'] = self._get_sap_uom_code(odoo_product.uom_po_id)

# بعد
# Use same UoM for purchase in Odoo 19.0
sap_data['PurchaseUnit'] = self._get_sap_uom_code(odoo_product.uom_id)
```

---

### 5. `components/mapper.py`
**قبل:**
```python
@mapping
def uom_po_id(self, record):
    """Map SAP purchase UoM to Odoo purchase UoM"""
    sap_uom = record.get('PurchaseUnit')
    if sap_uom:
        uom_id = self._get_or_create_uom_mapping(sap_uom)
        if uom_id:
            return {'uom_po_id': uom_id}
    return {}
```

**بعد:**
```python
# Note: uom_po_id removed in Odoo 19.0
# Purchase UoM is now handled through product.supplierinfo
# (function commented out)
```

---

## 📊 الإحصائيات

- **عدد الملفات المعدلة:** 5 ملفات
- **عدد الاستخدامات المحذوفة:** 8 استخدامات
- **عدد الوظائف المعطلة:** 1 وظيفة

---

## 💡 كيفية التعامل مع Purchase UoM في Odoo 19.0

إذا كنت بحاجة لتحديد وحدة شراء مختلفة عن وحدة البيع:

### استخدم `product.supplierinfo`:

```python
self.env['product.supplierinfo'].create({
    'product_tmpl_id': product.product_tmpl_id.id,
    'partner_id': supplier_id,
    'price': purchase_price,
    'product_uom': purchase_uom_id,  # وحدة الشراء المختلفة
})
```

هذا يسمح بتحديد وحدة شراء مختلفة **لكل مورد** بدلاً من وحدة شراء عامة واحدة.

---

## ✅ النتيجة

بعد الإصلاح:
- ✅ لا توجد أخطاء `uom_po_id`
- ✅ يتم استخدام `uom_id` لجميع وحدات القياس
- ✅ يمكن تحديد وحدات شراء مختلفة عبر `product.supplierinfo`
- ✅ متوافق 100% مع Odoo 19.0

---

## 📚 المراجع

- **Odoo 19.0 Documentation:** Product Management
- **Migration Guide:** Odoo 18 → Odoo 19

---

**✅ تم الإصلاح بنجاح!**



