# إصلاح خطأ الصلاحيات في نظام الأرشفة NBS Archive

## المشكلة

```
Error 13: Permission denied
/var/lib/odoo
```

عند محاولة رفع مستند في نظام الأرشفة NBS Archive، يظهر هذا الخطأ.

### السبب
- ❌ مستخدم Odoo لا يملك صلاحيات الكتابة على `/var/lib/odoo`
- ❌ مجلد `filestore` غير موجود أو بصلاحيات خاطئة
- ❌ مجلد قاعدة البيانات غير موجود في `filestore`

---

## الحل السريع ⚡

### على السيرفر البعيد:

```bash
cd /home/lugalai/Lugal-ai

# سحب التحديثات
git pull origin main

# تشغيل سكريبت إصلاح الصلاحيات
bash fix_filestore_permissions.sh
```

---

## الحل اليدوي (خطوة بخطوة)

### 1️⃣ التحقق من المجلدات

```bash
# التحقق من وجود المجلدات
ls -la /var/lib/odoo
ls -la /var/lib/odoo/filestore
ls -la /var/lib/odoo/filestore/nbs_lugalai
```

### 2️⃣ إنشاء المجلدات إذا لزم الأمر

```bash
# إنشاء المجلدات
sudo mkdir -p /var/lib/odoo/filestore/nbs_lugalai
```

### 3️⃣ إصلاح الصلاحيات

```bash
# تحديد المستخدم الحالي (عادة lugalai)
CURRENT_USER=$(whoami)

# إعطاء ملكية المجلدات للمستخدم
sudo chown -R $CURRENT_USER:$CURRENT_USER /var/lib/odoo

# إعطاء صلاحيات القراءة والكتابة
sudo chmod -R 775 /var/lib/odoo
```

### 4️⃣ اختبار الصلاحيات

```bash
# محاولة إنشاء ملف تجريبي
echo "test" > /var/lib/odoo/test.txt

# إذا نجح، احذف الملف
rm /var/lib/odoo/test.txt
```

### 5️⃣ إعادة تشغيل Odoo

```bash
# إيقاف Odoo
pkill -9 -f odoo-bin

# إعادة التشغيل
cd /home/lugalai/Lugal-ai
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &
```

---

## التحقق من الإعدادات

### استخدام سكريبت الفحص:

```bash
cd /home/lugalai/Lugal-ai
venv/bin/python check_filestore_config.py
```

**النتيجة المتوقعة:**
```
============================================================
التحقق من إعدادات Filestore - قاعدة البيانات: nbs_lugalai
============================================================

1. مجلد البيانات (data_dir):
   المسار: /var/lib/odoo
   ✅ المجلد موجود
   ✅ يمكن الكتابة

2. مجلد filestore:
   المسار: /var/lib/odoo/filestore/nbs_lugalai
   ✅ المجلد موجود
   ✅ يمكن الكتابة
   📊 عدد الملفات: 0
   📊 الحجم الإجمالي: 0.00 MB

3. اختبار الكتابة...
   ✅ نجح اختبار الكتابة!

4. التحقق من المرفقات في قاعدة البيانات...
   📎 إجمالي المرفقات: 45
   📎 مرفقات نظام الأرشفة: 0
   💾 مرفقات في filestore: 30
   💾 مرفقات في قاعدة البيانات: 15

============================================================
✅ انتهى الفحص
============================================================

التوصيات:
✅ جميع الإعدادات صحيحة!
```

---

## فهم المشكلة

### كيف يخزن Odoo الملفات؟

```
/var/lib/odoo/
├── filestore/
│   ├── nbs_lugalai/           ← قاعدة البيانات
│   │   ├── 01/
│   │   │   └── 0123456789abcdef...  ← ملفات مشفرة
│   │   ├── 02/
│   │   ├── nbs_archive/       ← مجلد نظام الأرشفة (اختياري)
│   │   └── ...
│   └── other_db/
└── sessions/
```

### عملية رفع ملف:

1. المستخدم يرفع ملف في نظام الأرشفة
2. Odoo يحاول حفظه في `/var/lib/odoo/filestore/nbs_lugalai/`
3. إذا لم يكن للمستخدم صلاحيات → **Error 13: Permission denied**

---

## الأسباب الشائعة

### 1. تشغيل Odoo بمستخدم مختلف

```bash
# التحقق من المستخدم الذي يشغل Odoo
ps aux | grep odoo-bin

# إذا كان يعمل بمستخدم آخر (مثل root)، أعد التشغيل
pkill -9 -f odoo-bin
su - lugalai  # أو المستخدم الصحيح
cd /home/lugalai/Lugal-ai
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &
```

### 2. المجلد ملك لمستخدم آخر

```bash
# التحقق من المالك
ls -la /var/lib/odoo

# إذا كان المالك root أو مستخدم آخر
sudo chown -R lugalai:lugalai /var/lib/odoo
```

### 3. صلاحيات القراءة فقط

```bash
# التحقق من الصلاحيات
ls -la /var/lib/odoo

# مثال على صلاحيات خاطئة:
drwxr-xr-x  ← صلاحيات قراءة فقط للمجموعة والآخرين

# إصلاح:
sudo chmod -R 775 /var/lib/odoo
```

### 4. SELinux أو AppArmor

```bash
# التحقق من SELinux (RedHat/CentOS)
getenforce

# إذا كان مفعّلاً، أضف سياسة:
sudo semanage fcontext -a -t odoo_var_lib_t "/var/lib/odoo(/.*)?"
sudo restorecon -R /var/lib/odoo

# التحقق من AppArmor (Ubuntu/Debian)
sudo aa-status

# إذا كان يمنع Odoo، عطّله مؤقتاً:
sudo aa-complain /usr/bin/python3
```

---

## حل بديل: تغيير مسار data_dir

إذا استمرت المشكلة، يمكنك تغيير مسار التخزين:

### 1. تعديل `odoo.conf`

```bash
nano /home/lugalai/Lugal-ai/odoo.conf
```

```ini
[options]
data_dir = /home/lugalai/odoo_data
# ... باقي الإعدادات
```

### 2. إنشاء المجلد الجديد

```bash
mkdir -p /home/lugalai/odoo_data/filestore
chmod -R 775 /home/lugalai/odoo_data
```

### 3. نقل البيانات القديمة (إذا وجدت)

```bash
# نقل filestore القديم
if [ -d "/var/lib/odoo/filestore" ]; then
    cp -r /var/lib/odoo/filestore/* /home/lugalai/odoo_data/filestore/
fi
```

### 4. إعادة تشغيل Odoo

```bash
pkill -9 -f odoo-bin
cd /home/lugalai/Lugal-ai
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &
```

---

## اختبار نظام الأرشفة

### في المتصفح:

1. **افتح Odoo**: `http://192.168.116.211:8069`
2. **سجل دخول** بحساب الأدمن
3. **اذهب إلى**: `NBS Archive` → `Documents`
4. **أنشئ مستند جديد**:
   - Name: Test Document
   - Department: Finance
   - Document Type: Invoice
5. **رفع ملف**: اضغط "Upload" وارفع ملف PDF
6. **حفظ**

### إذا نجح:
```
✅ تم رفع الملف بنجاح!
```

### إذا فشل:
```
❌ Error 13: Permission denied /var/lib/odoo/filestore/nbs_lugalai/...
```

تحقق من:
```bash
# مراقبة اللوغات
tail -f /home/lugalai/Lugal-ai/odoo.log | grep -i permission
```

---

## للمطورين: كيف يعمل Odoo filestore؟

### في Odoo:

```python
# addons/base/models/ir_attachment.py
@api.model
def _filestore(self):
    return tools.config.filestore(self._cr.dbname)

# في odoo/tools/config.py
def filestore(db_name):
    return os.path.join(config['data_dir'], 'filestore', db_name)
```

### عند رفع ملف:

```python
# في nbs.document (نظام الأرشفة)
attachment = self.env['ir.attachment'].create({
    'name': filename,
    'datas': base64_content,
    'res_model': 'nbs.document',
    'res_id': document.id,
})

# Odoo تلقائياً:
# 1. يحسب hash الملف
# 2. يحفظه في filestore/nbs_lugalai/[hash[:2]]/[hash]
# 3. يخزن المسار في ir_attachment.store_fname
```

---

## الملخص

| المشكلة | الحل |
|---------|------|
| ❌ Error 13 | ✅ `sudo chown -R lugalai:lugalai /var/lib/odoo` |
| ❌ المجلد غير موجود | ✅ `sudo mkdir -p /var/lib/odoo/filestore/nbs_lugalai` |
| ❌ صلاحيات قراءة فقط | ✅ `sudo chmod -R 775 /var/lib/odoo` |
| ❌ مستخدم خاطئ | ✅ تشغيل Odoo بمستخدم `lugalai` |

---

## الملفات المضافة:

1. ✅ **`fix_filestore_permissions.sh`**: سكريبت إصلاح الصلاحيات التلقائي
2. ✅ **`check_filestore_config.py`**: سكريبت فحص الإعدادات والصلاحيات
3. ✅ **`FIX_ARCHIVE_PERMISSION_ERROR_AR.md`**: دليل مفصل بالعربية

---

## الوقاية من المشكلة

### عند إنشاء سيرفر جديد:

```bash
# 1. إنشاء مستخدم Odoo
sudo useradd -m -s /bin/bash lugalai

# 2. إنشاء مجلد البيانات
sudo mkdir -p /var/lib/odoo/filestore
sudo chown -R lugalai:lugalai /var/lib/odoo
sudo chmod -R 775 /var/lib/odoo

# 3. تشغيل Odoo بالمستخدم الصحيح
su - lugalai
cd /home/lugalai/Lugal-ai
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &
```

---

**الآن نفذ السكريبت على السيرفر البعيد!** 🚀

```bash
bash fix_filestore_permissions.sh
```
