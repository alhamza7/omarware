# 🔧 خطة الإصلاح الشاملة

## 🎯 المشاكل المكتشفة

### 1. UoM Groups (160+ مجموعة لم تُجلب)
**السبب:**
- الكود يجلب فقط UnitOfMeasurements (20 وحدة)
- لا يجلب UnitOfMeasurementGroups بشكل صحيح
- SAP يرفض `$expand=UnitOfMeasurementGroupDefinitionCollection`

**الحل:**
- جلب Groups بدون expand
- ثم جلب definitions لكل group منفصلة
- أو استخدام endpoint مباشر

### 2. Warehouse Info (لم يُجلب أي شيء)
**السبب:**
```
Error: Cannot expand invalid navigation property 'ItemWarehouseInfoCollection'
```

**الحل:**
- جلب البيانات بدون expand
- استخدام endpoint منفصل `ItemWarehouseInfo`
- أو جلب لكل منتج على حدة

### 3. Prices (لم يُجلب)
**نفس المشكلة:** expand لا يعمل

**الحل:**
- جلب ItemPrices منفصلة
- أو استخدام endpoint `ItemPrices?$filter=ItemCode eq 'xxx'`

### 4. حقول ناقصة في المنتج
- ❌ الاسم الأجنبي (ForeignName)
- ❌ وحدة البيع (SalesUnit/UoMCode)
- ❌ وحدة الشراء (PurchaseUnit/UoMCode)
- ❌ وحدة التخزين (InventoryUoM)
- ❌ السعر الرئيسي

---

## ✅ خطة الإصلاح

### المرحلة 1: إصلاح UoM Groups
```python
1. جلب جميع UnitOfMeasurementGroups
2. لكل group، جلب definitions منفصلة
3. إنشاء uom.category في Odoo
4. إنشاء uom.uom لكل تعريف مع conversion factor
```

### المرحلة 2: تحسين استيراد المنتج
```python
1. إضافة ForeignName إلى المنتج
2. إضافة SalesUnit, PurchaseUnit, InventoryUoM
3. ربطها بـ uom.uom الصحيح
4. إضافة السعر الافتراضي
```

### المرحلة 3: إصلاح Warehouse Info
```python
1. جلب Warehouses من SAP
2. لكل منتج، جلب ItemWarehouseInfo منفصل
3. تحديث stock.quant مباشرة
4. إنشاء reorder rules إذا لزم
```

### المرحلة 4: إصلاح Prices
```python
1. جلب PriceLists من SAP
2. لكل منتج، جلب ItemPrices منفصل
3. إنشاء product.pricelist.item
4. ربط الأسعار بـ UoM الصحيح
```

---

## 🚀 التنفيذ

سأقوم بـ:
1. ✅ تعديل sap_uom.py لجلب Groups بشكل صحيح
2. ✅ تعديل sap_product_complete_migration.py لإضافة الحقول
3. ✅ إصلاح sap_product_warehouse_info.py
4. ✅ إصلاح sap_product_pricelist_sync.py
5. ✅ اختبار Migration الجديد




