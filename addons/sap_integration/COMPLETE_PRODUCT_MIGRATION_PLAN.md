# 📋 خطة Migration الكاملة للمنتجات من SAP إلى Odoo

## 🎯 الهدف
عمل Migration كامل 100% لجميع معلومات المنتجات من SAP إلى Odoo بدون أي نقص، بما في ذلك:
- ✅ جميع الحقول الأساسية والمتقدمة
- ✅ الأسعار المتعددة حسب وحدات القياس
- ✅ مجموعات وحدات القياس مع معاملات التحويل (مثل: 1كغم = 1000غم)
- ✅ معلومات المخزون لكل مستودع
- ✅ الأسماء الأجنبية والترجمات
- ✅ جميع العلاقات والربط بين الجداول

---

## 📊 تحليل الحقول الحالية vs المطلوبة

### ✅ الحقول الموجودة حاليًا:
```python
# في sap.product.product
- ItemCode → default_code
- ItemName → name  
- ItemDescription → description
- SalesUnitPrice → list_price
- PurchaseUnitPrice → standard_price
- SalesUnit, PurchaseUnit, InventoryUOM → uom_id, uom_po_id
- Weight, Volume
- ItemsGroupCode → categ_id
- BarCode → barcode
- Valid → active
```

### ❌ الحقول الناقصة المطلوبة:

#### 1. **معلومات أساسية إضافية**
- ❌ `ForeignName` - الاسم الأجنبي/الترجمة
- ❌ `ItemsGroupName` - اسم المجموعة
- ❌ `ManufacturerCatalogNumber` - رقم كاتالوج المصنع
- ❌ `Manufacturer` - المصنع
- ❌ `SupplierCatalogNo` - رقم كاتالوج المورد
- ❌ `DefaultSalesUoM` - وحدة البيع الافتراضية
- ❌ `DefaultPurchaseUoM` - وحدة الشراء الافتراضية

#### 2. **الأبعاد والأوزان**
- ❌ `Length1` - الطول
- ❌ `Width1` - العرض  
- ❌ `Height1` - الارتفاع
- ❌ `Length2` - الطول البديل
- ❌ `Width2` - العرض البديل
- ❌ `Height2` - الارتفاع البديل
- ❌ `WeightUnit` - وحدة الوزن
- ❌ `DimensionUnit` - وحدة الأبعاد

#### 3. **إدارة المخزون**
- ❌ `ManageBatchNumbers` - إدارة الدفعات
- ❌ `ManageSerialNumbers` - إدارة الأرقام التسلسلية
- ❌ `ManageStockByWarehouse` - إدارة المخزون حسب المستودع
- ❌ `MinLevel` - الحد الأدنى للمخزون
- ❌ `MaxLevel` - الحد الأقصى للمخزون
- ❌ `LeadTime` - وقت التسليم
- ❌ `ReorderQuantity` - كمية إعادة الطلب

#### 4. **المعلومات المالية والضريبية**
- ❌ `TaxCodeAR` - رمز الضريبة للمبيعات
- ❌ `TaxCodeAP` - رمز الضريبة للمشتريات
- ❌ `CommissionGroup` - مجموعة العمولة
- ❌ `CommissionPercent` - نسبة العمولة
- ❌ `CustomsGroupCode` - مجموعة الجمارك

#### 5. **معلومات الشراء والبيع**
- ❌ `PurchaseItem` - قابل للشراء
- ❌ `SalesItem` - قابل للبيع
- ❌ `InventoryItem` - عنصر مخزني
- ❌ `DefaultWarehouseCode` - المستودع الافتراضي
- ❌ `ShipType` - نوع الشحن

---

## 🔗 الجداول المرتبطة المطلوبة

### 1. **ItemPrices** - الأسعار المتعددة
```python
# الحقول المطلوبة:
- ItemCode
- PriceList  # قائمة الأسعار
- Price  # السعر
- Currency  # العملة
- UoMEntry  # وحدة القياس
- BasePriceList  # قائمة الأسعار الأساسية
- Factor  # معامل التحويل
```

### 2. **ItemWarehouseInfo** - معلومات المخزون
```python
# الحقول المطلوبة:
- ItemCode
- WarehouseCode  # رمز المستودع
- InStock  # الكمية المتوفرة
- Committed  # الكمية المحجوزة
- Ordered  # الكمية المطلوبة
- Available  # الكمية المتاحة (InStock - Committed)
- MinimumStock  # الحد الأدنى
- MaximumStock  # الحد الأقصى
- MinOrder  # الحد الأدنى للطلب
- DefaultBin  # الموقع الافتراضي
```

### 3. **ItemUnitOfMeasurementPackages** - وحدات القياس للمنتج
```python
# الحقول المطلوبة:
- ItemCode
- UoMEntry  # رقم وحدة القياس
- UoMCode  # رمز وحدة القياس
- UoMName  # اسم وحدة القياس
- QuantityPerUnit  # الكمية لكل وحدة
- LengthPackage  # طول الحزمة
- WidthPackage  # عرض الحزمة
- HeightPackage  # ارتفاع الحزمة
- WeightPackage  # وزن الحزمة
```

### 4. **UnitOfMeasurementGroups** - مجموعات وحدات القياس
```python
# الحقول المطلوبة:
- Code  # رمز المجموعة
- Name  # اسم المجموعة
- BaseUoM  # وحدة القياس الأساسية
- UnitOfMeasurementGroupDefinitionCollection:
  - UoMCode  # رمز الوحدة
  - UoMName  # اسم الوحدة
  - AlternateQuantity  # الكمية البديلة
  - BaseQuantity  # الكمية الأساسية
  # مثال: 1 كغم = 1000 غم
  # BaseQuantity=1, AlternateQuantity=1000
```

---

## 🏗️ بنية Models الجديدة

### 1. **sap.product.extended** - نموذج موسع للمنتج
```python
class SapProductExtended(models.Model):
    _name = 'sap.product.extended'
    _description = 'SAP Product Extended Information'
    
    # ربط بالمنتج
    product_id = fields.Many2one('product.product', required=True)
    backend_id = fields.Many2one('sap.backend', required=True)
    
    # معلومات إضافية
    foreign_name = fields.Char('Foreign Name')
    manufacturer_catalog_no = fields.Char('Manufacturer Catalog #')
    manufacturer_id = fields.Many2one('res.partner', 'Manufacturer')
    supplier_catalog_no = fields.Char('Supplier Catalog #')
    
    # الأبعاد
    length1 = fields.Float('Length 1')
    width1 = fields.Float('Width 1')
    height1 = fields.Float('Height 1')
    dimension_unit_id = fields.Many2one('uom.uom', 'Dimension Unit')
    
    # إدارة المخزون
    manage_batch_numbers = fields.Boolean('Manage Batch Numbers')
    manage_serial_numbers = fields.Boolean('Manage Serial Numbers')
    manage_stock_by_warehouse = fields.Boolean('Stock by Warehouse')
    
    # معلومات مالية
    commission_group_code = fields.Integer('Commission Group')
    commission_percent = fields.Float('Commission %')
    customs_group_code = fields.Char('Customs Group')
```

### 2. **sap.product.price** - الأسعار المتعددة
```python
class SapProductPrice(models.Model):
    _name = 'sap.product.price'
    _description = 'SAP Product Prices by UoM'
    
    product_id = fields.Many2one('product.product', required=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Price List')
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    price = fields.Float('Price', required=True)
    currency_id = fields.Many2one('res.currency', 'Currency')
    factor = fields.Float('Factor', default=1.0)
```

### 3. **sap.product.warehouse.info** - معلومات المخزون
```python
class SapProductWarehouseInfo(models.Model):
    _name = 'sap.product.warehouse.info'
    _description = 'SAP Product Warehouse Information'
    
    product_id = fields.Many2one('product.product', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', required=True)
    backend_id = fields.Many2one('sap.backend', required=True)
    
    # الكميات
    in_stock = fields.Float('In Stock')
    committed = fields.Float('Committed')
    ordered = fields.Float('Ordered')
    available = fields.Float('Available', compute='_compute_available')
    
    # الحدود
    minimum_stock = fields.Float('Minimum Stock')
    maximum_stock = fields.Float('Maximum Stock')
    min_order = fields.Float('Minimum Order')
    
    # الموقع
    default_bin = fields.Char('Default Bin')
```

---

## 🚀 سكريبت Migration الشامل

### مراحل التنفيذ:

#### **المرحلة 1: جلب وإنشاء UoM Groups**
```python
1. جلب جميع UnitOfMeasurementGroups من SAP
2. لكل مجموعة:
   - إنشاء uom.category في Odoo
   - جلب UnitOfMeasurementGroupDefinitionCollection
   - إنشاء uom.uom لكل وحدة مع معامل التحويل الصحيح
   - ربط الوحدات بالمجموعة
3. إنشاء sap.uom.sync لكل وحدة
```

#### **المرحلة 2: جلب المنتجات الأساسية**
```python
1. جلب جميع Items من SAP مع $expand
2. لكل منتج:
   - إنشاء/تحديث product.product
   - تعيين جميع الحقول الأساسية
   - ربط UoMs الصحيحة
```

#### **المرحلة 3: جلب المعلومات الموسعة**
```python
1. لكل منتج:
   - إنشاء sap.product.extended
   - ملء جميع الحقول المتقدمة
   - حفظ ForeignName والترجمات
```

#### **المرحلة 4: جلب الأسعار المتعددة**
```python
1. جلب ItemPrices من SAP
2. لكل سعر:
   - إنشاء product.pricelist إذا لم تكن موجودة
   - إنشاء sap.product.price
   - ربط السعر بـ UoM الصحيحة
```

#### **المرحلة 5: جلب معلومات المخزون**
```python
1. جلب ItemWarehouseInfo من SAP
2. لكل مخزن:
   - إنشاء/تحديث stock.warehouse
   - إنشاء sap.product.warehouse.info
   - تحديث الكميات المتاحة
```

#### **المرحلة 6: التحقق والتأكيد**
```python
1. عد جميع المنتجات المستوردة
2. التحقق من اكتمال جميع العلاقات
3. إنشاء تقرير Migration شامل
```

---

## 📝 التنفيذ الفعلي

سيتم إنشاء:
1. ✅ 3 Models جديدة
2. ✅ Views وقوائم لكل Model
3. ✅ سكريبت Migration تلقائي بالكامل
4. ✅ تقرير Migration مفصل

---

## ⚡ الاستخدام النهائي

```python
# في Python Shell - Migration كامل بأمر واحد
backend = env['sap.backend'].search([('active', '=', True)], limit=1)

# تشغيل Migration الشامل
migration = env['sap.product.complete.migration']
result = migration.run_complete_migration(backend)

# سيقوم بـ:
# ✅ جلب جميع UoM Groups مع التحويلات
# ✅ جلب جميع المنتجات مع كل الحقول
# ✅ جلب جميع الأسعار حسب UoMs
# ✅ جلب جميع معلومات المخزون
# ✅ إنشاء تقرير Migration كامل
```

---

**الآن سأبدأ التنفيذ...**

