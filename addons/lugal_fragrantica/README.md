# 🌸 Fragrantica Integration Module for Odoo

مودول Odoo لربط المنتجات مع قاعدة بيانات Fragrantica الشاملة للعطور.

---

## 📋 المميزات

- ✅ ربط منتجات العطور مع قاعدة بيانات شاملة (+49,000 عطر)
- ✅ عرض معلومات تفصيلية: النوتات العطرية، التوافقات، الوصف، الصور
- ✅ بحث متقدم بالعربي والإنجليزي
- ✅ إمكانية تخصيص وتعديل جميع المعلومات
- ✅ طلب إضافة عطور جديدة من موقع Fragrantica
- ✅ تاب مخصص في صفحة المنتج لعرض كل معلومات العطر

---

## 📦 التثبيت

### 1. نسخ المودول

```bash
cd /opt/odoo/addons/
git clone <repository_url> lugal_fragrantica
# أو نسخ المجلد يدوياً
```

### 2. تجهيز البيانات

**على جهازك المحلي:**

```bash
cd /path/to/Lugal-ai/fragrantica_data_export
python3 prepare_export.py
```

هذا سينشئ مجلد `fragrantica_data_export` يحتوي على:
- قاعدة البيانات `perfumes.db`
- مجلد `images/` بكل الصور

**نقل البيانات للسيرفر:**

```bash
# نسخ المجلد للسيرفر
scp -r fragrantica_data_export/ user@server:/tmp/

# على السيرفر
ssh user@server
cd /opt/odoo/addons/lugal_fragrantica
sudo mkdir -p static/fragrantica_data
sudo cp /tmp/fragrantica_data_export/perfumes.db static/fragrantica_data/
sudo cp -r /tmp/fragrantica_data_export/images static/fragrantica_data/
sudo chown -R odoo:odoo static/fragrantica_data
```

### 3. تثبيت المودول في Odoo

1. إعادة تشغيل Odoo:
   ```bash
   sudo systemctl restart odoo
   ```

2. في Odoo:
   - اذهب إلى **Apps**
   - ابحث عن "Fragrantica Integration"
   - اضغط **Install**

3. استيراد البيانات:
   - اذهب إلى **Fragrantica → Configuration → Import Data**
   - اضغط **Start Import**
   - انتظر حتى اكتمال الاستيراد (10-20 دقيقة)

---

## 🎯 الاستخدام

### ربط منتج بعطر من Fragrantica

1. افتح صفحة المنتج
2. اذهب إلى تاب **Fragrantica**
3. في حقل "Fragrantica Perfume"، ابحث عن العطر (بالعربي أو الإنجليزي)
4. اختر العطر المناسب
5. ستظهر تلقائياً جميع المعلومات:
   - صورة العطر
   - الاسم (عربي + انجليزي)
   - البراند والشعار
   - سنة الإصدار
   - الوصف الكامل
   - التوافقات الرئيسية (Main Accords)
   - النوتات العطرية (Top, Middle, Base)

### تخصيص المعلومات

إذا أردت تعديل أي معلومات:
1. فعّل خيار **Use Custom Data**
2. الآن يمكنك:
   - تعديل الوصف
   - تعديل السنة
   - إضافة/حذف نوتات عطرية
   - إضافة/حذف توافقات

### إضافة عطر غير موجود

إذا لم تجد العطر في قاعدة البيانات:
1. الصق رابط Fragrantica في حقل "Fragrantica URL (Pending)"
2. اضغط **Create Request**
3. سيتم إضافة الطلب لقائمة الانتظار
4. بعد جلب البيانات يدوياً وتحديث قاعدة البيانات، يمكن ربط العطر

---

## 📊 إدارة البيانات

### عرض جميع العطور

اذهب إلى: **Fragrantica → Perfumes**

هنا يمكنك:
- البحث في جميع العطور
- فلترة حسب البراند أو السنة
- عرض تفاصيل أي عطر
- رؤية المنتجات المربوطة بكل عطر

### طلبات الانتظار

اذهب إلى: **Fragrantica → Pending Requests**

هنا تظهر جميع الطلبات لإضافة عطور جديدة:
- حالة الطلب (Pending, Processing, Completed, Failed)
- الرابط المطلوب
- المنتج المرتبط
- المستخدم الذي قام بالطلب

---

## 🗄️ هيكل قاعدة البيانات

### Models الرئيسية

#### `fragrantica.perfume`
قاعدة بيانات العطور الكاملة:
- معلومات أساسية (اسم، براند، سنة)
- صور (عطر، براند)
- وصف كامل
- علاقات مع النوتات والتوافقات

#### `fragrantica.note`
النوتات العطرية:
- نوع النوتة (Top, Middle, Base)
- اسم النوتة
- صورة النوتة
- نسبة الظهور

#### `fragrantica.accord`
التوافقات الرئيسية:
- اسم التوافق
- نسبة التوافق
- لون التوافق

#### `product.template` (موسّع)
تم إضافة حقول:
- ربط بعطر Fragrantica
- معلومات مخصصة قابلة للتعديل
- نوتات وتوافقات مخصصة

---

## 🔧 التخصيص

### تغيير مسار قاعدة البيانات

يمكنك وضع `perfumes.db` في أي مكان وتحديد المسار في wizard الاستيراد.

### إضافة حقول إضافية

يمكن بسهولة توسيع Models لإضافة معلومات إضافية:

```python
class FragranticaPerfume(models.Model):
    _inherit = 'fragrantica.perfume'
    
    # أضف حقولك الجديدة
    custom_field = fields.Char('Custom Field')
```

---

## 📈 الأداء

### حجم البيانات
- 49,000+ عطر
- 150,000+ نوتة
- 100,000+ توافق
- 43,000+ صورة

### الاستيراد
- الوقت المتوقع: 10-20 دقيقة
- يمكن تقليل Batch Size إذا كان السيرفر بطيئاً

### البحث
- البحث سريع جداً بفضل PostgreSQL indexes
- دعم البحث بالعربي والإنجليزي معاً

---

## 🐛 حل المشاكل

### المشكلة: "Database file not found"
**الحل:**
```bash
cd /opt/odoo/addons/lugal_fragrantica/static
ls -la fragrantica_data/perfumes.db
# إذا لم يكن موجوداً، انسخه من مجلد التصدير
```

### المشكلة: الصور لا تظهر
**الحل:**
- تأكد من نسخ مجلد `images/` كاملاً
- تأكد من الصلاحيات: `sudo chown -R odoo:odoo static/fragrantica_data`
- في wizard الاستيراد، تأكد من تفعيل "Import Images"

### المشكلة: الاستيراد بطيء جداً
**الحل:**
- قلل Batch Size إلى 100 أو 200
- تأكد من أن السيرفر لديه RAM كافية (2GB+)

### المشكلة: خطأ "Duplicate fragrantica_id"
**الحل:**
- البيانات موجودة مسبقاً
- إما احذف البيانات القديمة أو لا تعيد الاستيراد

---

## 🔄 التحديث

لتحديث قاعدة البيانات ببيانات جديدة:

1. على جهازك المحلي، قم بتحديث `fregran/perfumes.db`
2. شغّل `prepare_export.py` مرة أخرى
3. انقل الملفات المحدثة للسيرفر
4. في Odoo، احذف البيانات القديمة:
   ```python
   # من Python Console في Odoo
   env['fragrantica.perfume'].search([]).unlink()
   ```
5. أعد تشغيل الاستيراد

---

## 📝 الصلاحيات

### المستخدمون العاديون
- عرض العطور
- ربط المنتجات بالعطور
- إنشاء طلبات لعطور جديدة
- تعديل المعلومات المخصصة

### المدراء (System)
- جميع صلاحيات المستخدمين العاديين
- استيراد البيانات
- تعديل قاعدة بيانات العطور
- إدارة الطلبات المعلقة

---

## 🤝 المساهمة

لإضافة ميزات جديدة أو تحسينات:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 الترخيص

LGPL-3

---

## 📧 الدعم

للدعم والمساعدة:
- راجع ملف `fragrantica_data_export/README.md` لتعليمات النقل
- راجع Issues في GitHub
- اتصل بفريق Lugal

---

**صُنع بـ ❤️ من فريق Lugal**






