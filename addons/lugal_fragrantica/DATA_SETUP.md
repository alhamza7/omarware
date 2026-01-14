# ⚠️ إعداد البيانات - Fragrantica Module

**مهم:** ملفات البيانات والصور **غير مُضمنة** في Git (حجمها ~3 GB)

---

## 📦 ما تحتاجه

بعد clone المشروع، تحتاج لنقل البيانات يدوياً:

### الملفات المطلوبة:
- `perfumes.db` - قاعدة البيانات (~50 MB)
- `images/` - مجلد الصور (~3 GB)
  - `perfumes/` - 37,600+ صورة عطر
  - `brands/` - 4,500+ شعار براند
  - `notes/` - 1,600+ صورة نوتة

---

## 🚀 طريقتان للإعداد

### ✅ الطريقة 1: نقل مجلد fregran كاملاً (الأسهل)

**على السيرفر:**

```bash
# 1. نقل مجلد fregran من الجهاز الأصلي
scp -r /path/to/fregran user@server:/opt/odoo/

# 2. تعيين الصلاحيات
sudo chown -R odoo:odoo /opt/odoo/fregran
sudo chmod -R 755 /opt/odoo/fregran
```

**المودول سيبحث تلقائياً في:**
- `/opt/odoo/fregran/perfumes.db`
- `/opt/odoo/fregran/static/images/`

✨ **لا حاجة لخطوات إضافية!**

📖 **راجع:** `INSTALLATION_DIRECT_FREGRAN.md`

---

### الطريقة 2: استخدام مجلد التصدير

**على جهازك المحلي:**

```bash
# 1. جهّز البيانات
cd fragrantica_data_export
python3 prepare_export.py  # أو START_PREPARE_EXPORT.bat

# 2. انقل للسيرفر
scp -r . user@server:/tmp/fragrantica_export/
```

**على السيرفر:**

```bash
# 3. انسخ للمكان الصحيح
cd /opt/odoo/addons/lugal_fragrantica/static
sudo mkdir -p fragrantica_data/images

sudo cp /tmp/fragrantica_export/perfumes.db fragrantica_data/
sudo cp -r /tmp/fragrantica_export/images/* fragrantica_data/images/

sudo chown -R odoo:odoo fragrantica_data/
```

📖 **راجع:** `INSTALLATION_AR.md`

---

## 🔍 التحقق من الإعداد

### تأكد من وجود البيانات:

```bash
# الطريقة 1: fregran
ls -lh /opt/odoo/fregran/perfumes.db
ls /opt/odoo/fregran/static/images/perfumes/ | head

# الطريقة 2: fragrantica_data
ls -lh static/fragrantica_data/perfumes.db
ls static/fragrantica_data/images/perfumes/ | head
```

---

## ✅ الخطوات التالية

بعد نقل البيانات:

1. **تثبيت المودول:**
   - Apps → ابحث "Fragrantica" → Install

2. **استيراد البيانات:**
   - Fragrantica → Configuration → Import Data
   - Start Import

3. **الاستخدام:**
   - افتح أي منتج → تاب Fragrantica
   - ابحث عن عطر → اربطه

---

## 📚 الدلائل الكاملة

- **البدء السريع (طريقة fregran):** `/QUICK_START_DIRECT_FREGRAN.md`
- **التثبيت الكامل (طريقة fregran):** `INSTALLATION_DIRECT_FREGRAN.md`
- **البدء السريع (طريقة التصدير):** `/QUICK_START_FRAGRANTICA.md`
- **التثبيت الكامل (طريقة التصدير):** `INSTALLATION_AR.md`

---

## 💡 نصيحة

**الطريقة 1** (نقل fregran) أسهل وأسرع - **موصى بها!**

لا تنسَ: البيانات **ضخمة** (~3 GB) - النقل قد يستغرق وقتاً طويلاً على الإنترنت البطيء.






