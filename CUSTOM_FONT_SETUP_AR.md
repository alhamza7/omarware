# إعداد الخط المخصص MCS-Taybah-S_U

## 🎨 نظرة عامة

تم إضافة الخط المخصص **MCS-Taybah-S_U-normal** كخط رئيسي لطباعة أسماء المنتجات والعناصر الأخرى في الملصقات.

---

## 📁 موقع الخط

### المسار الجديد:
```
addons/product_label_designer/static/src/fonts/MCS-Taybah-S_U-normal..ttf
```

### لماذا هذا المسار؟
✅ **أفضل الممارسات في Odoo** - الملفات الثابتة (fonts, images, CSS) تُحفظ في `/static/`
✅ **يتم تحميله تلقائياً** - Odoo يخدم الملفات من `/static/` بشكل تلقائي
✅ **منظم** - كل module له ملفاته الخاصة
✅ **سهل النقل** - عند نقل الـ module، الخط ينتقل معه

---

## 🔧 التعديلات المطبقة

### 1. تعريف الخط في CSS:

```css
/* Primary font: MCS-Taybah-S_U-normal from module fonts */
@font-face {
    font-family: 'MCS_Taybah_Primary';
    src: url('/product_label_designer/static/src/fonts/MCS-Taybah-S_U-normal..ttf') format('truetype');
    font-weight: normal;
    font-style: normal;
}

/* Fallback: Try to use local MCS_Taybah if installed */
@font-face {
    font-family: 'MCS_Taybah_Local';
    src: local('MCS_Taybah S_U Normal'), local('MCS Taybah'), local('mcs_taybah');
    font-weight: normal;
    font-style: normal;
}
```

### 2. استخدام الخط في العناصر:

```css
font-family: 'MCS_Taybah_Primary', 'MCS_Taybah_Local', 'Markazi Text', 'Arial', 'DejaVu Sans', sans-serif;
```

#### ترتيب الأولوية:
1. **MCS_Taybah_Primary** ← الخط الجديد من الـ module (أولوية أولى)
2. **MCS_Taybah_Local** ← إذا كان مثبت على النظام
3. **Markazi Text** ← خط عربي من Google Fonts
4. **Arial** ← خط عام
5. **DejaVu Sans** ← خط افتراضي في Linux
6. **sans-serif** ← خط النظام الافتراضي

---

## 📋 العناصر التي تستخدم الخط

### ✅ جميع العناصر التالية:
- 🏷️ **Product Name** (اسم المنتج)
- 🔤 **Product Code** (كود المنتج)
- 💰 **Price** (السعر)
- 📦 **Sub UoM** (وحدة القياس الفرعية)
- 📄 **Label Content** (محتوى الملصق العام)

---

## 🚀 خطوات التطبيق على السيرفر

### الخطوة 1: رفع مجلد الخطوط
```bash
# انتقل للمجلد المحلي
cd L:\Lugal-ai

# ارفع مجلد fonts كامل
scp -r addons/product_label_designer/static/src/fonts lugalai@192.168.116.211:/home/lugalai/Lugal-ai/addons/product_label_designer/static/src/
```

### الخطوة 2: رفع Template المحدث
```bash
# ارفع label_templates_simple.xml المحدث
scp addons/product_label_designer/reports/label_templates_simple.xml lugalai@192.168.116.211:/home/lugalai/Lugal-ai/addons/product_label_designer/reports/
```

### الخطوة 3: Upgrade Module
```bash
# اتصل بالسيرفر
ssh lugalai@192.168.116.211

# Upgrade module
cd /home/lugalai/Lugal-ai
source venv/bin/activate
./odoo-bin -c odoo.conf -d lugal -u product_label_designer --stop-after-init
```

### الخطوة 4: إعادة التشغيل
```bash
# أعد تشغيل Odoo
sudo systemctl restart odoo
# أو
./odoo-bin -c odoo.conf -d lugal --http-port=8070
```

### الخطوة 5: مسح Cache المتصفح
```
1. اضغط Ctrl + Shift + Delete
2. امسح Cached images and files
3. أعد تحميل الصفحة (Ctrl + F5)
```

---

## 🧪 الاختبار

### اختبار 1: التحقق من تحميل الخط

#### في المتصفح:
```
1. افتح الملصق في Odoo
2. اضغط F12 (Developer Tools)
3. انتقل إلى Network tab
4. ابحث عن: MCS-Taybah-S_U-normal..ttf
5. تحقق من Status: 200 (OK)
```

### اختبار 2: التحقق من استخدام الخط

#### في Developer Tools:
```
1. افتح Elements/Inspector
2. اختر عنصر Product Name
3. انظر إلى Computed Styles
4. تحقق من font-family
5. يجب أن يظهر: MCS_Taybah_Primary
```

### اختبار 3: الطباعة
```
1. اطبع ملصق منتج
2. تحقق من وضوح الخط العربي
3. قارن مع الخط القديم
```

---

## 🔍 استكشاف الأخطاء

### مشكلة: الخط لا يظهر (404 Error)

#### التشخيص:
```bash
# تحقق من وجود الملف
ls -la /home/lugalai/Lugal-ai/addons/product_label_designer/static/src/fonts/

# يجب أن يظهر:
# MCS-Taybah-S_U-normal..ttf
```

#### الحل:
```bash
# أعد رفع الخط
scp MCS-Taybah-S_U-normal..ttf lugalai@192.168.116.211:/home/lugalai/Lugal-ai/addons/product_label_designer/static/src/fonts/
```

---

### مشكلة: الخط لا يُطبق على النصوص

#### التشخيص:
```
1. افتح Developer Tools → Console
2. ابحث عن أخطاء CSS
3. تحقق من تحميل @font-face
```

#### الأسباب المحتملة:
1. ❌ **Cache** - امسح cache المتصفح
2. ❌ **صيغة الخط** - تأكد أن الملف `.ttf` صالح
3. ❌ **الصلاحيات** - تحقق من صلاحيات القراءة للملف

#### الحل:
```bash
# على السيرفر: تحقق من الصلاحيات
chmod 644 /home/lugalai/Lugal-ai/addons/product_label_designer/static/src/fonts/MCS-Taybah-S_U-normal..ttf

# أعد تشغيل Odoo
sudo systemctl restart odoo
```

---

### مشكلة: الخط يظهر في المعاينة لكن لا يطبع

#### السبب:
- بعض متصفحات الطباعة لا تدعم Web Fonts بشكل افتراضي

#### الحل:
```
1. في إعدادات الطباعة:
   ☑ Background graphics
   
2. في CSS، يمكن إضافة:
   @media print {
       * {
           -webkit-print-color-adjust: exact !important;
           print-color-adjust: exact !important;
       }
   }
```

---

## 💡 نصائح مهمة

### ✅ أفضل الممارسات:

1. **احتفظ بنسخة احتياطية** - احفظ الخط في مكان آمن
2. **اختبر على أجهزة مختلفة** - قد تختلف النتائج بين الأجهزة
3. **استخدم صيغ متعددة** - للتوافق الأفضل:
   ```css
   src: url('font.woff2') format('woff2'),
        url('font.woff') format('woff'),
        url('font.ttf') format('truetype');
   ```
4. **تحقق من الترخيص** - تأكد أن لديك حق استخدام الخط تجارياً

### ⚠️ تحذيرات:

1. **حجم الخط** - الخطوط الكبيرة تبطئ تحميل الصفحة
2. **التوافق** - بعض الخطوط قد لا تعمل في PDF generation
3. **Encoding** - تأكد أن الخط يدعم Unicode العربي

---

## 📊 قبل وبعد

### قبل:
```
font-family: 'MCS_Taybah_Local', 'Markazi Text', 'Arial', ...
                  ↑
            يعتمد على تثبيت الخط على النظام
```

### بعد:
```
font-family: 'MCS_Taybah_Primary', 'MCS_Taybah_Local', 'Markazi Text', ...
                  ↑
            يُحمّل من module مباشرةً (مضمون)
```

---

## 🎯 الخلاصة

### ✅ ما تم:
- نقل الخط من المجلد الرئيسي إلى `/static/src/fonts/`
- إضافة `@font-face` للخط الجديد
- جعله الخط الأساسي لجميع عناصر الملصق
- الاحتفاظ بـ fallback fonts للتوافق

### 📁 الملفات المعدلة:
1. `addons/product_label_designer/static/src/fonts/MCS-Taybah-S_U-normal..ttf` ← جديد
2. `addons/product_label_designer/reports/label_templates_simple.xml` ← معدّل

### 🚀 الخطوات التالية:
1. رفع الملفات للسيرفر
2. Upgrade module
3. اختبار الطباعة
4. مسح cache المتصفح إذا لزم الأمر

**الخط جاهز للاستخدام!** 🎉

---

**تاريخ:** 2025-12-06  
**الإصدار:** 1.0

