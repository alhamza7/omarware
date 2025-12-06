# تعليمات التطبيق: حدود العناصر + وحدة القياس الفرعية

## 🎯 نظرة عامة
تم إضافة ميزتين جديدتين:
1. **حدود للعناصر (Width/Height/Wrap)** - للتحكم في مساحة كل عنصر
2. **عرض وحدة القياس الفرعية** - من جدول البار كودات البديلة

---

## 📦 الملفات المعدلة

### 1. النموذج (Model):
```
addons/product_label_designer/models/product_label.py
```

### 2. الواجهة (View):
```
addons/product_label_designer/views/product_label_views.xml
```

### 3. القالب (Template):
```
addons/product_label_designer/reports/label_templates_simple.xml
```

---

## 🚀 خطوات التطبيق

### الخطوة 1: رفع الملفات للسيرفر
```bash
# ارفع الملفات المعدلة إلى السيرفر
scp addons/product_label_designer/models/product_label.py lugalai@192.168.116.211:/home/lugalai/Lugal-ai/addons/product_label_designer/models/
scp addons/product_label_designer/views/product_label_views.xml lugalai@192.168.116.211:/home/lugalai/Lugal-ai/addons/product_label_designer/views/
scp addons/product_label_designer/reports/label_templates_simple.xml lugalai@192.168.116.211:/home/lugalai/Lugal-ai/addons/product_label_designer/reports/
```

### الخطوة 2: Upgrade Module
```bash
# اتصل بالسيرفر
ssh lugalai@192.168.116.211

# Upgrade Module
cd /home/lugalai/Lugal-ai
source venv/bin/activate
./odoo-bin -c odoo.conf -d lugal -u product_label_designer --stop-after-init
```

### الخطوة 3: إعادة تشغيل Odoo
```bash
# أعد تشغيل Odoo
sudo systemctl restart odoo
# أو
cd /home/lugalai/Lugal-ai
source venv/bin/activate
./odoo-bin -c odoo.conf -d lugal --http-port=8070
```

---

## ⚙️ الإعدادات الجديدة

### في Visual Designer:

#### Name Position & Size:
```
- Name X Position: 5mm
- Name Y Position: 5mm
- Name Width: 70mm          ← جديد
- Name Height: 15mm         ← جديد
☑ Name Text Wrap            ← جديد
- Name Rotation: 0°
```

#### Foreign Name Position & Size:
```
- Foreign Name X: 5mm
- Foreign Name Y: 12mm
- Foreign Name Width: 70mm  ← جديد
- Foreign Name Height: 12mm ← جديد
☑ Foreign Name Wrap         ← جديد
- Foreign Name Rotation: 0°
```

#### Code Position & Size:
```
- Code X: 40mm
- Code Y: 25mm
- Code Width: 35mm          ← جديد
- Code Rotation: 0°
```

#### Price Position & Size:
```
- Price X: 40mm
- Price Y: 35mm
- Price Width: 35mm         ← جديد
- Price Rotation: 0°
```

#### Sub UoM Position & Size (يظهر فقط عند تفعيل show_sub_uom):
```
- Sub UoM X: 5mm            ← جديد
- Sub UoM Y: 20mm           ← جديد
- Sub UoM Width: 70mm       ← جديد
- Sub UoM Rotation: 0°      ← جديد
```

### في Display Options:
```
☑ Show Sub Unit of Measure  ← جديد
```

### في Style & Fonts:
```
- Sub UoM Font Size: 10pt   ← جديد
```

---

## 🧪 الاختبار

### اختبار 1: Text Wrapping

#### 1.1 افتح قالب موجود
```
Settings → Technical → Label Templates
```

#### 1.2 عدّل الإعدادات
```
Visual Designer:
  - Name Width: 40mm        ← عرض صغير
  - Name Height: 20mm       ← ارتفاع كبير
  ☑ Name Text Wrap          ← مفعّل
```

#### 1.3 اطبع منتج باسم طويل
```
اختر منتج مثل: "ماء معدني طبيعي من الينابيع الجبلية"
اطبع الملصق
النتيجة المتوقعة: النص موزع على أكثر من سطر
```

#### 1.4 اختبر بدون Wrap
```
Visual Designer:
  ☐ Name Text Wrap          ← معطّل

النتيجة المتوقعة: النص في سطر واحد مع ... في النهاية
```

---

### اختبار 2: Sub UoM

#### 2.1 أنشئ باركود بديل
```
Product → Alternative Barcodes → Create:
  - Barcode: 789012345
  - Sub UoM Name: "علبة 12 حبة"
  - Save
```

#### 2.2 فعّل العرض في القالب
```
Display Options:
  ☑ Show Sub Unit of Measure
```

#### 2.3 اضبط الموضع
```
Visual Designer → Sub UoM Position & Size:
  - Sub UoM X: 5mm
  - Sub UoM Y: 20mm
  - Sub UoM Width: 70mm
```

#### 2.4 اطبع الملصق
```
Barcode Scanner → Scan Barcode: 789012345
Print Label
النتيجة المتوقعة: يظهر "علبة 12 حبة" على الملصق
```

---

## 📋 التحقق من النجاح

### ✅ Checklist:

- [ ] الملفات مرفوعة للسيرفر
- [ ] Module تم upgrade بدون أخطاء
- [ ] Odoo يعمل بشكل طبيعي
- [ ] الحقول الجديدة تظهر في Visual Designer
- [ ] Name Width/Height يعملان بشكل صحيح
- [ ] Name Wrap يعمل (النص ينزل لأسطر متعددة)
- [ ] Sub UoM يظهر عند مسح باركود بديل
- [ ] Sub UoM له موضع وحجم قابل للتحكم
- [ ] Code Width و Price Width يعملان

---

## 🔍 استكشاف الأخطاء

### مشكلة: الحقول الجديدة لا تظهر
**الحل:**
```bash
# Upgrade مع restart
./odoo-bin -c odoo.conf -d lugal -u product_label_designer --stop-after-init
sudo systemctl restart odoo
```

### مشكلة: Text Wrap لا يعمل
**الحل:**
```
1. تأكد أن Name Height كبير كفاية (> 12mm)
2. تأكد أن Name Wrap مفعّل
3. امسح cache المتصفح
4. أعد تحميل الصفحة
```

### مشكلة: Sub UoM لا يظهر
**الحل:**
```
1. تأكد أن show_sub_uom مفعّل
2. تأكد أنك تمسح باركود بديل (ليس الرئيسي)
3. تأكد أن الباركود له sub_uom_name
4. تحقق من الـ logs:
   tail -f /var/log/odoo/odoo-server.log
```

### مشكلة: XML Syntax Error
**الحل:**
```bash
# تحقق من الـ XML
xmllint --noout addons/product_label_designer/reports/label_templates_simple.xml

# إذا كان هناك خطأ، راجع السطر المذكور
```

---

## 💡 نصائح الاستخدام

### للـ Text Wrapping:
1. **استخدمه للملصقات الصغيرة** - لتوفير المساحة
2. **اضبط Height بعناية** - لتجنب قطع النص
3. **جرب مع أسماء مختلفة** - قصيرة وطويلة
4. **قد يتعارض مع Auto Font Sizing** - اختر أحدهما

### للـ Sub UoM:
1. **استخدمه للتوضيح** - مثل "علبة"، "كرتونة"، "حبة"
2. **املأه في جدول Alternative Barcodes** - لكل باركود بديل
3. **اضبط الموضع بعيداً عن العناصر الأخرى**
4. **استخدم خط صغير** - 8-10pt

---

## 📚 المراجع

- الدليل الكامل: `ELEMENT_BOUNDS_SUB_UOM_AR.md`
- دليل Auto Font Sizing: `AUTO_FONT_SIZING_AR.md`
- دليل Template Rotation: `LABEL_ROTATION_180_AR.md`

---

## ✅ الخلاصة

### ما تم إضافته:

#### الحقول:
- ✅ `name_width`, `name_height`, `name_wrap`
- ✅ `foreign_name_width`, `foreign_name_height`, `foreign_name_wrap`
- ✅ `code_width`, `price_width`
- ✅ `show_sub_uom`
- ✅ `sub_uom_x`, `sub_uom_y`, `sub_uom_width`, `sub_uom_rotation`
- ✅ `font_size_sub_uom`

#### الوظائف:
- ✅ Text Wrapping للـ Name و Foreign Name
- ✅ حدود Width لجميع العناصر
- ✅ عرض Sub UoM من alternative barcodes
- ✅ تحكم كامل في موضع وحجم Sub UoM

**كل شيء جاهز للاستخدام!** 🎉

---

**تاريخ:** 2025-12-06  
**الإصدار:** 1.0

