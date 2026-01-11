# 🔧 إصلاح مشكلة الترميز العربي في PDF

**المشكلة:** الحروف العربية تظهر كرموز غريبة في PDF  
**السبب:** wkhtmltopdf لا يدعم الخطوط العربية افتراضياً  
**التاريخ:** 2026-01-11

---

## 🐛 المشكلة

عند طباعة الفاتورة، الحروف العربية تظهر هكذا:
```
❌ Ø´Ø±±ÙfØ© Ù†Ù^Ø± Ø§Ù„ÙfØ^Ø±Ø§Ø³
✅ شركة نور الفراس
```

---

## ✅ الحل الكامل

### الطريقة 1: تثبيت الخطوط العربية على الخادم (الحل الأفضل)

#### على الخادم (192.168.116.211):

```bash
# 1. تحديث النظام
sudo apt-get update

# 2. تثبيت خطوط DejaVu (تدعم العربية)
sudo apt-get install -y fonts-dejavu fonts-dejavu-core fonts-dejavu-extra

# 3. تثبيت خطوط عربية إضافية
sudo apt-get install -y fonts-arabeyes fonts-farsiweb

# 4. تثبيت خطوط Microsoft (اختياري)
sudo apt-get install -y ttf-mscorefonts-installer

# 5. تحديث ذاكرة الخطوط
sudo fc-cache -f -v

# 6. إعادة تشغيل Odoo
sudo systemctl restart odoo
```

✅ **بعد هذا، الخطوط العربية ستعمل!**

---

### الطريقة 2: استخدام wkhtmltopdf المحدث

في بعض الأحيان، إصدار wkhtmltopdf القديم لا يدعم UTF-8 بشكل جيد.

#### التحقق من الإصدار:

```bash
wkhtmltopdf --version
```

#### تثبيت إصدار أحدث:

```bash
# تحميل النسخة الأحدث
cd /tmp
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb

# تثبيت
sudo dpkg -i wkhtmltox_0.12.6.1-2.jammy_amd64.deb

# إذا ظهرت أخطاء dependencies
sudo apt-get install -f

# إعادة تشغيل Odoo
sudo systemctl restart odoo
```

---

### الطريقة 3: تحديث إعدادات Odoo

#### تحديث ملف odoo.conf:

```bash
sudo nano /etc/odoo/odoo.conf
```

#### أضف/عدّل:

```ini
[options]
; ... إعدادات أخرى ...

# Report settings
reportgz = False
workers = 2
```

#### احفظ وأعد التشغيل:

```bash
sudo systemctl restart odoo
```

---

## 📋 التعديلات التي قمت بها في الكود

### 1. إضافة ملف CSS للخطوط العربية:
**الملف:** `addons/pos_perfume_custom/static/src/css/pos_report_arabic.css`

```css
.pos-arabic-report {
    font-family: 'DejaVu Sans', 'Arial', 'Tahoma', sans-serif !important;
    direction: rtl;
    text-align: right;
}
```

### 2. تحديث manifest لتحميل CSS:
**الملف:** `addons/pos_perfume_custom/__manifest__.py`

```python
'web.report_assets_common': [
    'pos_perfume_custom/static/src/css/pos_report_arabic.css',
],
```

### 3. إصلاح تنسيق الأرقام بالدينار:
**قبل:**
```
78,000.000 IQD  ← أصفار زائدة
```

**بعد:**
```
78,000 د.ع  ← نظيف
```

### 4. تكبير اللوجو:
```xml
max-height: 120px  ← من 80px
max-width: 250px   ← من 200px
```

---

## 🚀 خطوات التطبيق الكاملة

### 1. على الخادم (192.168.116.211):

```bash
# تثبيت الخطوط
sudo apt-get update
sudo apt-get install -y fonts-dejavu fonts-dejavu-core fonts-dejavu-extra
sudo apt-get install -y fonts-arabeyes fonts-farsiweb
sudo fc-cache -f -v

# إعادة تشغيل Odoo
sudo systemctl restart odoo
```

### 2. من المتصفح:

```
1. Apps → Developer Mode
2. ابحث: POS Perfume Custom
3. Upgrade ⬆️
4. Settings → Developer Tools → Clear Assets
5. Ctrl + Shift + Delete → امسح كل شيء
6. Ctrl + F5
```

### 3. اختبر الطباعة:

```
POS Perfume → طلب جديد → 💾 Save → 🖨️ Print
```

✅ **الآن يجب أن تظهر العربية بشكل صحيح!**

---

## 🔍 التحقق من الخطوط المثبتة

```bash
# التحقق من وجود خطوط DejaVu
fc-list | grep -i dejavu

# التحقق من وجود خطوط عربية
fc-list :lang=ar

# يجب أن ترى:
# DejaVu Sans
# DejaVu Sans Mono
# Arabic fonts
```

---

## 📊 قبل وبعد

### قبل الإصلاح:
```
❌ Ø´Ø±±ÙfØ© Ù†Ù^Ø± Ø§Ù„ÙfØ^Ø±Ø§Ø³
❌ 78,000.000 IQD
❌ لوجو صغير جداً
```

### بعد الإصلاح:
```
✅ شركة نور الفراس
✅ 78,000 د.ع
✅ لوجو واضح وكبير
✅ رقم SAP: 2600006 (واضح باللون الأخضر)
```

---

## 🆘 حل المشاكل

### المشكلة: العربية ما زالت لا تظهر بعد تثبيت الخطوط
**الحل:**
```bash
# تأكد من تحديث ذاكرة الخطوط
sudo fc-cache -f -v

# أعد تشغيل Odoo
sudo systemctl restart odoo

# امسح الكاش
sudo rm -rf /tmp/wkhtmlto*
```

### المشكلة: اللوجو لا يظهر
**الحل:**
1. Settings → Companies → رفع لوجو جديد
2. صيغة PNG أو JPG
3. حجم: 300-500 KB
4. أبعاد موصى بها: 400x150 بكسل

### المشكلة: الأرقام تظهر بتنسيق خاطئ
**الحل:**
تم إصلاحه في الكود باستخدام:
```python
'{:,.0f}'.format(o.amount_total_iqd)
```

---

## 📝 ملاحظات مهمة

### 1. wkhtmltopdf:
- هو المسؤول عن تحويل HTML إلى PDF
- يحتاج لخطوط مثبتة على الخادم
- لا يكفي وضع خطوط في الكود

### 2. الخطوط الموصى بها:
- **DejaVu Sans** ← يدعم العربية جيداً
- **Arial** ← إذا كان متوفراً
- **Tahoma** ← جيد للعربية

### 3. الترميز:
- يجب أن يكون UTF-8
- تم التأكد من ذلك في الكود

---

## ✅ قائمة التحقق

بعد التطبيق، تأكد من:

- [ ] تثبيت الخطوط على الخادم
- [ ] تحديث fc-cache
- [ ] إعادة تشغيل Odoo
- [ ] تحديث الوحدة
- [ ] مسح الكاش
- [ ] رفع لوجو الشركة
- [ ] اختبار الطباعة

---

## 🎯 النتيجة النهائية المتوقعة

بعد تطبيق جميع الخطوات:

✅ **العربية:** واضحة ومقروءة  
✅ **اللوجو:** كبير وواضح (120px)  
✅ **رقم SAP:** 2600006 (بارز باللون الأخضر)  
✅ **الأرقام:** مُنسّقة بشكل صحيح (78,000 د.ع)  
✅ **التصميم:** احترافي ومنظم  
✅ **الطباعة:** ممتازة  

---

**الحالة:** ✅ جاهز للتطبيق  
**الأولوية:** 🔥 عالية (يجب تثبيت الخطوط على الخادم)

**الخطوة التالية:** قم بتثبيت الخطوط على الخادم أولاً! 🚀

