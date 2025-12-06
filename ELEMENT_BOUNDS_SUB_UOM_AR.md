# الميزات الجديدة: حدود العناصر + وحدة القياس الفرعية

## 📋 نظرة عامة

تم إضافة ميزتين مهمتين:
1. **حدود للعناصر مع Text Wrapping** - التحكم في عرض/ارتفاع العناصر مع إمكانية نزول النص للأسفل
2. **عرض وحدة القياس الفرعية** - من جدول البار كودات البديلة

---

## 🎯 الميزة 1: حدود العناصر مع Text Wrapping

### ما الجديد؟

#### للـ Name:
- ✅ `name_width` - العرض الأقصى (بالملم)
- ✅ `name_height` - الارتفاع الأقصى (بالملم)  
- ✅ `name_wrap` - السماح بتقسيم النص لعدة أسطر

#### للـ Foreign Name:
- ✅ `foreign_name_width`
- ✅ `foreign_name_height`
- ✅ `foreign_name_wrap`

#### للـ Code & Price:
- ✅ `code_width`
- ✅ `price_width`

### كيفية الاستخدام:

#### الخطوة 1: افتح القالب
```
Settings → Label Templates → Visual Designer
```

#### الخطوة 2: إعدادات Name
```
Name Position & Size:
  - Name X Position: 5mm
  - Name Y Position: 5mm
  - Name Width: 70mm        ← العرض الأقصى
  - Name Height: 15mm       ← الارتفاع الأقصى
  ☑ Name Text Wrap          ← السماح بالتقسيم
```

### أمثلة:

#### مثال 1: نص قصير (بدون wrap)
```
الإعدادات:
  Width: 70mm
  Height: 15mm
  ☑ Text Wrap

النتيجة:
┌────────────────────────────────┐
│       ماء معدني               │
└────────────────────────────────┘
```

#### مثال 2: نص طويل (مع wrap)
```
الإعدادات:
  Width: 50mm  ← عرض أصغر
  Height: 20mm ← ارتفاع أكبر
  ☑ Text Wrap

النتيجة:
┌─────────────────────┐
│  ماء معدني طبيعي   │
│  من الينابيع        │  ← سطر ثاني
└─────────────────────┘
```

#### مثال 3: بدون wrap (قطع النص)
```
الإعدادات:
  Width: 50mm
  Height: 15mm
  ☐ Text Wrap  ← معطّل

النتيجة:
┌─────────────────────┐
│  ماء معدني طبيع...  │  ← يقطع بـ ...
└─────────────────────┘
```

### CSS المطبق:

#### عند تفعيل Wrap:
```css
white-space: normal;
word-wrap: break-word;
overflow-wrap: break-word;
max-height: 15mm;
overflow: hidden;
```

#### عند تعطيل Wrap:
```css
white-space: nowrap;
overflow: hidden;
text-overflow: ellipsis;
```

---

## 🏷️ الميزة 2: عرض وحدة القياس الفرعية

### ما هي؟

عرض اسم وحدة القياس الفرعية (`sub_uom_name`) من جدول البار كودات البديلة (`product.barcode.alternative`).

### متى تظهر؟

- ✅ عند مسح باركود **بديل** (من جدول alternative barcodes)
- ✅ يجب أن يكون الباركود يحتوي على `sub_uom_name`
- ✅ يجب تفعيل `Show Sub Unit of Measure` في القالب

### كيفية الاستخدام:

#### الخطوة 1: تفعيل العرض
```
Display Options:
  ☑ Show Sub Unit of Measure
```

#### الخطوة 2: إعدادات الموضع والحجم
```
Visual Designer → Sub UoM Position & Size:
  - Sub UoM X Position: 5mm
  - Sub UoM Y Position: 20mm
  - Sub UoM Width: 70mm
  - Sub UoM Rotation: 0°
```

#### الخطوة 3: إعدادات الخط
```
Style & Fonts:
  - Sub UoM Font Size: 10pt
```

### مثال عملي:

#### السيناريو:
```
المنتج: ماء معدني
الباركود الرئيسي: 123456
البار كودات البديلة:
  - Barcode: 789012
    Sub UoM Name: "زجاجة 500 مل"  ← هذا ما سيظهر
```

#### النتيجة على الملصق:
```
┌─────────────────────────────────┐
│       ماء معدني                 │
│    زجاجة 500 مل                 │ ← Sub UoM
│                                 │
│    R00072                       │
│    [QR Code]                    │
│    25.00 ريال                   │
└─────────────────────────────────┘
```

### كيف يعمل تقنياً؟

```xml
<!-- في Template -->
<t t-if="template.show_sub_uom">
    <t t-set="scanned_barcode" t-value="data.get('scanned_barcode')"/>
    <t t-if="scanned_barcode">
        <!-- البحث في جدول البار كودات البديلة -->
        <t t-set="alt_barcode" t-value="env['product.barcode.alternative'].search([
            ('barcode', '=', scanned_barcode.strip().strip('/')),
            ('product_id', '=', o.id)
        ], limit=1)"/>
        
        <!-- عرض sub_uom_name إذا وجد -->
        <t t-if="alt_barcode and alt_barcode.sub_uom_name">
            <div class="product-sub-uom">
                <t t-esc="alt_barcode.sub_uom_name"/>
            </div>
        </t>
    </t>
</t>
```

---

## 📊 جدول المقارنة

### قبل وبعد:

| الميزة | قبل | بعد |
|--------|-----|-----|
| **عرض العناصر** | ثابت | قابل للتحكم ✅ |
| **ارتفاع العناصر** | غير محدد | قابل للتحكم ✅ |
| **Text Wrap** | غير متاح | متاح ✅ |
| **Sub UoM** | غير متاح | يظهر من الباركود ✅ |
| **التحكم في الموضع** | X, Y فقط | X, Y, Width, Height ✅ |

---

## 🎨 أمثلة التصميم

### تصميم 1: ملصق صغير مع wrap
```
الإعدادات:
  - Label: 50mm × 30mm
  - Name Width: 45mm
  - Name Height: 12mm
  - ☑ Name Wrap
  - ☑ Show Sub UoM

النتيجة:
  النص يتوزع على سطرين
  + عرض وحدة القياس
```

### تصميم 2: ملصق كبير بدون wrap
```
الإعدادات:
  - Label: 100mm × 60mm
  - Name Width: 90mm
  - Name Height: 20mm
  - ☐ Name Wrap
  
النتيجة:
  النص في سطر واحد
  إذا تجاوز يقطع بـ ...
```

---

## 💡 نصائح مهمة

### ✅ افعل:
1. **استخدم Wrap للملصقات الصغيرة** - يوفر مساحة
2. **حدد الـ Height عند تفعيل Wrap** - لتجنب تجاوز العنصر
3. **اختبر مع أسماء مختلفة** - قصيرة وطويلة
4. **استخدم Sub UoM للتوضيح** - مثل "علبة 12 حبة"

### ⚠️ انتبه:
1. **Height مع Wrap** - إذا كان صغير جداً قد يقطع النص
2. **Font Size مع Width** - قد تحتاج لتصغير الخط
3. **Auto Font Sizing + Wrap** - قد يتعارضان، اختر أحدهما
4. **Sub UoM فقط للبار كودات البديلة** - لن يظهر للباركود الرئيسي

### ❌ لا تفعل:
1. لا تجعل Width أصغر من النص الأقصر
2. لا تجعل Height أقل من سطر واحد
3. لا تنسى تفعيل `show_sub_uom` إذا أردت عرضها

---

## 🔧 التفاصيل التقنية

### الحقول المضافة في Model:

```python
# Name
name_width = fields.Float(default=70.0)
name_height = fields.Float(default=15.0)
name_wrap = fields.Boolean(default=True)

# Foreign Name
foreign_name_width = fields.Float(default=70.0)
foreign_name_height = fields.Float(default=12.0)
foreign_name_wrap = fields.Boolean(default=True)

# Code & Price
code_width = fields.Float(default=35.0)
price_width = fields.Float(default=35.0)

# Sub UoM
show_sub_uom = fields.Boolean(default=False)
sub_uom_x = fields.Float(default=5.0)
sub_uom_y = fields.Float(default=20.0)
sub_uom_width = fields.Float(default=70.0)
sub_uom_rotation = fields.Float(default=0.0)
font_size_sub_uom = fields.Integer(default=10)
```

### CSS Example:

```css
.product-name {
    width: 70mm;
    max-height: 15mm;
    white-space: normal;      /* عند تفعيل wrap */
    word-wrap: break-word;
    overflow: hidden;
    line-height: 1.2;
}

.product-sub-uom {
    position: absolute;
    left: 5mm;
    top: 20mm;
    width: 70mm;
    font-size: 10pt;
    color: #555;
}
```

---

## 🧪 الاختبار

### خطوات الاختبار:

#### 1. اختبار Text Wrap:
```
- اختر منتج باسم قصير (< 10 أحرف)
- اختر منتج باسم طويل (> 50 حرف)
- فعّل Wrap واطبع كليهما
- عطّل Wrap واطبع كليهما
- قارن النتائج
```

#### 2. اختبار Sub UoM:
```
- أنشئ باركود بديل مع sub_uom_name
- فعّل Show Sub Unit of Measure
- امسح الباركود البديل
- تحقق من ظهور sub_uom_name
```

---

## ✅ الخلاصة

### الميزة 1: حدود العناصر
- ✅ تحكم كامل في Width و Height
- ✅ Text Wrap لتقسيم النص
- ✅ يعمل مع Auto Font Sizing
- ✅ قابل للتخصيص لكل قالب

### الميزة 2: Sub UoM
- ✅ يظهر من جدول alternative barcodes
- ✅ تحكم كامل في الموضع والحجم
- ✅ يظهر فقط عند المسح
- ✅ مفيد لتوضيح الوحدات الفرعية

**الآن لديك تحكم أكبر في التصميم والمحتوى!** 🎉

---

**تاريخ الإنشاء:** 2025-12-06  
**الإصدار:** 1.0

