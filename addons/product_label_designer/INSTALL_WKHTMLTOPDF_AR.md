# تثبيت wkhtmltopdf - ضروري للطباعة!

## ⚠️ المشكلة:
```
Unable to find Wkhtmltopdf on this system
```

**السبب:** wkhtmltopdf غير مثبت (ضروري لتوليد PDF)

---

## ✅ الحل: تثبيت wkhtmltopdf

### **لنظام Windows (نظامك):**

#### الطريقة 1: تحميل مباشر (الأسرع)

```
1. اذهب إلى:
   https://wkhtmltopdf.org/downloads.html

2. اختر Windows:
   - wkhtmltox-0.12.6-1.msvc2015-win64.exe (64-bit)
   أو
   - wkhtmltox-0.12.6-1.msvc2015-win32.exe (32-bit)

3. حمّل الملف

4. شغّل المثبت (Double-click)

5. اتبع التعليمات (Next, Next, Install)

6. **مهم**: تثبيت في المسار الافتراضي:
   C:\Program Files\wkhtmltopdf\

7. أعد تشغيل Odoo
```

---

#### الطريقة 2: عبر Chocolatey

```powershell
# إذا كان لديك Chocolatey مثبت
choco install wkhtmltopdf -y
```

---

#### الطريقة 3: التحميل المباشر

**رابط مباشر (64-bit):**
```
https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.msvc2015-win64.exe
```

---

### **لنظام Linux:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install wkhtmltopdf -y

# CentOS/RHEL
sudo yum install wkhtmltopdf -y

# Arch Linux
sudo pacman -S wkhtmltopdf
```

---

### **لنظام macOS:**

```bash
# استخدم Homebrew
brew install wkhtmltopdf
```

---

## ✅ التحقق من التثبيت:

### في Command Line:

```cmd
# Windows
wkhtmltopdf --version

# يجب أن يظهر:
wkhtmltopdf 0.12.6 (with patched qt)
```

---

## 🔧 إعداد Odoo:

بعد تثبيت wkhtmltopdf:

### Windows:

```
1. أعد تشغيل Odoo تماماً (Ctrl+C ثم شغّل مرة أخرى)

2. تحقق من odoo.conf (اختياري):
   
[options]
...
# يمكنك إضافة المسار يدوياً إذا لم يجده تلقائياً
wkhtmltopdf = C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe
```

---

## ✅ اختبار wkhtmltopdf:

بعد التثبيت:

```
1. أعد تشغيل Odoo
2. افتح أي منتج
3. Print → أي تقرير
4. يجب أن يفتح PDF! ✅
```

---

## 🎯 **الخطوات الكاملة:**

```
┌─────────────────────────────────┐
│ 1. تثبيت wkhtmltopdf           │
│    - حمّل من الموقع            │
│    - شغّل المثبت               │
│    - Next, Next, Install        │
└─────────────────────────────────┘
            ⬇️
┌─────────────────────────────────┐
│ 2. أعد تشغيل Odoo              │
│    - Ctrl+C                     │
│    - شغّل مرة أخرى             │
└─────────────────────────────────┘
            ⬇️
┌─────────────────────────────────┐
│ 3. جرب الطباعة                │
│    - Quick Print                │
│    - Print Now                  │
│    - PDF يفتح! 🎉              │
└─────────────────────────────────┘
```

---

## 📥 **روابط التحميل:**

### Windows 64-bit (موصى به):
```
https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.msvc2015-win64.exe
```

### Windows 32-bit:
```
https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.msvc2015-win32.exe
```

---

## ⚠️ **ملاحظة مهمة:**

wkhtmltopdf ضروري لـ:
- ✅ تقارير PDF في Odoo
- ✅ فواتير PDF
- ✅ ملصقات PDF
- ✅ أي تقرير PDF

**بدونه:** التقارير تظهر HTML فقط (لا PDF)

---

## 🔍 **استكشاف الأخطاء:**

### إذا لم يجده Odoo بعد التثبيت:

```
1. تحقق من المسار:
   C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe
   
2. في odoo.conf أضف:
   wkhtmltopdf = C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe

3. أعد تشغيل Odoo
```

### في Linux إذا كان error:

```bash
# تثبيت النسخة الكاملة مع Qt patched
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bionic_amd64.deb
sudo dpkg -i wkhtmltox_0.12.6-1.bionic_amd64.deb
sudo apt-get install -f
```

---

## ✅ **بعد التثبيت:**

```
كل التقارير ستعمل:
✅ ملصقات المنتجات
✅ فواتير المبيعات
✅ عروض الأسعار
✅ تقارير المخزون
✅ أي تقرير PDF في Odoo
```

---

## 🎊 **خلاصة:**

```
المشكلة: wkhtmltopdf غير مثبت
الحل: تثبيت wkhtmltopdf
الوقت: 5 دقائق فقط
النتيجة: جميع التقارير تعمل!
```

---

**حمّل الآن وثبّت! بعدها كل شيء سيعمل!** 🚀

**رابط التحميل:**
https://wkhtmltopdf.org/downloads.html



