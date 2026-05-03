# 🔧 حل متقدم: مشكلة الترميز العربي المستمرة

**الحالة:** تم تثبيت الخطوط لكن المشكلة باقية  
**التاريخ:** 2026-01-11

---

## 🔍 تشخيص المشكلة

من الصورة، يتضح أن:
- ✅ الاتجاه صحيح (RTL)
- ✅ اللوجو يظهر
- ✅ رقم SAP صحيح (2600008)
- ✅ الأرقام نظيفة (78,000)
- ❌ **الترميز ما زال خاطئاً** ← المشكلة الوحيدة الباقية

---

## 🚀 الحلول المتقدمة

### الحل 1: مسح ذاكرة wkhtmltopdf وإعادة تشغيل كاملة

```bash
# على الخادم (192.168.116.211):

# 1. مسح ذاكرة wkhtmltopdf
sudo rm -rf /tmp/wkhtmlto*

# 2. مسح ذاكرة Odoo
sudo rm -rf /var/lib/odoo/.local/share/Odoo/filestore/*/.report_cache 2>/dev/null

# 3. إعادة تشغيل كاملة
sudo systemctl stop odoo
sleep 3
sudo systemctl start odoo

# 4. التحقق من الخدمة
sudo systemctl status odoo
```

---

### الحل 2: تحديث wkhtmltopdf لنسخة أحدث

النسخة القديمة من wkhtmltopdf قد لا تدعم UTF-8 بشكل جيد.

```bash
# التحقق من الإصدار الحالي
wkhtmltopdf --version

# إذا كان أقل من 0.12.6، قم بالتحديث:

# 1. تنزيل النسخة الأحدث
cd /tmp
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb

# 2. تثبيت
sudo dpkg -i wkhtmltox_0.12.6.1-2.jammy_amd64.deb

# 3. إصلاح dependencies
sudo apt-get install -f

# 4. التحقق
wkhtmltopdf --version

# 5. إعادة تشغيل Odoo
sudo systemctl restart odoo
```

---

### الحل 3: تحديد الخط بشكل صريح في wkhtmltopdf

أضف هذه الإعدادات في `/etc/odoo/odoo.conf`:

```bash
sudo nano /etc/odoo/odoo.conf
```

أضف أو عدّل:

```ini
[options]
; PDF Report settings
report_dpi = 96
```

احفظ وأعد التشغيل:

```bash
sudo systemctl restart odoo
```

---

### الحل 4: التحقق من locale على الخادم

```bash
# التحقق من locale الحالي
locale

# إذا لم يكن يدعم UTF-8، قم بتفعيله:
sudo locale-gen en_US.UTF-8
sudo locale-gen ar_IQ.UTF-8
sudo update-locale LANG=en_US.UTF-8

# إعادة التشغيل
sudo systemctl restart odoo
```

---

### الحل 5: التحقق من صلاحيات الخطوط

```bash
# التأكد من أن الخطوط قابلة للقراءة
sudo chmod -R 755 /usr/share/fonts/truetype/dejavu/

# تحديث ذاكرة الخطوط
sudo fc-cache -f -v

# التحقق من توفر الخطوط
fc-list | grep -i dejavu | head -10

# يجب أن ترى:
# DejaVu Sans
# DejaVu Sans Mono
# DejaVu Serif
```

---

### الحل 6: استخدام خط مختلف في التقرير

إذا لم تعمل DejaVu Sans، جرّب خطوط أخرى.

سأقوم بتحديث التقرير ليستخدم خيارات خطوط متعددة:

---

## 🔍 خطوات التشخيص

نفذ هذه الأوامر على الخادم وأرسل لي النتائج:

```bash
# 1. الخطوط المثبتة
echo "=== Installed Fonts ==="
fc-list | grep -i dejavu

# 2. الخطوط العربية
echo "=== Arabic Fonts ==="
fc-list :lang=ar | head -5

# 3. إصدار wkhtmltopdf
echo "=== wkhtmltopdf Version ==="
wkhtmltopdf --version

# 4. Locale
echo "=== Locale ==="
locale | grep -i utf

# 5. حالة Odoo
echo "=== Odoo Status ==="
sudo systemctl status odoo | grep -i active
```

---

## 💡 الحل المقترح التالي

بناءً على الصورة، المشكلة تبدو كأنها من wkhtmltopdf نفسه.

### جرّب هذا الترتيب:

```bash
# 1. مسح كل الذاكرة المؤقتة
sudo rm -rf /tmp/wkhtmlto*
sudo rm -rf /tmp/wktemp*

# 2. إعادة بناء ذاكرة الخطوط
sudo fc-cache -f -v

# 3. إعادة تشغيل كاملة (مع مسح العمليات)
sudo systemctl stop odoo
sudo pkill -9 -f odoo
sleep 5
sudo systemctl start odoo

# 4. التحقق
sudo tail -f /var/log/odoo/odoo.log
```

---

## 🎯 خطة بديلة: استخدام HTML بدلاً من PDF

إذا لم تنجح جميع الحلول، يمكننا:

1. تغيير التقرير ليكون HTML بدلاً من PDF
2. HTML يعرض العربية دائماً بشكل صحيح
3. يمكن الطباعة من المتصفح (Ctrl+P)

**هل تريد هذا الحل؟**

---

## 📊 الاحتمالات

| السبب المحتمل | الحل |
|---|---|
| wkhtmltopdf قديم | تحديثه للنسخة 0.12.6 |
| ذاكرة مؤقتة | مسح /tmp/wkhtmlto* |
| locale خاطئ | تفعيل UTF-8 |
| صلاحيات الخطوط | chmod 755 |
| Odoo cache | إعادة تشغيل كاملة |

---

## 🆘 ماذا الآن؟

### الخيار أ: أرسل لي نتائج التشخيص
نفذ أوامر التشخيص أعلاه وأرسل النتائج

### الخيار ب: جرّب الحل المتقدم
نفذ أوامر "الحل المقترح" أعلاه

### الخيار ج: حل بديل (HTML)
سأحوّل التقرير ل HTML (يعمل 100%)

---

**ما هو الخيار الذي تفضله؟** 🤔

