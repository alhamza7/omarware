# حل مشكلة AssetsLoadingError

## المشكلة
```
AssetsLoadingError: The loading of /web/assets/6ffb030/web_tour.interactive.min.js failed
```

هذه المشكلة تحدث عندما:
1. ملفات Assets المحفوظة في قاعدة البيانات (ir.attachment) قديمة أو تالفة
2. الكاش لم يتم مسحه بشكل صحيح
3. Assets bundle لم يتم إعادة بنائه بعد تحديث الوحدات

## الحل السريع

### الطريقة 1: استخدام السكريبت الشامل (موصى به)

```bash
# تشغيل السكريبت الشامل
./fix_assets_loading_error.sh
```

هذا السكريبت يقوم بـ:
1. إيقاف Odoo
2. مسح الكاش من النظام
3. مسح الكاش من قاعدة البيانات (بما في ذلك جميع Assets)
4. تحديث وحدة web_tour
5. إعادة بناء Assets
6. إعادة تشغيل Odoo

### الطريقة 2: استخدام سكريبت Python

```bash
# تشغيل سكريبت Python مباشرة
python3 fix_assets_error.py
# أو
venv/bin/python fix_assets_error.py
```

### الطريقة 3: خطوات يدوية

#### 1. إيقاف Odoo
```bash
pkill -f "odoo-bin.*lugal"
# أو
pkill -f odoo-bin
```

#### 2. مسح الكاش من قاعدة البيانات
```bash
python3 clear_cache_from_db.py
# أو
venv/bin/python clear_cache_from_db.py
```

#### 3. تحديث وحدة web_tour
```bash
python3 odoo-bin -c odoo.conf -d lugal -u web_tour --stop-after-init
```

#### 4. إعادة بناء Assets (تحديث وحدة web)
```bash
python3 odoo-bin -c odoo.conf -d lugal -u web --stop-after-init
```

#### 5. إعادة تشغيل Odoo
```bash
python3 odoo-bin -c odoo.conf -d lugal --http-port=8069
```

#### 6. مسح كاش المتصفح
- اضغط `Ctrl+Shift+Delete` لمسح الكاش
- أو اضغط `Ctrl+F5` لإعادة تحميل الصفحة بدون كاش

## الحل من داخل Odoo (إذا كان السيرفر يعمل)

### من Odoo Shell:
```python
# فتح Odoo shell
python3 odoo-bin shell -c odoo.conf -d lugal

# ثم في shell:
env['ir.ui.view'].invalidate_model()
env['ir.qweb'].invalidate_model()
env['ir.http'].invalidate_model()
env['ir.actions.actions'].invalidate_model()

# حذف جميع Assets
assets = env['ir.attachment'].search([
    '|',
    ('name', 'like', 'web.assets_%'),
    ('url', 'like', '/web/assets/%')
])
assets.unlink()

# حذف web_tour assets
web_tour_assets = env['ir.attachment'].search([
    '|',
    ('name', 'like', 'web_tour.%'),
    ('name', 'ilike', '%web_tour%')
])
web_tour_assets.unlink()

env.cr.commit()
```

### من واجهة Odoo:
1. اذهب إلى: **Settings** → **Technical** → **Database Structure** → **Attachments**
2. ابحث عن: `web.assets_%` أو `web_tour.%`
3. احذف جميع النتائج
4. أعد تحميل الصفحة

## التحقق من الحل

بعد تطبيق الحل:
1. افتح المتصفح
2. اضغط `Ctrl+Shift+Delete` لمسح الكاش
3. اضغط `Ctrl+F5` لإعادة تحميل الصفحة
4. تحقق من أن الخطأ لم يعد يظهر في Console

## ملاحظات مهمة

- Assets سيتم إعادة بنائها تلقائياً عند أول طلب بعد الحذف
- قد يستغرق إعادة بناء Assets بعض الوقت في المرة الأولى
- تأكد من أن وحدة `web_tour` مثبتة ومحدثة
- إذا استمرت المشكلة، جرب إعادة تثبيت وحدة `web_tour`:
  ```bash
  python3 odoo-bin -c odoo.conf -d lugal -i web_tour --stop-after-init
  ```

## الملفات المتعلقة

- `fix_assets_loading_error.sh` - سكريبت شامل لحل المشكلة
- `fix_assets_error.py` - سكريبت Python لحل المشكلة
- `clear_cache_from_db.py` - سكريبت مسح الكاش (تم تحديثه)
