# 📦 Fragrantica Data Export

مجلد تصدير بيانات Fragrantica للنقل إلى السيرفر

---

## 📋 المحتويات

بعد تشغيل `prepare_export.py`، سيحتوي هذا المجلد على:

```
fragrantica_data_export/
├── perfumes.db          # قاعدة بيانات SQLite (~50 MB)
├── images/              # مجلد الصور (~2-3 GB)
│   ├── perfumes/        # صور العطور (37,600+ صورة)
│   ├── brands/          # شعارات البراندات (4,500+ صورة)
│   └── notes/           # صور النوتات (1,600+ صورة)
├── prepare_export.py    # سكريبت التجهيز
├── START_PREPARE_EXPORT.bat  # لتشغيل السكريبت (Windows)
└── README.md            # هذا الملف
```

---

## 🚀 الاستخدام

### 1️⃣ تجهيز البيانات

#### على Windows:
- شغّل ملف `START_PREPARE_EXPORT.bat`

#### على Linux/Mac:
```bash
python3 prepare_export.py
```

### 2️⃣ نقل البيانات للسيرفر

```bash
# نسخ المجلد بالكامل للسيرفر
scp -r fragrantica_data_export/ user@server:/tmp/

# أو باستخدام rsync (أسرع)
rsync -avz --progress fragrantica_data_export/ user@server:/tmp/fragrantica_export/
```

### 3️⃣ على السيرفر

```bash
# الانتقال لمجلد المودول
cd /opt/odoo/addons/lugal_fragrantica

# إنشاء مجلد البيانات
sudo mkdir -p static/fragrantica_data

# نسخ قاعدة البيانات
sudo cp /tmp/fragrantica_export/perfumes.db static/fragrantica_data/

# نسخ الصور
sudo cp -r /tmp/fragrantica_export/images static/fragrantica_data/

# تعيين الصلاحيات
sudo chown -R odoo:odoo static/fragrantica_data
sudo chmod -R 755 static/fragrantica_data
```

---

## 📊 معلومات البيانات

### قاعدة البيانات (perfumes.db)

- **الجداول:**
  - `perfumes` - 49,000+ عطر
  - `notes` - 150,000+ نوتة عطرية
  - `main_accords` - 100,000+ توافق رئيسي

- **الحجم:** ~50 MB

- **الحقول المهمة:**
  ```
  perfumes:
    - id, url, name, arabic_name
    - brand_name, brand_logo_url
    - image_url, description_full
    - year
  
  notes:
    - perfume_id, note_type (Top/Middle/Base)
    - note_name, note_image_url
    - note_opacity, note_order
  
  main_accords:
    - perfume_id, accord_name
    - accord_width, accord_color
    - accord_order
  ```

### الصور (images/)

- **perfumes/** - 37,600+ ملف
  - تنسيق: `{perfume_id}.jpg`
  - أبعاد: متنوعة (عادة 300x300 إلى 600x600)
  - الحجم: ~1.5-2 GB

- **brands/** - 4,500+ ملف
  - تنسيق: `{brand-name}.jpg`
  - أبعاد: متنوعة (شعارات)
  - الحجم: ~200-300 MB

- **notes/** - 1,600+ ملف
  - تنسيق: `{note-name}.jpg`
  - أبعاد: متنوعة (رموز)
  - الحجم: ~100-200 MB

---

## 🔍 التحقق من البيانات

### التحقق من قاعدة البيانات:

```bash
# التحقق من حجم الملف
ls -lh perfumes.db

# فتح قاعدة البيانات (يتطلب sqlite3)
sqlite3 perfumes.db "SELECT COUNT(*) FROM perfumes;"
```

### التحقق من الصور:

```bash
# عد ملفات الصور
find images/ -type f -name "*.jpg" | wc -l

# حساب الحجم الكلي
du -sh images/
```

---

## ⚡ نصائح للنقل السريع

### 1. ضغط البيانات قبل النقل

```bash
# ضغط المجلد
tar -czf fragrantica_data.tar.gz perfumes.db images/

# نقل الملف المضغوط
scp fragrantica_data.tar.gz user@server:/tmp/

# على السيرفر: فك الضغط
cd /tmp
tar -xzf fragrantica_data.tar.gz
```

### 2. نقل على دفعات (للإنترنت البطيء)

```bash
# نقل قاعدة البيانات أولاً (صغيرة)
scp perfumes.db user@server:/tmp/

# نقل كل مجلد صور على حدة
scp -r images/perfumes/ user@server:/tmp/images/
scp -r images/brands/ user@server:/tmp/images/
scp -r images/notes/ user@server:/tmp/images/
```

### 3. استخدام rsync (أفضل لإعادة النقل)

```bash
# rsync يتجاهل الملفات الموجودة مسبقاً
rsync -avz --progress \
  fragrantica_data_export/ \
  user@server:/tmp/fragrantica_export/
```

---

## 🐛 حل المشاكل

### المشكلة: "No space left on device"

**الحل:**
- تحقق من المساحة المتاحة:
  ```bash
  df -h
  ```
- احذف ملفات غير ضرورية أو استخدم قرص أكبر

### المشكلة: النقل بطيء جداً

**الحل:**
- استخدم الضغط (راجع "نصائح للنقل السريع")
- أو استخدم خدمة سحابية (Google Drive, Dropbox)
- أو انقل USB/قرص خارجي إذا كان السيرفر محلياً

### المشكلة: بعض الصور ناقصة

**الحل:**
- أعد تشغيل `prepare_export.py`
- تحقق من أن مجلد `fregran/static/images/` كامل

---

## 📞 الدعم

للمزيد من المساعدة:
- راجع `addons/lugal_fragrantica/README.md`
- راجع `addons/lugal_fragrantica/INSTALLATION_AR.md`

---

**🎯 الهدف:** نقل هذه البيانات للسيرفر واستيرادها في Odoo لبناء قاعدة بيانات شاملة للعطور!




