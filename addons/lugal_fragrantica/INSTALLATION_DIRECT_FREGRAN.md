# 🚀 التثبيت المباشر - نقل مجلد fregran كاملاً

دليل تثبيت مبسّط عند نقل مجلد `fregran` بالكامل للسيرفر

---

## 📋 نظرة عامة

هذا الدليل للحالة التي تنقل فيها مجلد `fregran` **بالكامل** إلى السيرفر بدلاً من تصدير البيانات فقط.

**المميزات:**
- ✅ أسهل وأسرع
- ✅ لا حاجة لـ `prepare_export.py`
- ✅ البنية كاملة كما هي
- ✅ يمكن استخدام السكريبتات الموجودة في fregran

---

## 🎯 الخطوات السريعة

### 1️⃣ نقل المجلد للسيرفر

#### من جهازك (Git Bash):

```bash
cd D:/capo_dev/Lugal-ai

# نقل المجلد بالكامل
scp -r fregran/ user@server:/opt/odoo/

# أو باستخدام rsync (أفضل للملفات الكثيرة)
rsync -avz --progress fregran/ user@server:/opt/odoo/fregran/
```

**الوقت المتوقع:** 30 دقيقة - 2 ساعة (حسب سرعة الإنترنت)

**الحجم:** ~3 GB

---

### 2️⃣ على السيرفر - تهيئة المسارات

اختر **أحد الخيارات** التالية:

#### ✅ الخيار أ: Symlink (موصى به)

```bash
ssh user@server

# تعيين الصلاحيات
sudo chown -R odoo:odoo /opt/odoo/fregran
sudo chmod -R 755 /opt/odoo/fregran

# إنشاء المجلد المطلوب
cd /opt/odoo/addons/lugal_fragrantica/static
sudo mkdir -p fragrantica_data/images

# ربط قاعدة البيانات
sudo ln -s /opt/odoo/fregran/perfumes.db fragrantica_data/perfumes.db

# ربط الصور
sudo ln -s /opt/odoo/fregran/static/images/perfumes fragrantica_data/images/perfumes
sudo ln -s /opt/odoo/fregran/static/images/brands fragrantica_data/images/brands
sudo ln -s /opt/odoo/fregran/static/images/notes fragrantica_data/images/notes

# تعيين الصلاحيات
sudo chown -R odoo:odoo fragrantica_data/
```

**المميزات:**
- توفير المساحة (لا نسخ مكرر)
- سهولة التحديث
- الملفات الأصلية في مكان واحد

#### الخيار ب: النسخ المباشر

```bash
ssh user@server

# إنشاء المجلد
cd /opt/odoo/addons/lugal_fragrantica/static
sudo mkdir -p fragrantica_data/images

# نسخ قاعدة البيانات
sudo cp /opt/odoo/fregran/perfumes.db fragrantica_data/

# نسخ الصور
sudo cp -r /opt/odoo/fregran/static/images/* fragrantica_data/images/

# تعيين الصلاحيات
sudo chown -R odoo:odoo fragrantica_data/
sudo chmod -R 755 fragrantica_data/
```

**المميزات:**
- مستقل تماماً
- لا يتأثر بحذف fregran

#### الخيار ج: استخدام fregran مباشرة (بدون نقل)

```bash
ssh user@server

# فقط تعيين الصلاحيات
sudo chown -R odoo:odoo /opt/odoo/fregran
sudo chmod -R 755 /opt/odoo/fregran

# المودول معدّل ليبحث في /opt/odoo/fregran تلقائياً
```

**المميزات:**
- أسهل طريقة
- المودول **محدّث** ليدعم هذا المسار تلقائياً

---

### 3️⃣ التحقق من البنية

بعد أي خيار، تحقق من:

```bash
# التحقق من قاعدة البيانات
ls -lh /opt/odoo/addons/lugal_fragrantica/static/fragrantica_data/perfumes.db
# أو
ls -lh /opt/odoo/fregran/perfumes.db

# التحقق من الصور
ls /opt/odoo/addons/lugal_fragrantica/static/fragrantica_data/images/perfumes/ | head
# أو
ls /opt/odoo/fregran/static/images/perfumes/ | head
```

---

### 4️⃣ تثبيت المودول في Odoo

```bash
# إعادة تشغيل Odoo
sudo systemctl restart odoo
```

**في Odoo:**
1. Apps → Update Apps List → Update
2. ابحث: "Fragrantica"
3. اضغط: **Install**

---

### 5️⃣ استيراد البيانات

**في Odoo:**

1. اذهب إلى: **Fragrantica → Configuration → Import Data**

2. **اترك حقل Database Path فارغاً** - المودول سيجد القاعدة تلقائياً

3. الإعدادات:
   - ✅ Import Images: **مفعّل**
   - Batch Size: `500` (أو `100` للسيرفرات البطيئة)

4. اضغط: **Start Import**

5. انتظر 10-20 دقيقة

6. عند الانتهاء → **Close**

---

## ✅ التحقق من النجاح

### اختبر المودول:

```
1. Sales → Products → Products
2. افتح أي منتج
3. تاب "Fragrantica"
4. ابحث: "Dior" أو "ديور"
5. اختر عطراً
6. احفظ
7. ✓ هل ظهرت كل المعلومات والصور؟
```

### إذا كان الجواب نعم:
🎉 **تهانينا! التثبيت نجح!**

### إذا كان الجواب لا:
راجع قسم "حل المشاكل" أدناه ⬇️

---

## 🐛 حل المشاكل

### ❌ المشكلة: "Database file not found"

**السبب:** المودول لم يجد `perfumes.db`

**الحل:**

```bash
# تحقق من المسارات التي يبحث فيها المودول:
ls -l /opt/odoo/addons/lugal_fragrantica/static/fragrantica_data/perfumes.db
ls -l /opt/odoo/addons/lugal_fragrantica/static/fregran/perfumes.db
ls -l /opt/odoo/fregran/perfumes.db

# واحد منهم على الأقل يجب أن يكون موجوداً
```

**إذا لم يكن موجوداً:**
```bash
# أنشئ symlink
sudo ln -s /opt/odoo/fregran/perfumes.db \
  /opt/odoo/addons/lugal_fragrantica/static/fragrantica_data/perfumes.db
```

---

### ❌ المشكلة: الصور لا تظهر

**الحل 1 - تحقق من المسارات:**

```bash
# تحقق من وجود الصور
ls /opt/odoo/fregran/static/images/perfumes/ | head -5

# إنشاء symlinks
cd /opt/odoo/addons/lugal_fragrantica/static
sudo mkdir -p fragrantica_data/images
sudo ln -s /opt/odoo/fregran/static/images/perfumes fragrantica_data/images/perfumes
sudo ln -s /opt/odoo/fregran/static/images/brands fragrantica_data/images/brands
sudo ln -s /opt/odoo/fregran/static/images/notes fragrantica_data/images/notes
```

**الحل 2 - تحميل الصور من Odoo:**

في Odoo → Settings → Technical → Python Code:

```python
# تحميل صور العطور
perfumes = env['fragrantica.perfume'].search([('image', '=', False)], limit=100)
perfumes.load_image_from_static()

# تحميل صور النوتات
notes = env['fragrantica.note'].search([('note_image', '=', False)], limit=1000)
notes.load_image_from_static()
```

---

### ❌ المشكلة: Permission denied

**الحل:**

```bash
# إصلاح الصلاحيات
sudo chown -R odoo:odoo /opt/odoo/fregran
sudo chown -R odoo:odoo /opt/odoo/addons/lugal_fragrantica/static/
sudo chmod -R 755 /opt/odoo/fregran
sudo chmod -R 755 /opt/odoo/addons/lugal_fragrantica/static/
```

---

### ❌ المشكلة: الاستيراد بطيء جداً

**الحل:**

1. في wizard الاستيراد، قلل **Batch Size** إلى `100`
2. تأكد من RAM كافية:
   ```bash
   free -h
   ```
3. أوقف خدمات غير ضرورية مؤقتاً

---

## 🔄 التحديث لاحقاً

### عند إضافة عطور جديدة:

#### 1. على جهازك المحلي:
```bash
# استخدم سكريبتات fregran لجلب عطور جديدة
cd D:/capo_dev/Lugal-ai/fregran
# شغّل سكريبت الـ scraping...
```

#### 2. نقل قاعدة البيانات المحدثة فقط:
```bash
scp perfumes.db user@server:/tmp/perfumes_new.db
```

#### 3. على السيرفر:
```bash
# استبدل القاعدة القديمة
sudo cp /tmp/perfumes_new.db /opt/odoo/fregran/perfumes.db
sudo chown odoo:odoo /opt/odoo/fregran/perfumes.db
```

#### 4. في Odoo:
- أعد تشغيل Import Data wizard
- العطور الجديدة ستُضاف تلقائياً

---

## 💡 نصائح Pro

### استخدام سكريبتات fregran مباشرة على السيرفر:

إذا كان لديك Python على السيرفر:

```bash
# تثبيت المتطلبات
cd /opt/odoo/fregran
pip3 install -r requirements.txt

# تشغيل Flask gallery (اختياري)
python3 app.py

# تشغيل scraping (عند الحاجة)
python3 scrapingbee_auto.py
```

### Symlinks vs Copy:

| الميزة | Symlink | Copy |
|--------|---------|------|
| المساحة | ✅ توفير | ❌ مكرر |
| السرعة | ✅ فوري | ❌ بطيء |
| التحديث | ✅ تلقائي | ❌ يدوي |
| الاستقلالية | ❌ يعتمد على fregran | ✅ مستقل |

**التوصية:** استخدم **Symlink** إلا إذا كنت تريد حذف `fregran` لاحقاً.

---

## 📊 المسارات المدعومة

المودول **محدّث** ليبحث تلقائياً في:

### لقاعدة البيانات:
1. `addons/lugal_fragrantica/static/fragrantica_data/perfumes.db`
2. `addons/lugal_fragrantica/static/fregran/perfumes.db`
3. `/opt/odoo/fregran/perfumes.db` ✨ **جديد**

### للصور:
1. `addons/lugal_fragrantica/static/fragrantica_data/images/`
2. `addons/lugal_fragrantica/static/fregran/static/images/`
3. `/opt/odoo/fregran/static/images/` ✨ **جديد**

**يعني:** ضع `fregran` في أي مسار من الثلاثة وسيعمل! 🎉

---

## ✅ Checklist التثبيت

- [ ] نقل مجلد `fregran` للسيرفر (`/opt/odoo/fregran/`)
- [ ] تعيين الصلاحيات (`chown odoo:odoo`)
- [ ] إنشاء symlinks أو نسخ البيانات
- [ ] إعادة تشغيل Odoo
- [ ] تثبيت المودول من Apps
- [ ] استيراد البيانات (Import Data wizard)
- [ ] اختبار في منتج (تاب Fragrantica)
- [ ] تحميل الصور (إذا لم تظهر)

---

## 📞 المساعدة

- **للتفاصيل الكاملة:** `INSTALLATION_AR.md`
- **للبدء السريع:** `QUICK_START_FRAGRANTICA.md`
- **للـ Scraping:** `SCRAPING_GUIDE_AR.md`

---

**🎉 استمتع باستخدام Fragrantica مع طريقة التثبيت المباشرة!**

هذه الطريقة **أسهل وأسرع** من التصدير اليدوي، وتتيح لك استخدام كل إمكانيات `fregran` على السيرفر!



