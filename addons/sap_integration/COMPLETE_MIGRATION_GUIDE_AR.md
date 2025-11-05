# 🚀 دليل Migration الكامل من SAP إلى Odoo

## 📌 نظرة عامة

تم إنشاء نظام **Migration كامل 100%** لنقل جميع بيانات المنتجات من SAP إلى Odoo بدون أي نقص.

---

## ✅ ما تم تنفيذه

### 1. **Models الجديدة (3 نماذج)**

#### ✅ `sap.product.extended` - المعلومات الموسعة
```python
# الحقول الإضافية غير الموجودة في product.product:
- foreign_name, foreign_name_2 (الأسماء الأجنبية)
- manufacturer_id, manufacturer_catalog_no (معلومات المصنع)
- supplier_catalog_no (رقم كاتالوج المورد)
- length1, width1, height1, length2, width2, height2 (الأبعاد)
- dimension_unit_id, weight_unit_id, volume_unit_id (وحدات القياس)
- manage_batch_numbers, manage_serial_numbers (إدارة الدفعات والأرقام التسلسلية)
- min_level, max_level, reorder_quantity, lead_time (مستويات المخزون)
- tax_code_ar, tax_code_ap (رموز الضرائب)
- commission_group_code, commission_percent (العمولات)
- customs_group_code, ship_type (الجمارك والشحن)
- items_group_name, user_text, remarks (معلومات إضافية)
```

#### ✅ `sap.product.pricelist.sync` - مزامنة الأسعار
```python
# يربط بين SAP ItemPrices و Odoo Pricelists:
- يستخدم نظام product.pricelist الموجود في Odoo ✅
- يدعم أسعار متعددة حسب UoM
- يدعم أسعار متعددة حسب قوائم الأسعار
- ينشئ product.pricelist.item تلقائياً
```

#### ✅ `sap.product.warehouse.info` - معلومات المخزون
```python
# يربط بين SAP ItemWarehouseInfo و Odoo Stock:
- يستخدم stock.quant للكميات الفعلية ✅
- يستخدم stock.warehouse.orderpoint لنقاط إعادة الطلب ✅
- يحفظ معلومات SAP الإضافية (default_bin, sap_codes)
```

### 2. **UoM Groups - موجود ومكتمل ✅**
```python
# في sap_uom.py - يجلب:
- UnitOfMeasurementGroups من SAP
- UnitOfMeasurementGroupDefinitionCollection (التحويلات)
- ينشئ uom.category لكل مجموعة
- ينشئ uom.uom لكل وحدة مع معاملات التحويل
# مثال: 1 كغم = 1000 غم (factor = 0.001)
```

### 3. **Wizard Migration الشامل**
```python
# sap.product.complete.migration:
- يشغل Migration على 4 مراحل
- يعرض تقرير مفصل
- يتعامل مع الأخطاء تلقائياً
- يوفر إحصائيات كاملة
```

---

## 🎯 كيفية الاستخدام

### **الطريقة 1: من واجهة Odoo (الأسهل)**

#### الخطوات:

1. **حدّث وحدة SAP Integration**:
   ```
   Settings > Apps > Apps
   ابحث عن "SAP Integration"
   اضغط "Upgrade"
   ```

2. **افتح Migration Wizard**:
   ```
   SAP Integration > 🚀 Complete Migration
   ```

3. **اختر Backend** واضغط **"🚀 Run Migration"**

4. **انتظر** حتى يكتمل (سيعرض progress)

5. **راجع النتائج** في تبويب "Statistics"

---

### **الطريقة 2: من Python Shell (متقدم)**

```python
# 1. الحصول على Backend
backend = env['sap.backend'].search([('active', '=', True)], limit=1)

# 2. إنشاء Migration Wizard
wizard = env['sap.product.complete.migration'].create({
    'backend_id': backend.id,
    'stage1_uom_groups': True,      # ✅ UoM Groups
    'stage2_products': True,         # ✅ Products
    'stage3_pricelists': True,       # ✅ Pricelists
    'stage4_warehouse_info': True,   # ✅ Warehouse Info
    'batch_size': 100,               # حجم الدفعة
    'update_existing': True,         # تحديث الموجود
    'skip_errors': True,             # تجاوز الأخطاء
})

# 3. تشغيل Migration
wizard.run_complete_migration()

# 4. عرض النتائج
print(f"State: {wizard.state}")
print(f"Products: {wizard.total_products}")
print(f"Pricelists: {wizard.total_pricelists}")
print(f"Prices: {wizard.total_prices}")
print(f"Warehouses: {wizard.total_warehouses}")
print(f"Errors: {wizard.errors_count}")
print(f"\nLog:\n{wizard.migration_log}")
```

---

### **الطريقة 3: مراحل منفصلة**

```python
backend = env['sap.backend'].search([('active', '=', True)], limit=1)

# المرحلة 1: UoM Groups
print("Stage 1: UoM Groups...")
uom_result = env['sap.uom.sync'].import_all_uoms_from_sap(backend)
print(f"✓ Imported {uom_result} UoM groups")

# المرحلة 2: Products (من wizard موجود)
print("\nStage 2: Products...")
wizard = env['sap.import.wizard'].create({
    'backend_id': backend.id,
    'import_customers': False,
    'import_products': True,
})
wizard.action_import()

# المرحلة 3: Pricelists
print("\nStage 3: Pricelists...")
pricelist_sync = env['sap.product.pricelist.sync']
price_result = pricelist_sync.import_all_pricelists_from_sap(backend, 100)
print(f"✓ Imported {price_result['total_prices']} prices")

# المرحلة 4: Warehouse Info
print("\nStage 4: Warehouse Info...")
warehouse_sync = env['sap.product.warehouse.info']
warehouse_result = warehouse_sync.import_all_warehouse_info_from_sap(backend, 100)
print(f"✓ Imported {warehouse_result['created_records']} warehouse records")
```

---

## 📊 ما سيتم استيراده

### **من SAP Items API:**
```json
{
  "ItemCode": "PROD001",
  "ItemName": "زيت زيتون",
  "ForeignName": "Olive Oil",
  "ItemsGroupCode": 100,
  "ItemsGroupName": "Oils",
  "SalesUnitPrice": 10.00,
  "PurchaseUnitPrice": 7.00,
  "InventoryUOM": "L",
  "SalesUnit": "L",
  "PurchaseUnit": "L",
  "ManufacturerCatalogNo": "OO-001",
  "Weight": 1.5,
  "Length1": 10.0,
  "Width1": 10.0,
  "Height1": 25.0,
  "ManageBatchNumbers": "Y",
  "MinLevel": 50,
  "MaxLevel": 500,
  "ItemPrices": [
    {"PriceList": 1, "Price": 10.00, "UoMCode": "L"},
    {"PriceList": 1, "Price": 6.00, "UoMCode": "500ML"},
    {"PriceList": 2, "Price": 8.00, "UoMCode": "L"}
  ],
  "ItemWarehouseInfoCollection": [
    {
      "WarehouseCode": "WH01",
      "InStock": 100,
      "Committed": 20,
      "MinimumStock": 50,
      "MaximumStock": 500,
      "DefaultBin": "A-01-05"
    }
  ]
}
```

### **إلى Odoo:**

#### 1. **product.product** (الأساسي):
```
- name = "زيت زيتون"
- default_code = "PROD001"
- list_price = 10.00
- standard_price = 7.00
- uom_id = "Liter"
- weight = 1.5
- barcode, categ_id, etc.
```

#### 2. **sap.product.extended** (موسع):
```
- foreign_name = "Olive Oil"
- items_group_name = "Oils"
- manufacturer_catalog_no = "OO-001"
- length1 = 10, width1 = 10, height1 = 25
- manage_batch_numbers = True
- min_level = 50, max_level = 500
```

#### 3. **product.pricelist** + **pricelist.item**:
```
Pricelist 1:
  - Item 1: PROD001, 1 L = 10.00$
  - Item 2: PROD001, 500 ML = 6.00$
  
Pricelist 2:
  - Item 1: PROD001, 1 L = 8.00$
```

#### 4. **stock.quant**:
```
WH01 / PROD001:
  - quantity = 100
  - reserved_quantity = 20
```

#### 5. **stock.warehouse.orderpoint**:
```
WH01 / PROD001:
  - product_min_qty = 50
  - product_max_qty = 500
```

---

## 🔍 التحقق من النتائج

### بعد Migration، يمكنك التحقق:

```python
# 1. عدد المنتجات
products = env['product.product'].search([('default_code', '!=', False)])
print(f"Products: {len(products)}")

# 2. عدد المعلومات الموسعة
extended = env['sap.product.extended'].search([])
print(f"Extended Info: {len(extended)}")

# 3. عدد الأسعار
prices = env['sap.product.pricelist.sync'].search([])
print(f"Price Sync Records: {len(prices)}")

# 4. عدد قوائم الأسعار
pricelists = env['product.pricelist'].search([('name', 'like', 'SAP')])
print(f"SAP Pricelists: {len(pricelists)}")

# 5. عدد معلومات المخازن
warehouses = env['sap.product.warehouse.info'].search([])
print(f"Warehouse Info: {len(warehouses)}")

# 6. مثال منتج كامل
product = products[0]
print(f"\nExample Product: {product.name} ({product.default_code})")

# - المعلومات الموسعة
ext = env['sap.product.extended'].search([('product_id', '=', product.id)], limit=1)
if ext:
    print(f"  Foreign Name: {ext.foreign_name}")
    print(f"  Group: {ext.items_group_name}")

# - الأسعار
product_prices = env['sap.product.pricelist.sync'].search([('product_id', '=', product.id)])
print(f"  Prices: {len(product_prices)}")
for p in product_prices:
    print(f"    - {p.odoo_pricelist_id.name}: {p.price} {p.currency_id.name}")

# - المخزون
wh_info = env['sap.product.warehouse.info'].search([('product_id', '=', product.id)])
print(f"  Warehouses: {len(wh_info)}")
for wh in wh_info:
    print(f"    - {wh.warehouse_name}: {wh.current_qty_available} available")
```

---

## 📋 القوائم الجديدة في Odoo

بعد التحديث، ستجد في القوائم:

```
SAP Integration
├── 🚀 Complete Migration ← ★ ابدأ من هنا!
├── 📊 Dashboard
├── ⚙️ Configuration
│   ├── SAP Backends
│   ├── UoM Mapping
│   └── Pricelist Mapping
├── 🔄 Synchronization
│   ├── Customers
│   ├── Products
│   ├── Quotations
│   ├── Sales Orders
│   └── Warehouses
└── 📦 Data Management
    ├── Extended Product Info ← ★ معلومات موسعة
    ├── Product Pricelist Sync ← ★ الأسعار
    ├── Product Warehouse Info ← ★ المخزون
    ├── Bindings
    └── Sync Logs
```

---

## 🎯 الاستخدام السريع

### **استخدام بسيط (من الواجهة):**

1. افتح Odoo
2. اذهب إلى: `SAP Integration > 🚀 Complete Migration`
3. اختر Backend
4. اضغط **"🚀 Run Migration"**
5. انتظر الإشعار "Migration Complete!"
6. راجع النتائج في تبويب "Statistics"

---

### **استخدام متقدم (من Python Shell):**

```bash
# افتح Odoo Shell
cd L:\Lugal-ai
python odoo-bin shell -d YOUR_DATABASE_NAME --no-http
```

```python
# في Python Shell
backend = env['sap.backend'].search([('active', '=', True)], limit=1)

# Migration كامل بأمر واحد
wizard = env['sap.product.complete.migration'].create({
    'backend_id': backend.id,
})
wizard.run_complete_migration()

# عرض Log
print(wizard.migration_log)

# عرض الإحصائيات
print(f"Products: {wizard.total_products}")
print(f"Prices: {wizard.total_prices}")
print(f"Warehouses: {wizard.total_warehouses}")
```

---

## 📊 مثال Migration كامل

### **قبل Migration:**
```
Odoo: فارغ
```

### **بعد Migration:**

```
✅ UoM Groups:
  - Weight Category
    ├── KG (Reference, factor=1.0)
    ├── G (Smaller, factor=0.001) → 1 KG = 1000 G
    └── TON (Bigger, factor=1000.0)
  
  - Volume Category
    ├── L (Reference, factor=1.0)
    └── ML (Smaller, factor=0.001) → 1 L = 1000 ML

✅ Products: 150 منتج
  Product: زيت زيتون (PROD001)
    - Name: زيت زيتون
    - Foreign Name: Olive Oil
    - Price: 10.00$
    - UoM: Liter
    - Weight: 1.5 kg
    - Group: Oils
    - Manufacturer: XYZ Company
    - Dimensions: 10×10×25 cm
    - Manage Batches: Yes

✅ Pricelists: 3 قوائم
  - SAP Price List 1 (Default)
  - SAP Price List 2 (Wholesale)
  - SAP Price List 3 (Retail)

✅ Price Records: 450 سعر
  زيت زيتون:
    - List 1: 1 L = 10.00$
    - List 1: 500 ML = 6.00$
    - List 2: 1 L = 8.00$

✅ Warehouse Info: 300 سجل
  زيت زيتون @ المستودع الرئيسي:
    - In Stock: 100 L
    - Reserved: 20 L
    - Available: 80 L
    - Min Level: 50 L
    - Max Level: 500 L
    - Default Bin: A-01-05
```

---

## 🔧 إعدادات SAP Backend

تأكد من هذه الإعدادات قبل Migration:

```
SAP Integration > Configuration > Backends > [Your Backend]

Connection:
  ✅ Service Layer URL: https://sap-server:50000/b1s/v1
  ✅ Username: ***
  ✅ Password: ***
  ✅ Company DB: COMPANY_DB
  ✅ Connection Status: Connected

Settings:
  ✅ Batch Size: 100
  ✅ Timeout: 30 seconds
  ✅ Retry Attempts: 3
```

---

## 📝 Logs و Monitoring

### **Migration Log:**
```
SAP Integration > 🚀 Complete Migration
→ افتح السجل
→ تبويب "Migration Log"
```

### **Sync Logs:**
```
SAP Integration > Data Management > Sync Logs
```

### **Odoo System Logs:**
```
L:\Lugal-ai\odoo.log
```

ابحث عن:
```
Processing UoM Group: ...
Imported X products...
Created pricelist item for...
Updated stock quant for...
```

---

## ✅ التحقق من الاكتمال

### **Checklist:**

- [ ] ✅ UoM Groups مستوردة مع معاملات التحويل
- [ ] ✅ جميع المنتجات مستوردة مع الحقول الأساسية
- [ ] ✅ المعلومات الموسعة (ForeignName, Dimensions, etc.)
- [ ] ✅ Pricelists منشأة
- [ ] ✅ الأسعار مربوطة بـ UoMs الصحيحة
- [ ] ✅ معلومات المخزون محدثة
- [ ] ✅ Reorder rules منشأة
- [ ] ✅ Stock quants محدثة بالكميات

---

## 🚀 البدء الآن!

### **خيار سريع (Recommended):**

```python
# في Odoo Shell:
backend = env['sap.backend'].search([('active', '=', True)], limit=1)
wizard = env['sap.product.complete.migration'].create({'backend_id': backend.id})
wizard.run_complete_migration()
```

### **أو:**

من الواجهة:
```
SAP Integration > 🚀 Complete Migration > Run Migration
```

---

## 📞 الدعم

إذا واجهت أي مشاكل:
1. راجع Migration Log في الـ wizard
2. راجع Sync Logs
3. راجع ملف odoo.log
4. تحقق من SAP Connection

---

**✨ Migration جاهز للتنفيذ! ✨**













