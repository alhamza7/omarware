# حل خطأ ModuleNotFoundError: opensearchpy

## المشكلة

عند محاولة تثبيت أي وحدة في Odoo (مثل `sale`)، يظهر الخطأ التالي:

```
ModuleNotFoundError: No module named 'opensearchpy'
  File "/home/lugalai/Lugal-ai/addons/nbs_archive/models/opensearch_service.py", line 6, in <module>
    from opensearchpy import OpenSearch, exceptions as opensearch_exceptions
```

## السبب

وحدة `nbs_archive` تحتاج إلى مكتبة `opensearchpy` التي لم يتم تثبيتها في البيئة الافتراضية (venv).

## الحل السريع (السيرفر البعيد)

```bash
cd /home/lugalai/Lugal-ai

# سحب التحديثات
git pull origin main

# تشغيل سكريبت التثبيت
bash install_opensearchpy.sh
```

هذا السكريبت سيقوم بـ:
1. ✅ إيقاف Odoo
2. ✅ تثبيت `opensearchpy`
3. ✅ تثبيت المكتبات المرتبطة
4. ✅ إعادة تشغيل Odoo

## الحل اليدوي

إذا أردت التثبيت يدوياً:

```bash
cd /home/lugalai/Lugal-ai

# إيقاف Odoo
pkill -9 -f odoo-bin
sleep 3

# تثبيت opensearchpy
venv/bin/pip install opensearchpy

# إعادة تشغيل Odoo
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &
```

## التحقق من التثبيت

بعد تشغيل السكريبت أو التثبيت اليدوي:

### 1. تحقق من أن Odoo يعمل:
```bash
ps aux | grep odoo-bin
```

يجب أن ترى عملية Odoo تعمل.

### 2. تحقق من أن المكتبة مثبتة:
```bash
venv/bin/pip list | grep opensearch
```

يجب أن ترى:
```
opensearchpy    2.x.x
```

### 3. تحقق من اللوج:
```bash
tail -50 /home/lugalai/Lugal-ai/odoo.log
```

يجب ألا ترى أخطاء `ModuleNotFoundError`.

## الآن يمكنك

1. ✅ تثبيت وحدة `sale` من Apps
2. ✅ تثبيت أي وحدة أخرى
3. ✅ وحدة `nbs_archive` يجب أن تعمل بدون مشاكل

## معلومات إضافية

### ما هي opensearchpy؟

`opensearchpy` هي مكتبة Python للتواصل مع OpenSearch (نظام بحث وتحليل بيانات مفتوح المصدر مشابه لـ Elasticsearch).

### لماذا تحتاجها وحدة nbs_archive؟

وحدة `nbs_archive` تستخدم OpenSearch لأرشفة وفهرسة البيانات للبحث السريع.

### هل يمكن تعطيل nbs_archive؟

نعم، إذا لم تكن تستخدم وحدة `nbs_archive`، يمكنك:

1. **نقلها خارج addons path**:
   ```bash
   mv /home/lugalai/Lugal-ai/addons/nbs_archive /home/lugalai/nbs_archive_backup
   ```

2. **أو تعديل `__init__.py` لتجاهل الأخطاء**:
   ```python
   try:
       from . import models
   except ImportError:
       pass
   ```

لكن **الحل الأفضل** هو تثبيت المكتبة المطلوبة.

## استكشاف الأخطاء

### إذا فشل التثبيت:

#### 1. تحديث pip:
```bash
venv/bin/pip install --upgrade pip
```

#### 2. تثبيت من requirements.txt:
```bash
venv/bin/pip install -r requirements.txt
```

#### 3. تحقق من الإنترنت:
```bash
ping pypi.org
```

### إذا استمر الخطأ بعد التثبيت:

```bash
# تحقق من أن البيئة الافتراضية صحيحة
which python
# يجب أن يعطي: /home/lugalai/Lugal-ai/venv/bin/python

# تحقق من أن Odoo يستخدم البيئة الافتراضية
ps aux | grep odoo-bin
# يجب أن ترى: venv/bin/python odoo-bin
```

## ملاحظات

- تم إضافة `opensearchpy` إلى `requirements.txt` لتجنب هذه المشكلة في المستقبل
- عند إعداد نسخة Odoo جديدة، استخدم:
  ```bash
  venv/bin/pip install -r requirements.txt
  ```
  لتثبيت جميع المكتبات المطلوبة

## الدعم

إذا استمرت المشكلة، أرسل:
1. نتيجة `venv/bin/pip list | grep opensearch`
2. آخر 50 سطر من `odoo.log`
3. نتيجة `ps aux | grep odoo-bin`
