# ⚡ دليل البدء السريع - Fragrantica Module

دليل سريع لتشغيل مودول Fragrantica في 4 خطوات! 🚀

---

## ✅ ما تحتاجه

- ✅ Odoo 14+ مثبت
- ✅ مجلد `fregran` يحتوي على قاعدة البيانات والصور
- ✅ اتصال بالسيرفر (SSH/FTP)
- ✅ 5 GB مساحة على السيرفر

---

## 📝 الخطوات (4 فقط!)

### 1️⃣ تجهيز البيانات (5 دقائق)

**على جهازك (Windows):**

```
1. افتح مجلد: fragrantica_data_export
2. شغّل: START_PREPARE_EXPORT.bat
3. انتظر حتى ينتهي (سينسخ 50 MB + 3 GB صور)
```

**النتيجة:** سيتم إنشاء `perfumes.db` و `images/`

---

### 2️⃣ نقل البيانات للسيرفر (10 دقائق - ساعتين حسب الإنترنت)

**من جهازك:**

```bash
# افتح Git Bash أو PowerShell
cd D:/capo_dev/Lugal-ai/fragrantica_data_export

# انقل للسيرفر (استبدل user وserver بمعلوماتك)
scp -r . user@server:/tmp/fragrantica_export/
```

**على السيرفر:**

```bash
ssh user@server

# انسخ للمكان الصحيح
cd /opt/odoo/addons/lugal_fragrantica
sudo mkdir -p static/fragrantica_data
sudo cp /tmp/fragrantica_export/perfumes.db static/fragrantica_data/
sudo cp -r /tmp/fragrantica_export/images static/fragrantica_data/
sudo chown -R odoo:odoo static/fragrantica_data
```

---

### 3️⃣ تثبيت المودول (2 دقيقة)

**في Odoo:**

```
1. إعادة تشغيل Odoo:
   sudo systemctl restart odoo

2. في Odoo → Apps
3. ابحث: "Fragrantica"
4. اضغط: Install
```

---

### 4️⃣ استيراد البيانات (15 دقيقة)

**في Odoo:**

```
1. اذهب إلى: Fragrantica → Configuration → Import Data
2. اترك كل الإعدادات كما هي
3. فعّل: ✅ Import Images
4. اضغط: Start Import
5. انتظر... (سيستغرق 10-20 دقيقة)
6. عند الانتهاء اضغط: Close
```

---

## 🎉 جاهز!

الآن:

### اختبر المودول:

```
1. اذهب: Sales → Products → Products
2. افتح أي منتج
3. ستجد تاب جديد: "Fragrantica"
4. في حقل "Fragrantica Perfume"، ابحث: "Dior" أو "ديور"
5. اختر عطراً
6. احفظ
7. 🎊 كل معلومات العطر ظهرت!
```

---

## 📚 للمزيد من التفاصيل

- **التثبيت الكامل:** `addons/lugal_fragrantica/INSTALLATION_AR.md`
- **الوثائق التقنية:** `addons/lugal_fragrantica/README.md`
- **Scraping عطور جديدة:** `addons/lugal_fragrantica/SCRAPING_GUIDE_AR.md`
- **ملخص شامل:** `FRAGRANTICA_MODULE_SUMMARY.md`

---

## 🆘 مشاكل شائعة

### "Database file not found"
```bash
# تأكد من وجود الملف
ls /opt/odoo/addons/lugal_fragrantica/static/fragrantica_data/perfumes.db
```

### الصور لا تظهر
```bash
# تأكد من الصلاحيات
sudo chown -R odoo:odoo /opt/odoo/addons/lugal_fragrantica/static/
```

### الاستيراد بطيء
- قلل Batch Size إلى 100 في wizard الاستيراد

---

## 🎯 الاستخدام اليومي

### ربط منتج بعطر:
```
1. افتح المنتج
2. تاب "Fragrantica"
3. ابحث عن العطر
4. اختر
5. احفظ → تلقائياً تظهر كل المعلومات!
```

### تعديل المعلومات:
```
1. في تاب Fragrantica
2. فعّل: ✅ Use Custom Data
3. عدّل ما تريد
4. احفظ
```

### طلب عطر جديد:
```
1. إذا لم تجد العطر
2. الصق رابط Fragrantica في حقل "Fragrantica URL (Pending)"
3. اضغط: Create Request
4. سيتم إضافته لاحقاً
```

---

## ✨ نصائح Pro

- 💡 البحث يعمل بالعربي والإنجليزي
- 💡 يمكن البحث بالبراند أو اسم العطر
- 💡 الصور عالية الجودة تلقائياً
- 💡 النوتات والتوافقات قابلة للتعديل
- 💡 كل المعلومات محفوظة في Odoo

---

## 📊 الإحصائيات

**ما لديك الآن:**
- 🌟 49,000+ عطر
- 🎨 150,000+ نوتة عطرية
- 🎯 100,000+ توافق رئيسي
- 🖼️ 43,000+ صورة

---

**استمتع باستخدام Fragrantica Module! 🎊**

للدعم، راجع الوثائق الكاملة في `addons/lugal_fragrantica/`








