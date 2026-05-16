# تعليمات التحديث النهائية

## 🎯 الملفات الجاهزة للرفع

تم إصلاح جميع الأخطاء وإضافة جميع الميزات الجديدة:

### ✅ الميزات المضافة:
1. **حدود العناصر مع Text Wrapping** - للتحكم في عرض/ارتفاع العناصر
2. **وحدة القياس الفرعية (Sub UoM)** - من جدول البار كودات البديلة
3. **الخط المخصص MCS-Taybah-S_U** - كخط رئيسي لجميع النصوص

### ✅ الإصلاحات المطبقة:
- إصلاح XML Syntax Error (السطر 197) - تحويل `&` إلى `&amp;`

---

## 📦 الملفات المعدلة

### 1. Model:
```
addons/product_label_designer/models/product_label.py
```

### 2. View:
```
addons/product_label_designer/views/product_label_views.xml
```

### 3. Template:
```
addons/product_label_designer/reports/label_templates_simple.xml
```

### 4. الخط الجديد (مجلد كامل):
```
addons/product_label_designer/static/src/fonts/
  └── MCS-Taybah-S_U-normal..ttf
```

---

## 🚀 خطوات الرفع والتطبيق

### الخطوة 1: رفع الملفات للسيرفر

```bash
# في PowerShell من L:\Lugal-ai

# 1. رفع Model
scp addons/product_label_designer/models/product_label.py lugalai@192.168.116.211:/home/lugalai/Lugal-ai/addons/product_label_designer/models/

# 2. رفع View (مع الإصلاح)
scp addons/product_label_designer/views/product_label_views.xml lugalai@192.168.116.211:/home/lugalai/Lugal-ai/addons/product_label_designer/views/

# 3. رفع Template (مع الخط)
scp addons/product_label_designer/reports/label_templates_simple.xml lugalai@192.168.116.211:/home/lugalai/Lugal-ai/addons/product_label_designer/reports/

# 4. رفع مجلد الخطوط (كامل)
scp -r addons/product_label_designer/static/src/fonts lugalai@192.168.116.211:/home/lugalai/Lugal-ai/addons/product_label_designer/static/src/
```

### الخطوة 2: Upgrade Module على السيرفر

```bash
# اتصل بالسيرفر
ssh lugalai@192.168.116.211

# انتقل للمجلد
cd /home/lugalai/Lugal-ai

# فعّل البيئة الافتراضية
source venv/bin/activate

# Upgrade Module
./odoo-bin -c odoo.conf -d lugal -u product_label_designer --stop-after-init
```

### الخطوة 3: إعادة تشغيل Odoo

```bash
# الطريقة 1: باستخدام systemctl (إذا كان مثبت كخدمة)
sudo systemctl restart odoo

# أو الطريقة 2: تشغيل مباشر
cd /home/lugalai/Lugal-ai
source venv/bin/activate
./odoo-bin -c odoo.conf -d lugal --http-port=8070
```

### الخطوة 4: مسح Cache المتصفح

```
1. في المتصفح اضغط: Ctrl + Shift + Delete
2. اختر: Cached images and files
3. اضغط: Clear data
4. أعد تحميل الصفحة: Ctrl + F5
```

---

## 🧪 الاختبار

### اختبار 1: حدود العناصر

```
1. افتح: Settings → Technical → Label Templates
2. اختر قالب
3. انتقل إلى: Visual Designer
4. تحقق من وجود:
   ✓ Name Width
   ✓ Name Height
   ✓ Name Wrap
5. عدّل القيم واطبع ملصق
```

### اختبار 2: Sub UoM

```
1. افتح منتج
2. انتقل إلى: Alternative Barcodes
3. أضف باركود مع Sub UoM Name
4. في القالب فعّل: Show Sub Unit of Measure
5. امسح الباركود البديل
6. اطبع الملصق
7. تحقق من ظهور Sub UoM
```

### اختبار 3: الخط المخصص

```
1. اطبع ملصقig ;g adx [hi. hg]
2. افتح F12 → Network
3. ابحث عن: MCS-Taybah-S_U-normal..ttf
4. تحقق من: Status 200 (OK)
5. افتح Elements → اختر Product Name
6. تحقق من: font-family يحتوي على MCS_Taybah_Primary
```

---

## 🔍 استكشاف الأخطاء المحتملة

### مشكلة 1: XML Syntax Error بعد Upgrade

**السبب:** قد يكون هناك `&` أخرى غير مُهرّبة

**الحل:**
```bash
# على السيرفر
cd /home/lugalai/Lugal-ai
grep -n 'string="[^"]*&[^"]*"' addons/product_label_designer/views/product_label_views.xml

# إذا وجدت نتائج، استبدل & بـ &amp;
```

---

### مشكلة 2: الحقول الجديدة لا تظهر

**السبب:** Module لم يتم upgrade بشكل صحيح

**الحل:**
```bash
# Upgrade مع force
./odoo-bin -c odoo.conf -d lugal -u product_label_designer --stop-after-init --log-level=debug

# تحقق من الـ log
tail -f /var/log/odoo/odoo-server.log
```

---

### مشكلة 3: الخط لا يظهر (404)

**السبب:** مجلد fonts لم يُرفع أو الصلاحيات خاطئة

**الحل:**
```bash
# تحقق من وجود الملف
ls -la /home/lugalai/Lugal-ai/addons/product_label_designer/static/src/fonts/

# أعد رفع المجلد
scp -r addons/product_label_designer/static/src/fonts lugalai@192.168.116.211:/home/lugalai/Lugal-ai/addons/product_label_designer/static/src/

# اضبط الصلاحيات
chmod -R 755 /home/lugalai/Lugal-ai/addons/product_label_designer/static/
chmod 644 /home/lugalai/Lugal-ai/addons/product_label_designer/static/src/fonts/*.ttf
```

---

### مشكلة 4: Sub UoM لا يظهر

**الأسباب المحتملة:**
1. `show_sub_uom` غير مفعّل
2. الباركود المستخدم ليس بديل
3. Sub UoM Name فارغ

**الحل:**
```
1. تأكد من تفعيل: Display Options → ☑ Show Sub Unit of Measure
2. تأكد أن الباركود موجود في: Alternative Barcodes tab
3. تأكد أن Sub UoM Name مملوء في الباركود البديل
```

---

## 📊 ملخص التغييرات

### في Model (product_label.py):

```python
# حقول جديدة للحدود والـ Wrap
name_width = fields.Float(default=70.0)
name_height = fields.Float(default=15.0)
name_wrap = fields.Boolean(default=True)
foreign_name_width = fields.Float(default=70.0)
foreign_name_height = fields.Float(default=12.0)
foreign_name_wrap = fields.Boolean(default=True)
code_width = fields.Float(default=35.0)
price_width = fields.Float(default=35.0)

# حقول Sub UoM
show_sub_uom = fields.Boolean(default=False)
sub_uom_x = fields.Float(default=5.0)
sub_uom_y = fields.Float(default=20.0)
sub_uom_width = fields.Float(default=70.0)
sub_uom_rotation = fields.Float(default=0.0)
font_size_sub_uom = fields.Integer(default=10)
```

### في View (product_label_views.xml):

```xml
<!-- إضافة حقول Width/Height/Wrap في Visual Designer -->
<field name="name_width"/>
<field name="name_height"/>
<field name="name_wrap"/>
<!-- ... وغيرها -->

<!-- إضافة Sub UoM في Display Options -->
<field name="show_sub_uom"/>
```

### في Template (label_templates_simple.xml):

```xml
<!-- إضافة @font-face للخط الجديد -->
@font-face {
    font-family: 'MCS_Taybah_Primary';
    src: url('/product_label_designer/static/src/fonts/MCS-Taybah-S_U-normal..ttf') format('truetype');
}

<!-- استخدام الخط في جميع العناصر -->
font-family: 'MCS_Taybah_Primary', 'MCS_Taybah_Local', ...

<!-- إضافة CSS لـ Sub UoM -->
.product-sub-uom { ... }

<!-- عرض Sub UoM في Template -->
<t t-if="template.show_sub_uom">
    <div class="product-sub-uom">
        <t t-esc="alt_barcode.sub_uom_name"/>
    </div>
</t>
```

---

## ✅ Checklist النهائي

قبل الإعلان عن النجاح، تحقق من:

- [ ] **رفع الملفات**: جميع الملفات الـ 3 + مجلد fonts
- [ ] **Upgrade**: تم بدون أخطاء
- [ ] **إعادة التشغيل**: Odoo يعمل بشكل طبيعي
- [ ] **الحقول**: تظهر في Visual Designer
- [ ] **Name Width/Height**: يعملان
- [ ] **Name Wrap**: ينزل النص لأسطر متعددة
- [ ] **Sub UoM**: يظهر عند المسح
- [ ] **الخط**: يُحمّل بدون 404
- [ ] **الخط**: يُطبّق على النصوص
- [ ] **الطباعة**: تعمل بشكل صحيح

---

## 🎉 النجاح!

عند إتمام جميع الخطوات بنجاح، ستحصل على:

✅ **تحكم كامل في حدود العناصر**
✅ **Text Wrapping للنصوص الطويلة**
✅ **عرض وحدة القياس الفرعية**
✅ **خط عربي احترافي موحد**

---

**تاريخ:** 2025-12-06  
**الإصدار النهائي:** 2.0

