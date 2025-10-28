# أين تجد معلومات المخازن؟
## Where to Find Warehouse Data

**التاريخ:** 2025-10-26  
**عدد سجلات المخازن:** 211,711

---

## 📍 طرق الوصول لمعلومات المخازن

### 1️⃣ من قائمة SAP Integration ⭐ (الأسهل)

**المسار:**
```
SAP Integration > Warehouse > Product Warehouse Info
```

**ما ستجده:**
- جميع المنتجات مع بيانات المخازن
- الكميات من SAP
- أسماء المخازن
- الكميات المتاحة والمحجوزة

**الحقول المتوفرة:**
- Product Code
- Product Name  
- Warehouse Name
- Last In Stock (الكمية الموجودة)
- Last Available (الكمية المتاحة)
- Last Committed (الكمية المحجوزة)
- Minimum/Maximum Stock
- Sync Status

**الفلاتر المفيدة:**
- فلتر بـ Warehouse
- فلتر بـ Product
- فلتر بـ Sync Status

---

### 2️⃣ من صفحة المنتج

**المسار:**
```
Inventory > Products > Products
↓
(افتح أي منتج)
↓
Inventory Tab
```

**ما ستجده:**
- On Hand Quantity (الكمية الموجودة)
- Forecasted Quantity (الكمية المتوقعة)
- Routes (المسارات)
- Reordering Rules

**للمنتجات من SAP:**
- يمكنك رؤية الكميات في جميع المخازن
- تم تحديثها من SAP

---

### 3️⃣ من قائمة Inventory

**المسار الأول - الكميات:**
```
Inventory > Reporting > Inventory Valuation
```

**المسار الثاني - الموقع:**
```
Inventory > Products > Products
↓
Filters > Group By > Location
```

**ما ستجده:**
- الكميات لكل منتج
- القيمة المخزنية
- الحركات

---

### 4️⃣ من قائمة Stock/Inventory

**لرؤية الكميات المفصلة:**
```
Inventory > Operations > On Hand
```

**أو:**
```
Inventory > Reporting > Stock
```

**ما ستجده:**
- Quantity On Hand
- Reserved
- Available
- Location breakdown

---

## 🔍 البحث والفلترة

### للبحث عن منتج معين:

**الطريقة 1: من SAP Integration**
```
SAP Integration > Warehouse > Product Warehouse Info
↓
Search: اكتب كود المنتج (مثل: ADF00001)
```

**الطريقة 2: من Product**
```
Inventory > Products > Products
↓
Search: اكتب اسم أو كود المنتج
↓
افتح المنتج > Inventory Tab
```

---

## 📊 معلومات إضافية متوفرة:

### في `sap.product.warehouse.info`:

**معلومات SAP الأصلية:**
- `last_in_stock` - الكمية في المخزن
- `last_committed` - الكمية المحجوزة
- `last_ordered` - الكمية المطلوبة
- `last_available` - المتاح = InStock - Committed

**معلومات Reorder:**
- `minimum_stock` - الحد الأدنى
- `maximum_stock` - الحد الأقصى
- `min_order` - الكمية الدنيا للطلب

**معلومات المخزن:**
- `sap_warehouse_code` - كود المخزن في SAP
- `sap_warehouse_name` - اسم المخزن
- `default_bin` - الموقع الافتراضي

**معلومات المزامنة:**
- `last_sync_date` - تاريخ آخر مزامنة
- `sync_status` - حالة المزامنة
- `sync_error_message` - رسائل الأخطاء

---

## 🎯 أمثلة عملية:

### مثال 1: البحث عن كمية منتج معين

**الخطوات:**
1. اذهب إلى: `SAP Integration > Warehouse > Product Warehouse Info`
2. ابحث عن: `ADF00001`
3. سترى جميع المخازن التي يوجد فيها هذا المنتج
4. الكميات لكل مخزن

### مثال 2: رؤية جميع منتجات مخزن معين

**الخطوات:**
1. اذهب إلى: `SAP Integration > Warehouse > Product Warehouse Info`
2. Filter > Add Custom Filter
3. `Warehouse Name` = "محل الشورجة" (مثلاً)
4. سترى جميع المنتجات في هذا المخزن

### مثال 3: المنتجات التي تحتاج إعادة طلب

**الخطوات:**
1. اذهب إلى: `SAP Integration > Warehouse > Product Warehouse Info`
2. Filter > Add Custom Filter
3. `Last Available` < `Minimum Stock`
4. سترى المنتجات التي تحت الحد الأدنى

---

## 💻 عرض البيانات في الواجهة

### القوائم المتاحة:

#### في SAP Integration:
```
SAP Integration
├── Products
│   ├── Product Sync
│   └── Extended Product Info
├── Pricelists
│   └── Product Pricelist Sync ← الأسعار
└── Warehouse
    └── Product Warehouse Info ← المخازن ⭐
```

#### في Inventory:
```
Inventory
├── Products
│   ├── Products ← رؤية الكميات
│   └── Product Variants
├── Operations
│   ├── On Hand ← الكميات الحالية
│   └── Transfers
└── Reporting
    ├── Stock ← تقرير الكميات
    └── Inventory Valuation
```

---

## 🔧 نصائح للاستخدام:

### 1. للتحقق السريع:
استخدم: `SAP Integration > Warehouse > Product Warehouse Info`

### 2. لرؤية الكميات الحية:
استخدم: `Inventory > Operations > On Hand`

### 3. للتقارير:
استخدم: `Inventory > Reporting > Stock`

### 4. للبحث المتقدم:
استخدم Filters و Group By في أي قائمة

---

## 📱 الوصول السريع:

### رابط مباشر (بعد تسجيل الدخول):
```
http://localhost:8069/web#action=xxx&model=sap.product.warehouse.info
```

### أو من القائمة:
```
☰ Menu > SAP Integration > Warehouse > Product Warehouse Info
```

---

## 🎊 الخلاصة:

**معلومات المخازن موجودة في:**

1. **SAP Integration > Warehouse > Product Warehouse Info** ← ⭐ الأفضل
2. **Inventory > Products > (افتح منتج) > Inventory Tab**
3. **Inventory > Operations > On Hand**
4. **Inventory > Reporting > Stock**

**عدد السجلات:** 211,711 سجل مخزن  
**الحالة:** ✅ مستوردة ومتوفرة  
**جاهزة للاستخدام:** نعم 100%

---

تم التوثيق: 2025-10-26 10:35




