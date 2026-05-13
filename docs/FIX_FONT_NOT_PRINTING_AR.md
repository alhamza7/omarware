# حل مشكلة عدم ظهور الخط المخصص في الطباعة

## 🔍 التشخيص: لماذا لا يظهر الخط؟

### المشكلة:
عند توليد PDF في Odoo، يتم استخدام **wkhtmltopdf** الذي:
- ❌ لا يستطيع تحميل الخطوط من URLs في بعض الحالات
- ❌ لا يستطيع الوصول لخطوط Web Fonts
- ✅ يستطيع فقط استخدام الخطوط **المثبتة على النظام**

---

## ✅ الحل: تثبيت الخط على السيرفر

### الطريقة الأسهل (مع Script):

#### الخطوة 1: رفع الملفات للسيرفر
```bash
# في PowerShell من L:\Lugal-ai

# 1. رفع الخط
scp -r addons/product_label_designer/static/src/fonts lugalai@192.168.116.211:/home/lugalai/Lugal-ai/addons/product_label_designer/static/src/

# 2. رفع Template المحدث
scp addons/product_label_designer/reports/label_templates_simple.xml lugalai@192.168.116.211:/home/lugalai/Lugal-ai/addons/product_label_designer/reports/

# 3. رفع script التثبيت
scp install_custom_font.sh lugalai@192.168.116.211:/home/lugalai/Lugal-ai/
```

#### الخطوة 2: تشغيل Script التثبيت
```bash
# اتصل بالسيرفر
ssh lugalai@192.168.116.211

# انتقل للمجلد
cd /home/lugalai/Lugal-ai

# اجعل Script قابل للتنفيذ
chmod +x install_custom_font.sh

# شغل Script
./install_custom_font.sh
```

#### الخطوة 3: Upgrade Module
```bash
# Upgrade module
source venv/bin/activate
./odoo-bin -c odoo.conf -d lugal -u product_label_designer --stop-after-init

# أعد تشغيل Odoo
sudo systemctl restart odoo
```

---

### الطريقة اليدوية (بدون Script):

```bash
# 1. اتصل بالسيرفر
ssh lugalai@192.168.116.211

# 2. أنشئ مجلد الخطوط
mkdir -p ~/.fonts

# 3. انسخ الخط
cp /home/lugalai/Lugal-ai/addons/product_label_designer/static/src/fonts/MCS-Taybah-S_U-normal..ttf ~/.fonts/

# 4. حدث cache الخطوط
fc-cache -f -v

# 5. تحقق من التثبيت
fc-list | grep -i "taybah"

# 6. (اختياري) تثبيت على مستوى النظام
sudo mkdir -p /usr/share/fonts/truetype/mcs-taybah
sudo cp ~/.fonts/MCS-Taybah-S_U-normal..ttf /usr/share/fonts/truetype/mcs-taybah/
sudo fc-cache -f -v

# 7. أعد تشغيل Odoo
sudo systemctl restart odoo
```

---

## 🧪 التحقق من نجاح التثبيت

### 1. التحقق من تثبيت الخط على النظام:
```bash
# على السيرفر
fc-list | grep -i "taybah"

# يجب أن يظهر شيء مثل:
# /home/lugalai/.fonts/MCS-Taybah-S_U-normal..ttf: MCS Taybah:style=Normal
```

### 2. التحقق من استخدام wkhtmltopdf للخط:
```bash
# اختبار بسيط
echo '<html><head><style>@font-face{font-family:"MCS_Taybah_Local";src:local("MCS-Taybah-S_U-normal..");}body{font-family:"MCS_Taybah_Local";font-size:20pt;}</style></head><body>اختبار الخط العربي</body></html>' > test.html

wkhtmltopdf test.html test.pdf

# افتح test.pdf وتحقق من الخط
```

### 3. اختبر في Odoo:
```
1. افتح قالب ملصق
2. اطبع ملصق منتج
3. افتح PDF الناتج
4. تحقق من الخط
```

---

## 🔍 استكشاف الأخطاء

### المشكلة 1: الخط لا يظهر بعد التثبيت

**الأسباب المحتملة:**
1. wkhtmltopdf لم يُعاد تشغيله
2. Odoo لم يُعاد تشغيله
3. اسم الخط في local() لا يطابق

**الحل:**
```bash
# 1. أعد تشغيل Odoo بالكامل
sudo systemctl stop odoo
sudo systemctl start odoo

# 2. تحقق من اسم الخط الدقيق
fc-list | grep -i "taybah"

# 3. حدث Template ليطابق الاسم الصحيح
# في local('اسم الخط هنا')
```

---

### المشكلة 2: الخط يعمل في المعاينة لكن ليس في PDF

**السبب:**
- المعاينة تستخدم متصفح الويب (يدعم Web Fonts)
- PDF يستخدم wkhtmltopdf (يحتاج خطوط النظام)

**الحل:**
- تأكد من تثبيت الخط على النظام (الحلول أعلاه)

---

### المشكلة 3: Permission Denied عند النسخ

**الحل:**
```bash
# استخدم sudo للتثبيت على مستوى النظام
sudo mkdir -p /usr/share/fonts/truetype/mcs-taybah
sudo cp ~/MCS-Taybah-S_U-normal..ttf /usr/share/fonts/truetype/mcs-taybah/
sudo chmod 644 /usr/share/fonts/truetype/mcs-taybah/MCS-Taybah-S_U-normal..ttf
sudo fc-cache -f -v
```

---

## 💡 نصائح مهمة

### ✅ أفضل الممارسات:

1. **تثبيت على مستوى النظام** - يضمن الوصول لجميع المستخدمين
2. **استخدم أسماء بسيطة** - تجنب الأحرف الخاصة في اسم الملف
3. **دائماً fc-cache** - بعد أي تعديل على الخطوط
4. **أعد تشغيل Odoo** - بعد تثبيت خطوط جديدة

### ⚠️ تحذيرات:

1. **الترخيص** - تأكد من حقوق استخدام الخط
2. **الحجم** - الخطوط الكبيرة تبطئ PDF generation
3. **التوافق** - بعض الخطوط قد لا تعمل مع wkhtmltopdf

---

## 📊 المقارنة بين الطرق

| الطريقة | مكان الخط | PDF | Browser | التعقيد |
|---------|-----------|-----|---------|---------|
| **URL (Web Font)** | Module/static | ❌ | ✅ | سهل |
| **System Install** | /usr/share/fonts | ✅ | ✅ | متوسط |
| **User Install** | ~/.fonts | ✅ | ✅ | سهل |
| **Base64 Embed** | في CSS | ✅ | ✅ | معقد |

**الحل الموصى به:** تثبيت على النظام (System Install) ✅

---

## 🎯 الخلاصة

### ما تم تحديثه:

1. ✅ إضافة `font-display: swap` في @font-face
2. ✅ إضافة أسماء بديلة أكثر في local()
3. ✅ إنشاء script تثبيت تلقائي
4. ✅ دليل شامل لحل المشكلة

### الخطوات المطلوبة:

1. رفع الملفات للسيرفر
2. تشغيل `install_custom_font.sh`
3. Upgrade module
4. إعادة تشغيل Odoo
5. اختبار الطباعة

**بعد هذه الخطوات، الخط سيعمل في PDF! 🎉**

---

**تاريخ:** 2025-12-06  
**الإصدار:** 3.0

