# ✅ تم تثبيت النسخة المحلية بنجاح!
## Local Installation Complete

---

## 📊 معلومات التثبيت

### قاعدة البيانات:
```
الاسم: lugal_local
المنفذ: 5432
المستخدم: capo7amzah
```

### خادم Odoo:
```
المنفذ: 8070
Long Polling: 8073
الوضع: Development (مع إعادة التحميل التلقائي)
```

### الدخول:
```
المستخدم: admin
كلمة السر: admin
```

---

## 🚀 تشغيل النظام

### الطريقة 1: باستخدام السكريبت (موصى به)

```bash
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
./start_local.sh
```

### الطريقة 2: يدوياً

```bash
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
source venv/bin/activate
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_local
```

### الطريقة 3: في الخلفية

```bash
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
nohup ./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_local > odoo_local.log 2>&1 &
```

---

## 🌐 الوصول للنظام

افتح المتصفح واذهب إلى:

```
http://localhost:8070
```

أو:

```
http://127.0.0.1:8070
```

معلومات الدخول:
```
المستخدم: admin
كلمة السر: admin
```

---

## 📦 الوحدات المثبتة

### الوحدات الأساسية:
```
✅ base - النواة الأساسية
✅ web - الواجهة الويب
✅ sale - المبيعات
✅ purchase - المشتريات
✅ stock - المخزون
✅ account - المحاسبة
```

### الوحدات المخصصة:
```
✅ nbs_archive - نظام الأرشفة
✅ pos_perfume_custom - POS للعطور
```

---

## 🛠️ أوامر مفيدة

### تشغيل Odoo:
```bash
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
./start_local.sh
```

### إيقاف Odoo:
```bash
pkill -f "odoo-bin.*lugal_local"
# أو Ctrl+C في terminal الذي يعمل فيه
```

### تثبيت وحدة:
```bash
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_local \
    -i module_name --stop-after-init
```

### ترقية وحدة:
```bash
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_local \
    -u module_name --stop-after-init
```

### فتح Odoo Shell:
```bash
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
./venv/bin/python odoo-bin shell -c odoo_local.conf -d lugal_local

# في الشل:
>>> env['res.users'].search([])
>>> env['product.product'].search_count([])
```

### مراقبة اللوغات:
```bash
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
tail -f odoo_local.log
```

---

## 🔧 الإعدادات

### ملف الإعدادات:
```
odoo_local.conf
```

### مجلد الملفات:
```
filestore_local/
```

### ملف اللوغات:
```
odoo_local.log
```

---

## 📝 ملاحظات مهمة

### المنفذ 8070:
```
⚠️  النسخة المحلية تعمل على المنفذ 8070 (وليس 8069)
⚠️  هذا لتجنب التعارض مع أي نسخة Odoo أخرى
```

### وضع التطوير:
```
✅ التحميل التلقائي للتغييرات مفعّل
✅ تحديثات QWeb التلقائية مفعلة
✅ تحديثات XML التلقائية مفعلة
```

### قاعدة البيانات:
```
💡 قاعدة البيانات منفصلة عن قاعدة الإنتاج
💡 يمكنك حذفها وإعادة إنشائها بحرية
💡 لاستيراد من الإنتاج، راجع القسم التالي
```

---

## 🔄 استيراد بيانات من الإنتاج

### إذا أردت نسخ بيانات من السيرفر البعيد:

#### 1. نسخ قاعدة البيانات:
```bash
# على السيرفر
ssh lugalai@192.168.116.211
pg_dump nbs_lugalai > ~/backup.sql
exit

# على جهازك
scp lugalai@192.168.116.211:~/backup.sql ~/

# استيراد
dropdb lugal_local
createdb lugal_local
psql lugal_local < ~/backup.sql
```

#### 2. نسخ الملفات:
```bash
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
rsync -avz lugalai@192.168.116.211:/var/lib/odoo/filestore/nbs_lugalai/ \
    filestore_local/lugal_local/
```

---

## 🐛 استكشاف الأخطاء

### المشكلة: "Database does not exist"
```bash
createdb lugal_local
```

### المشكلة: "Port 8070 already in use"
```bash
# أوقف العملية القديمة
pkill -f "odoo-bin.*lugal_local"

# أو غير المنفذ في odoo_local.conf
nano odoo_local.conf
# غير http_port = 8070 إلى 8071
```

### المشكلة: "Permission denied"
```bash
# تأكد من الصلاحيات
chmod +x start_local.sh
chmod -R 755 filestore_local/
```

### المشكلة: "Module not found"
```bash
# أعد تثبيت المتطلبات
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📊 الحالة الحالية

```
✅ Python 3.x - مثبت
✅ PostgreSQL - مثبت وجاهز
✅ Virtual Environment - تم إنشاؤه
✅ Dependencies - تم تثبيتها
✅ Database (lugal_local) - تم إنشاؤها
✅ Base Modules - مثبتة
✅ Custom Modules - مثبتة
✅ Configuration File - تم إنشاؤه
✅ Admin User - جاهز
✅ Start Script - جاهز
```

---

## 🎯 الخطوة التالية

### ابدأ الآن:

```bash
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
./start_local.sh
```

### ثم افتح المتصفح:

```
http://localhost:8070
```

### سجل دخول:

```
المستخدم: admin
كلمة السر: admin
```

---

## 🎉 مبروك!

نسختك المحلية من Lugal NBS ERP جاهزة للاستخدام! 🚀

يمكنك الآن:
- تطوير وحدات جديدة
- اختبار الميزات
- التدرب على النظام
- العمل بدون اتصال بالإنترنت

---

**تاريخ التثبيت:** $(date)  
**المسار:** /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai  
**قاعدة البيانات:** lugal_local  
**المنفذ:** 8070
