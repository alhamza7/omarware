# 📘 دليل التثبيت والاستخدام - مودول Fragrantica

---

## 📑 جدول المحتويات

1. [نظرة عامة](#نظرة-عامة)
2. [المتطلبات](#المتطلبات)
3. [خطوات التثبيت](#خطوات-التثبيت)
4. [تجهيز البيانات](#تجهيز-البيانات)
5. [نقل البيانات للسيرفر](#نقل-البيانات-للسيرفر)
6. [استيراد البيانات في Odoo](#استيراد-البيانات-في-odoo)
7. [الاستخدام اليومي](#الاستخدام-اليومي)
8. [حل المشاكل](#حل-المشاكل)

---

## 🎯 نظرة عامة

مودول **Fragrantica Integration** يتيح لك:

- ربط منتجات العطور في Odoo مع قاعدة بيانات شاملة من **Fragrantica**
- عرض معلومات تفصيلية عن كل عطر (نوتات، توافقات، وصف، صور)
- البحث في أكثر من **49,000 عطر** بالعربي والإنجليزي
- تخصيص وتعديل المعلومات حسب احتياجاتك
- طلب إضافة عطور جديدة غير موجودة في القاعدة

---

## 💻 المتطلبات

### على السيرفر:
- Odoo 14.0 أو أحدث
- PostgreSQL
- مساحة قرص: **5 GB** على الأقل
- RAM: **2 GB** على الأقل

### على جهازك المحلي (للتجهيز):
- Python 3.7+
- مجلد `fregran` يحتوي على قاعدة البيانات والصور

---

## 🚀 خطوات التثبيت

### الخطوة 1: نسخ المودول

#### على السيرفر:

```bash
# الانتقال لمجلد addons
cd /opt/odoo/addons/

# نسخ المودول (إذا كان في Git)
git clone <repository_url> lugal_fragrantica

# أو نسخ المجلد يدوياً
scp -r /path/to/lugal_fragrantica user@server:/opt/odoo/addons/
```

### الخطوة 2: تعيين الصلاحيات

```bash
sudo chown -R odoo:odoo /opt/odoo/addons/lugal_fragrantica
sudo chmod -R 755 /opt/odoo/addons/lugal_fragrantica
```

### الخطوة 3: إعادة تشغيل Odoo

```bash
sudo systemctl restart odoo
```

---

## 📦 تجهيز البيانات

هذه الخطوة تتم **على جهازك المحلي** (حيث توجد بيانات `fregran`).

### الطريقة الآلية (موصى بها):

#### على Windows:

1. افتح مجلد `fragrantica_data_export`
2. شغّل ملف `START_PREPARE_EXPORT.bat`
3. انتظر حتى اكتمال النسخ

#### على Linux/Mac:

```bash
cd /path/to/Lugal-ai/fragrantica_data_export
python3 prepare_export.py
```

### النتيجة:

سيتم إنشاء الملفات التالية في `fragrantica_data_export/`:
- ✅ `perfumes.db` - قاعدة البيانات (حوالي 50 MB)
- ✅ `images/` - مجلد الصور (حوالي 2-3 GB)
  - `perfumes/` - صور العطور
  - `brands/` - شعارات البراندات
  - `notes/` - صور النوتات
- ✅ `README.md` - تعليمات التثبيت

---

## 📤 نقل البيانات للسيرفر

### الطريقة 1: استخدام SCP (موصى بها)

```bash
# من جهازك المحلي
cd /path/to/Lugal-ai/fragrantica_data_export

# نقل المجلد كاملاً للسيرفر
scp -r . user@server:/tmp/fragrantica_export/
```

### الطريقة 2: استخدام FTP/SFTP

استخدم FileZilla أو أي برنامج FTP لنقل مجلد `fragrantica_data_export` بالكامل إلى `/tmp/` على السيرفر.

### الطريقة 3: Google Drive / Dropbox (للسيرفرات البعيدة)

1. ارفع المجلد على Google Drive أو Dropbox
2. على السيرفر، حمّله باستخدام `wget` أو `rclone`

---

## 📥 وضع البيانات في المكان الصحيح

**على السيرفر:**

```bash
# الانتقال لمجلد المودول
cd /opt/odoo/addons/lugal_fragrantica

# إنشاء مجلد البيانات
sudo mkdir -p static/fragrantica_data

# نسخ قاعدة البيانات
sudo cp /tmp/fragrantica_export/perfumes.db static/fragrantica_data/

# نسخ مجلد الصور بالكامل
sudo cp -r /tmp/fragrantica_export/images static/fragrantica_data/

# تعيين الصلاحيات
sudo chown -R odoo:odoo static/fragrantica_data
sudo chmod -R 755 static/fragrantica_data
```

### التحقق من النسخ:

```bash
# التحقق من وجود قاعدة البيانات
ls -lh static/fragrantica_data/perfumes.db

# التحقق من مجلدات الصور
ls static/fragrantica_data/images/
# يجب أن ترى: perfumes  brands  notes

# عد الصور (اختياري)
find static/fragrantica_data/images/ -type f | wc -l
# يجب أن يظهر حوالي 43,000+
```

---

## 🔌 تثبيت المودول في Odoo

### 1. تفعيل Developer Mode

1. اذهب إلى **Settings**
2. في الأسفل، اضغط **Activate the developer mode**

### 2. تحديث قائمة Apps

1. اذهب إلى **Apps**
2. اضغط على القائمة (☰) → **Update Apps List**
3. اضغط **Update**

### 3. البحث والتثبيت

1. في **Apps**، ابحث عن: `fragrantica`
2. ستجد **Fragrantica Integration**
3. اضغط **Install**

### 4. انتظر اكتمال التثبيت

قد يستغرق 1-2 دقيقة.

---

## 📊 استيراد البيانات في Odoo

بعد تثبيت المودول:

### الخطوات:

1. **اذهب إلى القائمة:**
   - **Fragrantica** → **Configuration** → **Import Data**

2. **املأ النموذج:**
   - **Database Path**: اتركه **فارغاً** (سيستخدم المسار الافتراضي)
   - **Import Images**: ✅ **فعّل** هذا الخيار
   - **Batch Size**: اترك `500` (أو قلّله إلى `100` إذا كان السيرفر بطيئاً)

3. **ابدأ الاستيراد:**
   - اضغط **Start Import**

4. **انتظر الاستيراد:**
   - سترى شريط تقدم يعرض:
     - عدد العطور المستوردة
     - عدد النوتات المستوردة
     - عدد التوافقات المستوردة
   - **الوقت المتوقع**: 10-20 دقيقة

5. **انتهى!**
   - عند الانتهاء، ستظهر رسالة "Import completed successfully!"
   - اضغط **Close**

---

## 🎨 الاستخدام اليومي

### 1️⃣ ربط منتج بعطر من Fragrantica

#### الخطوات:

1. **افتح صفحة المنتج:**
   - Sales → Products → Products
   - اختر منتجاً موجوداً أو أنشئ منتجاً جديداً

2. **اذهب لتاب Fragrantica:**
   - ستجد تاباً جديداً اسمه **"Fragrantica"**

3. **ابحث عن العطر:**
   - في حقل **"Fragrantica Perfume"**، ابدأ الكتابة
   - يمكنك البحث بـ:
     - الاسم الإنجليزي (مثلاً: "Dior Sauvage")
     - الاسم العربي (مثلاً: "سوفاج ديور")
     - اسم البراند (مثلاً: "Dior")

4. **اختر العطر:**
   - ستظهر نتائج البحث
   - اختر العطر المناسب

5. **احفظ المنتج:**
   - اضغط **Save**

#### النتيجة:

ستظهر **تلقائياً** جميع معلومات العطر:
- ✅ صورة العطر (كبيرة وعالية الجودة)
- ✅ الاسم بالإنجليزي والعربي
- ✅ البراند + شعار البراند
- ✅ سنة الإصدار
- ✅ الوصف الكامل
- ✅ **التوافقات الرئيسية** (Main Accords) مع نسبها
- ✅ **النوتات العطرية**:
  - Top Notes (النوتات العليا)
  - Middle Notes (النوتات الوسطى)
  - Base Notes (النوتات القاعدية)

---

### 2️⃣ تخصيص المعلومات

إذا أردت تعديل أي معلومات:

1. في تاب **Fragrantica**، فعّل خيار:
   ☑️ **Use Custom Data**

2. الآن يمكنك:
   - **تعديل الوصف:** احذف الوصف الحالي واكتب وصفاً جديداً في حقل "Custom Description"
   - **تعديل السنة:** غيّر قيمة "Custom Year"
   - **تعديل النوتات:** في أقسام النوتات، يمكنك إضافة أو حذف نوتات
   - **تعديل التوافقات:** في قسم Accords، يمكنك إضافة أو حذف توافقات

3. احفظ التغييرات

---

### 3️⃣ إضافة عطر غير موجود في القاعدة

إذا لم تجد العطر عند البحث:

1. **احصل على رابط Fragrantica:**
   - اذهب إلى موقع [Fragrantica.com](https://www.fragrantica.com)
   - ابحث عن العطر
   - انسخ الرابط (مثلاً: `https://www.fragrantica.com/perfume/Dior/Sauvage-31861.html`)

2. **في تاب Fragrantica:**
   - الصق الرابط في حقل **"Fragrantica URL (Pending)"**
   - اضغط زر **"Create Request"**

3. **النتيجة:**
   - سيتم إنشاء "طلب معلق" (Pending Request)
   - سيظهر إشعار: "Pending request created"
   - المدير سيرى هذا الطلب في قائمة **Fragrantica → Pending Requests**

4. **لاحقاً:**
   - بعد أن يقوم المدير بجلب بيانات العطر يدوياً وتحديث القاعدة
   - ارجع للمنتج واختر العطر من القائمة

---

### 4️⃣ عرض جميع العطور

لعرض قاعدة البيانات الكاملة:

1. اذهب إلى: **Fragrantica** → **Perfumes**

2. هنا يمكنك:
   - **البحث:** ابحث بأي اسم أو براند
   - **الفلترة:**
     - عطور لها صور فقط: **Has Image**
     - عطور لها اسم عربي: **Has Arabic Name**
   - **التجميع:**
     - حسب البراند: **Group By → Brand**
     - حسب السنة: **Group By → Year**

3. **عرض تفاصيل عطر:**
   - اضغط على أي عطر لرؤية كل التفاصيل
   - يمكنك رؤية المنتجات المربوطة بهذا العطر

---

### 5️⃣ إدارة الطلبات المعلقة

**للمدراء فقط:**

1. اذهب إلى: **Fragrantica** → **Pending Requests**

2. ستظهر قائمة بجميع الطلبات:
   - **Pending**: طلبات جديدة لم يتم معالجتها
   - **Processing**: طلبات قيد المعالجة
   - **Completed**: طلبات مكتملة
   - **Failed**: طلبات فشلت

3. **معالجة الطلبات:**
   - على جهازك المحلي، استخدم سكريبت الـ scraping في `fregran/`
   - أضف العطور المطلوبة لقاعدة البيانات
   - حدّث القاعدة على السيرفر (راجع قسم "التحديث")
   - في Odoo، افتح الطلب واضغط **Mark as Completed**

---

## 🔄 تحديث قاعدة البيانات

لإضافة عطور جديدة أو تحديث البيانات:

### على جهازك المحلي:

1. **جلب بيانات جديدة:**
   - استخدم سكريبت في `fregran/` لجلب العطور الجديدة
   - تأكد من تحديث `fregran/perfumes.db`

2. **تجهيز التصدير مرة أخرى:**
   ```bash
   cd fragrantica_data_export
   python3 prepare_export.py
   ```

3. **نقل للسيرفر:**
   ```bash
   scp perfumes.db user@server:/tmp/perfumes_new.db
   ```

### على السيرفر:

1. **نسخ قاعدة البيانات الجديدة:**
   ```bash
   sudo cp /tmp/perfumes_new.db /opt/odoo/addons/lugal_fragrantica/static/fragrantica_data/perfumes.db
   ```

2. **في Odoo - خيار 1 (استيراد إضافي):**
   - اذهب لـ **Import Data**
   - شغّل الاستيراد مرة أخرى
   - العطور الجديدة ستُضاف تلقائياً (بفضل constraint على fragrantica_id)

3. **خيار 2 (إعادة استيراد كاملة):**
   - احذف البيانات القديمة أولاً:
   ```python
   # في Odoo → Settings → Technical → Python Code
   env['fragrantica.perfume'].search([]).unlink()
   ```
   - ثم شغّل الاستيراد من جديد

---

## 🐛 حل المشاكل

### ❌ المشكلة: "Database file not found"

**السبب:** قاعدة البيانات غير موجودة في المكان الصحيح.

**الحل:**
```bash
# تحقق من وجود الملف
ls -la /opt/odoo/addons/lugal_fragrantica/static/fragrantica_data/perfumes.db

# إذا لم يكن موجوداً، انسخه:
sudo cp /tmp/fragrantica_export/perfumes.db /opt/odoo/addons/lugal_fragrantica/static/fragrantica_data/
sudo chown odoo:odoo /opt/odoo/addons/lugal_fragrantica/static/fragrantica_data/perfumes.db
```

---

### ❌ المشكلة: الصور لا تظهر

**الحل 1 - التحقق من وجود الصور:**
```bash
ls /opt/odoo/addons/lugal_fragrantica/static/fragrantica_data/images/perfumes/ | head
# يجب أن ترى ملفات .jpg
```

**الحل 2 - التحقق من الصلاحيات:**
```bash
sudo chown -R odoo:odoo /opt/odoo/addons/lugal_fragrantica/static/
sudo chmod -R 755 /opt/odoo/addons/lugal_fragrantica/static/
```

**الحل 3 - إعادة تحميل الصور:**
- في wizard الاستيراد، تأكد من تفعيل ✅ **Import Images**

---

### ❌ المشكلة: الاستيراد بطيء جداً

**الحل:**
- في wizard الاستيراد، قلّل **Batch Size** إلى `100` أو `200`
- تأكد من أن السيرفر لديه RAM كافية:
  ```bash
  free -h
  ```

---

### ❌ المشكلة: خطأ "Duplicate fragrantica_id"

**السبب:** العطر موجود مسبقاً في القاعدة.

**الحل:**
- لا تعيد الاستيراد إذا كانت البيانات موجودة
- أو احذف البيانات القديمة أولاً (راجع قسم "التحديث")

---

### ❌ المشكلة: لا أجد التاب "Fragrantica" في المنتج

**الحل:**
1. تأكد من تثبيت المودول:
   - Apps → ابحث "Fragrantica" → يجب أن يكون **Installed**

2. أعد تحديث الصفحة (Ctrl+F5)

3. تأكد من الصلاحيات - يجب أن تكون User على الأقل

---

### ❌ المشكلة: البحث لا يعمل بالعربي

**الحل:**
- البحث العربي يعتمد على وجود `arabic_name` في القاعدة
- تأكد من أن الاستيراد شمل الأسماء العربية
- يمكنك التحقق:
  ```python
  # في Python Console
  env['fragrantica.perfume'].search([('arabic_name', '!=', False)]).count()
  ```

---

## 📞 الدعم

إذا واجهت أي مشكلة:

1. **راجع هذا الدليل أولاً**
2. **راجع ملف `README.md` في المودول**
3. **راجع `fragrantica_data_export/README.md`**
4. **اتصل بفريق Lugal**

---

## ✅ Checklist للتثبيت الناجح

قبل أن تبدأ الاستخدام، تأكد من:

- [ ] تم نسخ المودول لمجلد `/opt/odoo/addons/`
- [ ] تم تجهيز البيانات بنجاح على الجهاز المحلي
- [ ] تم نقل `perfumes.db` للسيرفر
- [ ] تم نقل مجلد `images/` للسيرفر
- [ ] تم تعيين الصلاحيات الصحيحة (`chown` و `chmod`)
- [ ] تم تثبيت المودول في Odoo
- [ ] تم استيراد البيانات بنجاح
- [ ] التاب "Fragrantica" يظهر في صفحة المنتج
- [ ] البحث يعمل بالعربي والإنجليزي
- [ ] الصور تظهر بشكل صحيح

---

**🎉 تهانينا! مودول Fragrantica جاهز للاستخدام!**









