# ⚡ دليل البدء السريع - نقل fregran مباشرة

**الطريقة الأسهل!** 🚀 نقل مجلد `fregran` كاملاً بدون تصدير

---

## 🎯 الخطوات (3 فقط!)

### 1️⃣ نقل المجلد للسيرفر

**من جهازك (Git Bash):**

```bash
cd D:/capo_dev/Lugal-ai

# نقل fregran بالكامل
scp -r fregran/ user@server:/opt/odoo/

# أو استخدم rsync
rsync -avz --progress fregran/ user@server:/opt/odoo/fregran/
```

⏱️ **الوقت:** 30 دقيقة - ساعتين (حسب الإنترنت)
💾 **الحجم:** ~3 GB

---

### 2️⃣ على السيرفر - تهيئة بسيطة

```bash
ssh user@server

# تعيين الصلاحيات فقط!
sudo chown -R odoo:odoo /opt/odoo/fregran
sudo chmod -R 755 /opt/odoo/fregran

# تثبيت Odoo
sudo systemctl restart odoo
```

✨ **ملاحظة:** المودول **محدّث** ليبحث في `/opt/odoo/fregran/` تلقائياً!

---

### 3️⃣ تثبيت واستيراد في Odoo

**في Odoo:**

```
1. Apps → ابحث "Fragrantica" → Install

2. Fragrantica → Configuration → Import Data
   - اترك Database Path فارغاً
   - ✅ Import Images
   - Start Import
   - انتظر 10-20 دقيقة
```

---

## 🎉 جاهز!

**اختبر:**
```
Sales → Products → أي منتج → تاب "Fragrantica"
ابحث: "Dior" → اختر عطر → احفظ
→ كل المعلومات والصور ظهرت! ✓
```

---

## 🔧 إذا واجهت مشاكل

### الصور لا تظهر؟

```bash
# أنشئ symlinks
cd /opt/odoo/addons/lugal_fragrantica/static
sudo mkdir -p fragrantica_data/images
sudo ln -s /opt/odoo/fregran/perfumes.db fragrantica_data/
sudo ln -s /opt/odoo/fregran/static/images/perfumes fragrantica_data/images/
sudo ln -s /opt/odoo/fregran/static/images/brands fragrantica_data/images/
sudo ln -s /opt/odoo/fregran/static/images/notes fragrantica_data/images/
sudo chown -R odoo:odoo fragrantica_data/
```

### Database not found؟

المودول يبحث في:
- ✅ `/opt/odoo/fregran/perfumes.db`
- ✅ `addons/lugal_fragrantica/static/fregran/perfumes.db`
- ✅ `addons/lugal_fragrantica/static/fragrantica_data/perfumes.db`

تأكد من وجود الملف في أحدها!

---

## 💡 المميزات

مقارنة بطريقة التصدير:

| الميزة | نقل مباشر | التصدير |
|--------|-----------|---------|
| السرعة | ✅ أسرع | ❌ بطيء |
| الخطوات | 3 خطوات | 5 خطوات |
| تجهيز محلي | لا يحتاج | يحتاج |
| استخدام سكريبتات fregran | ✅ نعم | ❌ لا |
| التحديث | ✅ سهل | ❌ معقد |

**التوصية:** ✨ **استخدم هذه الطريقة!**

---

## 📚 للمزيد

- **تفاصيل كاملة:** `addons/lugal_fragrantica/INSTALLATION_DIRECT_FREGRAN.md`
- **حل المشاكل:** نفس الملف أعلاه
- **Scraping:** `addons/lugal_fragrantica/SCRAPING_GUIDE_AR.md`

---

**🚀 استمتع! الطريقة الأسهل والأسرع لتشغيل Fragrantica!**










