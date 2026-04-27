# 📍 دليل سريع: أين تجد البيانات المُزامنة؟

**آخر تحديث**: 4 ديسمبر 2025

---

## 🎯 الوصول السريع

### 1️⃣ المنتجات (الأساسي)
```
📍 المسار: Inventory → Products → Products
```
**ستجد**:
- ✅ جميع المنتجات المُزامنة
- ✅ الباركود الرئيسي
- ✅ اسم المنتج وكوده (ItemCode)
- ✅ السعر

**داخل المنتج**:
- 📋 Tab "Alternative Barcodes" ← الباركودات الفرعية
- 🔘 زر "Alternative Barcodes" في الأعلى ← عدد الباركودات

---

### 2️⃣ الباركودات البديلة (عرض شامل)
```
📍 المسار: Inventory → Configuration → Alternative Barcodes
```
**ستجد**:
- ✅ جميع الباركودات البديلة لكل المنتجات
- ✅ وحدة القياس (UoM) لكل باركود
- ✅ SAP UoMEntry
- ✅ آخر تزامن (Last Sync)
- ✅ حالة التفعيل (Active)

**عرض القائمة**:
```
Product     | Barcode | UoM Name  | UoM Entry | Active | Last Sync
------------|---------|-----------|-----------|--------|----------
زيت زيتون   | 20493   | كرتون     | 12        | ✓      | 2025-12-04
زيت زيتون   | 20494   | صندوق     | 6         | ✓      | 2025-12-04
أرز بسمتي   | 30123   | شوال      | 50        | ✓      | 2025-12-04
```

---

### 3️⃣ قوائم الأسعار
```
📍 المسار: Sales → Configuration → Pricelists
```
**ستجد**:
- ✅ SAP Price List 1
- ✅ SAP Price List 2
- ✅ SAP Price List 3
- ... إلخ

**داخل كل قائمة**:
- Tab "Price Rules" ← أسعار كل المنتجات
- أسعار مختلفة حسب UoM

---

### 4️⃣ المخازن
```
📍 المسار: Inventory → Configuration → Warehouses
```
**ستجد**:
- ✅ جميع المخازن المُزامنة
- ✅ كود المخزن (من SAP)
- ✅ اسم المخزن

---

### 5️⃣ الكميات في المخزون
```
📍 المسار 1: Inventory → Reporting → Inventory Report
📍 المسار 2: Inventory → Products → Products → [منتج] → زر "On Hand"
```
**ستجد**:
- ✅ الكميات المتوفرة
- ✅ الكميات المحجوزة
- ✅ المواقع (Locations)

---

### 6️⃣ وحدات القياس
```
📍 المسار: Inventory → Configuration → Units of Measure
```
**ستجد**:
- ✅ جميع UoM المُزامنة
- ✅ عوامل التحويل
- ✅ الفئات (Categories)

---

## 🔍 كيف تتحقق من منتج معين؟

### الطريقة 1: من الباركود
```
1. Inventory → Products → Products
2. في خانة البحث، اكتب الباركود: 20493
3. افتح المنتج
4. انظر إلى Tab "Alternative Barcodes"
```

### الطريقة 2: من الباركودات البديلة مباشرة
```
1. Inventory → Configuration → Alternative Barcodes
2. في خانة البحث، اكتب الباركود: 20493
3. ستجد السجل مباشرة مع معلوماته
```

---

## 📊 تفاصيل الباركودات البديلة

### داخل المنتج:

```
┌─────────────────────────────────────┐
│ منتج: زيت زيتون نخيل 5 لتر         │
├─────────────────────────────────────┤
│ 📋 General Information              │
│   - Name: زيت زيتون نخيل 5 لتر       │
│   - Internal Reference: ITEM001      │
│   - Barcode: 123456 (قنينة واحدة)  │
│   - Sales Price: 50.00               │
├─────────────────────────────────────┤
│ 📊 Alternative Barcodes (Tab)       │
│   ┌────────────────────────────────┐│
│   │ Seq | Barcode | UoM Name       ││
│   ├─────┼─────────┼────────────────┤│
│   │  1  │ 20493   │ كرتون (12)    ││
│   │  2  │ 20494   │ صندوق (72)    ││
│   │  3  │ 20495   │ باليت (720)   ││
│   └────────────────────────────────┘│
├─────────────────────────────────────┤
│ 🔘 زر في الأعلى:                   │
│    [📊 Alternative Barcodes: 3]     │
└─────────────────────────────────────┘
```

---

## ⚡ البحث السريع

### بحث عن باركود معين:
```
Method 1: Global Search
  → في أي صفحة، اضغط على Search (أعلى اليمين)
  → اكتب الباركود
  → اختر "Products" أو "Alternative Barcodes"

Method 2: Filters
  → Inventory → Products → Products
  → Filters → Add Custom Filter
  → barcode contains "20493"
  → Apply
```

---

## 🎯 سيناريوهات عملية

### سيناريو 1: "عندي باركود، أريد معرفة المنتج"
```
1. Inventory → Configuration → Alternative Barcodes
2. Search: 20493
3. ستجد: Product = "زيت زيتون"، UoM = "كرتون"
```

### سيناريو 2: "عندي منتج، أريد كل الباركودات"
```
1. Inventory → Products → Products
2. افتح المنتج
3. Tab "Alternative Barcodes"
4. ستجد جميع الباركودات الرئيسية والفرعية
```

### سيناريو 3: "أريد طباعة ليبل لباركود فرعي"
```
1. Inventory → Product Labels → SAP Label Printer
2. امسح الباركود (مثلاً: 20493)
3. النظام يجد المنتج تلقائياً من الباركودات البديلة
4. يطبع الليبل مع UoM الصحيح!
```

---

## 🔄 بعد المزامنة

### تحقق من نجاح المزامنة:

```
✅ خطوة 1: عدد المنتجات
   Inventory → Products → Products
   → تحقق من العدد

✅ خطوة 2: الباركودات البديلة
   Inventory → Configuration → Alternative Barcodes
   → يجب أن ترى باركودات كثيرة

✅ خطوة 3: فتح منتج عشوائي
   → Tab "Alternative Barcodes"
   → يجب أن يحتوي على باركودات

✅ خطوة 4: تجربة الطباعة
   Product Labels → SAP Label Printer
   → جرب باركود فرعي
   → يجب أن يعمل فوراً!
```

---

## 📞 استكشاف الأخطاء

### ❌ "لا أجد Alternative Barcodes في Menu"
**الحل**:
```
1. تأكد من تحديث الموديول:
   Apps → product_label_designer → Upgrade
   
2. تحقق من الصلاحيات:
   Settings → Users → [المستخدم]
   → يجب أن يكون: Stock User أو Stock Manager
   
3. Refresh الصفحة (F5)
```

### ❌ "Tab Alternative Barcodes فارغ"
**الحل**:
```
1. قم بالمزامنة:
   Inventory → Configuration → SAP Product Migration
   → Stage 2: Import Products
   → Run Complete Migration
   
2. تحقق من أن SAP يحتوي على باركودات فرعية
```

### ❌ "زر Alternative Barcodes لا يظهر في المنتج"
**السبب**: لا يوجد باركودات بديلة لهذا المنتج
**الحل**: الزر يظهر فقط عندما `alternative_barcode_count > 0`

---

## 🎓 نصائح

### 💡 نصيحة 1: ضع Alternative Barcodes في Favorites
```
1. Inventory → Configuration → Alternative Barcodes
2. Add to my Favorites ⭐
3. الآن يمكنك الوصول إليها بسرعة!
```

### 💡 نصيحة 2: استخدم Filters
```
في Alternative Barcodes:
  → Filter by Product
  → Filter by UoM Name
  → Filter by Active/Inactive
```

### 💡 نصيحة 3: Export إلى Excel
```
في أي قائمة:
  → Select All
  → Actions → Export
  → اختر الحقول
  → Download
```

---

## ✅ الخلاصة

```
📍 المنتجات:              Inventory → Products → Products
📍 الباركودات البديلة:    Inventory → Configuration → Alternative Barcodes
📍 قوائم الأسعار:         Sales → Configuration → Pricelists
📍 المخازن:               Inventory → Configuration → Warehouses
📍 طباعة الليبلات:        Inventory → Product Labels → SAP Label Printer

🎯 كل شيء موجود ومُزامن ومُنظم!
```

---

**للدعم**: راجع ملف `OFFLINE_MODE_UPDATE_AR.md` للمزيد من التفاصيل

