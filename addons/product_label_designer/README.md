# Product Label Designer - مصمم ملصقات المنتجات 🏷️

## Overview | نظرة عامة

**Professional** product label designer for Odoo 19 with **Visual Designer**, **A4 Sheet Printing**, **Foreign Names**, and full Arabic support.

موديول احترافي لتصميم وطباعة ملصقات المنتجات في Odoo 19 مع **مصمم مرئي**، **طباعة A4**، **الأسماء الأجنبية**، ودعم عربي كامل.

---

## 🌟 Key Features | المميزات الرئيسية

### 1. 🎨 Visual Designer (Drag & Drop)
- Interactive visual editor | محرر مرئي تفاعلي
- Drag & drop elements | سحب وإفلات العناصر
- Real-time preview | معاينة فورية
- Keyboard shortcuts | اختصارات لوحة المفاتيح
- Pixel-perfect positioning | مواضع دقيقة

### 2. 🌐 Foreign Name Support
- Add product names in multiple languages | أسماء بلغات متعددة
- Separate positioning | مواضع منفصلة
- RTL/LTR support | دعم اليمين لليسار

### 3. 📄 A4 Sheet Printing
- Print multiple labels on A4 | طباعة عدة ملصقات على A4
- Customizable grid (2×4, 3×3, etc) | شبكة قابلة للتخصيص
- Auto-arrange labels | ترتيب تلقائي
- Fill empty cells | ملء الخلايا الفارغة

### 4. 📊 Complete Product Data
- Product name (Arabic) | اسم المنتج (عربي)
- Foreign name (English/Other) | اسم أجنبي
- Product code | كود المنتج
- Price | السعر
- Barcode (Code128) | باركود
- Logo | الشعار

### 5. 🎯 Advanced Customization
- Background images | صور خلفية
- Logo support | دعم الشعار
- Color customization | تخصيص الألوان
- Font sizes | أحجام الخطوط
- Element positions | مواضع العناصر
- High quality PDF (300 DPI) | PDF عالي الجودة

---

## 📦 Installation | التثبيت

### 1. Install the Module | تثبيت الموديول

```bash
# Restart Odoo | أعد تشغيل Odoo
sudo systemctl restart odoo

# Or from source | أو من المصدر
./odoo-bin -c odoo.conf -u product_label_designer -d your_database
```

### 2. Activate | التفعيل

1. Apps → Update Apps List | التطبيقات → تحديث القائمة
2. Search "Product Label Designer" | ابحث عن المصمم
3. Click **Install** | اضغط تثبيت

---

## 🚀 Quick Start | البدء السريع

### Method 1: Quick Print | طباعة سريعة

```
1. Open product | افتح منتج
2. Click "Print Label" button | زر طباعة ملصق
3. Select template | اختر القالب
4. Choose print mode (Single/A4) | اختر وضع الطباعة
5. Print! | اطبع!
```

### Method 2: Visual Designer | المصمم المرئي

```
1. Inventory → Product Labels → Label Templates
2. Create/Edit template | إنشاء/تعديل قالب
3. Go to "Visual Designer" tab | تبويب المصمم المرئي
4. Click "Open Visual Designer" | افتح المصمم
5. Drag & drop elements | اسحب وأفلت العناصر
6. Save positions | احفظ المواضع
```

### Method 3: A4 Sheet Printing | طباعة A4

```
1. Select products (multiple) | اختر منتجات
2. Action → Print Labels | إجراء → طباعة ملصقات
3. Choose print mode: "A4 Sheet" | اختر A4
4. Set copies per product | عدد النسخ
5. Print! | اطبع!
```

---

## 🎨 Visual Designer Guide | دليل المصمم المرئي

### Features | المميزات:

- **Drag & Drop**: Move elements by dragging
- **Keyboard**: Use arrow keys (1mm), Shift+Arrow (10mm)
- **Click to Select**: Click any element to select
- **Real-time Position**: See X,Y coordinates in sidebar
- **Auto-save**: Positions saved automatically

### Keyboard Shortcuts | الاختصارات:

| Key | Action |
|-----|--------|
| ← → ↑ ↓ | Move 1mm |
| Shift + Arrows | Move 10mm |
| Click | Select element |
| Drag | Move element |

---

## 📐 Label Sizes | الأحجام

### Common Sizes | أحجام شائعة:

| Size | Usage | Grid (A4) |
|------|-------|-----------|
| 80×60mm | Perfume labels | 2×4 (8 labels) |
| 100×50mm | Supermarket | 2×5 (10 labels) |
| 50×30mm | Small labels | 4×9 (36 labels) |

### A4 Layout Examples | أمثلة A4:

```
2 × 4 = 8 labels per page (80×60mm)
3 × 6 = 18 labels per page (70×40mm)
4 × 10 = 40 labels per page (50×30mm)
```

---

## 🌍 Foreign Name Usage | استخدام الاسم الأجنبي

### Adding Foreign Names | إضافة الأسماء:

1. Open product form | افتح نموذج المنتج
2. Fill "Foreign Name" field | املأ حقل الاسم الأجنبي
   - Example: "Rose Perfume 30ml"
3. In template, enable "Show Foreign Name"
4. Position it using Visual Designer

### Use Cases | حالات الاستخدام:

- Arabic name + English name
- Local name + International name
- Brand name + Generic name

---

## 🖨️ Print Modes | أوضاع الطباعة

### 1. Single Labels | ملصقات فردية

- One label per page
- Size matches template
- Best for thermal printers
- High quality

### 2. A4 Sheet | ورقة A4

- Multiple labels per page
- Grid layout (customizable)
- Best for office printers
- Cost-effective

---

## ⚙️ Template Configuration | إعداد القالب

### Basic Settings | الإعدادات الأساسية:

```
Name: My Label Template
Width: 80mm
Height: 60mm
```

### Display Options | خيارات العرض:

- ☑️ Show Product Name
- ☑️ Show Foreign Name
- ☑️ Show Product Code
- ☑️ Show Price
- ☑️ Show Barcode
- ☑️ Show Logo

### A4 Layout | تخطيط A4:

```
Labels per Row: 2
Labels per Column: 4
Margin: 2mm
→ Total: 8 labels per page
```

### Visual Designer | المصمم المرئي:

Set exact positions for each element:
```
Name: X=5mm, Y=5mm
Foreign Name: X=5mm, Y=12mm
Code: X=40mm, Y=25mm
Price: X=40mm, Y=35mm
Barcode: X=5mm, Y=45mm
Logo: X=5mm, Y=5mm (W=20mm, H=15mm)
```

---

## 💡 Examples | أمثلة

### Example 1: Perfume Label | ملصق عطور

```
Template:
- Size: 80×60mm
- Elements: Name (AR), Foreign Name (EN), Code, Price, Logo
- Colors: Teal theme (#00A09D)
- A4: 2×4 grid

Product:
- Name: عطر الورد الجوري
- Foreign Name: Royal Rose Perfume 30ml
- Code: P-001
- Price: 99.99
```

### Example 2: Supermarket Label | ملصق سوبر ماركت

```
Template:
- Size: 100×50mm
- Elements: Name, Price (Large), Barcode
- Colors: Red theme (#E91E63)
- A4: 2×5 grid

Focus: Large price, Clear barcode
```

---

## 🔧 Requirements | المتطلبات

- Odoo 19.0+
- Python 3.10+
- Modules: product, stock, web

---

## 📞 Support | الدعم

- **Documentation**: This file
- **Issues**: GitHub Issues
- **Email**: support@lugal-ai.com

---

## 📝 License | الترخيص

LGPL-3

---

## 👨‍💻 Author | المطور

**Lugal AI**

---

## 🎉 Enjoy! | استمتع!

**Create beautiful labels with ease!**

**صمم ملصقات جميلة بسهولة!** 🏷️✨
