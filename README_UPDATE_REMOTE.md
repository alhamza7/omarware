# دليل تحديث الكود على سطح المكتب البعيد

## المشكلة
بعد تحديث الملفات من GitHub، التغييرات لا تظهر لأن:
1. الوحدات لم يتم تحديثها في قاعدة البيانات
2. الكاش لم يتم مسحه
3. Assets (ملفات JavaScript/CSS) لم يتم تجميعها من جديد

## الحل السريع

### الطريقة 1: استخدام السكريبت الشامل (موصى به)

```bash
# جعل السكريبت قابل للتنفيذ
chmod +x update_and_clear_cache.sh

# تشغيل السكريبت
./update_and_clear_cache.sh
```

### الطريقة 2: خطوات يدوية

#### 1. إيقاف Odoo
```bash
pkill -f "odoo-bin.*lugal"
# أو
pkill -f odoo-bin
```

#### 2. مسح الكاش من النظام
```bash
rm -rf ~/.local/share/Odoo/filestore/lugal/*
rm -rf /tmp/odoo_*
find ~/Lugal-ai -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find ~/Lugal-ai -type f -name "*.pyc" -delete 2>/dev/null || true
```

#### 3. تحديث الوحدات
```bash
cd ~/Lugal-ai
venv/bin/python odoo-bin -c odoo.conf -d lugal \
    -u pos_perfume_custom,sap_integration \
    --stop-after-init
```

#### 4. مسح الكاش من قاعدة البيانات
```bash
# استخدام السكريبت Python
venv/bin/python clear_cache_from_db.py

# أو من Odoo shell
venv/bin/python odoo-bin shell -c odoo.conf -d lugal
# ثم في shell:
# >>> env['ir.ui.view'].clear_caches()
# >>> env['ir.qweb'].clear_caches()
# >>> env['ir.http'].clear_caches()
# >>> env['ir.actions.actions'].clear_caches()
# >>> assets = env['ir.attachment'].search([('name', 'like', 'web.assets_%')])
# >>> assets.unlink()
# >>> env.cr.commit()
```

#### 5. إعادة تشغيل Odoo
```bash
cd ~/Lugal-ai
venv/bin/python odoo-bin -c odoo.conf -d lugal --http-port=8069

# أو في الخلفية:
nohup venv/bin/python odoo-bin -c odoo.conf -d lugal --http-port=8069 > odoo.log 2>&1 &
```

### الطريقة 3: من واجهة Odoo (إذا كان السيرفر يعمل)

1. اذهب إلى: **Apps** → **SAP Integration** → **Upgrade**
2. اذهب إلى: **Apps** → **POS Perfume Custom** → **Upgrade**
3. امسح كاش المتصفح (Ctrl+Shift+Delete)
4. أعد تحميل الصفحة (Ctrl+F5)

## مسح كاش المتصفح

### Chrome/Edge:
- اضغط `Ctrl+Shift+Delete`
- اختر "Cached images and files"
- اضغط "Clear data"

### Firefox:
- اضغط `Ctrl+Shift+Delete`
- اختر "Cache"
- اضغط "Clear Now"

### أو استخدم:
- `Ctrl+F5` - إعادة تحميل قوية
- `Ctrl+Shift+R` - إعادة تحميل بدون كاش

## التحقق من التحديث

### 1. تحقق من السجل
```bash
tail -f odoo.log | grep -E "POS|SAP|action_confirm"
```

### 2. تحقق من إصدار الكود
```bash
# في ملف Python
grep -n "def action_confirm" addons/pos_perfume_custom/models/pos_perfume_order.py

# في ملف JavaScript
grep -n "action_confirm" addons/pos_perfume_custom/static/src/app/pos_perfume_screen.js
```

### 3. تحقق من قاعدة البيانات
```bash
venv/bin/python odoo-bin shell -c odoo.conf -d lugal
# ثم:
# >>> env['ir.module.module'].search([('name', '=', 'pos_perfume_custom')]).read(['state', 'latest_version'])
```

## نصائح مهمة

1. **دائماً أعد تشغيل Odoo** بعد تحديث الكود
2. **امسح كاش المتصفح** بعد تحديث JavaScript/CSS
3. **استخدم `-u` لتحديث الوحدات** بعد تغيير Python code
4. **استخدم `--stop-after-init`** عند التحديث لتجنب مشاكل

## حل مشاكل شائعة

### المشكلة: التغييرات لا تظهر
**الحل:**
```bash
# 1. تأكد من تحديث الوحدات
-u pos_perfume_custom,sap_integration

# 2. امسح الكاش
./update_and_clear_cache.sh

# 3. أعد تشغيل Odoo
```

### المشكلة: JavaScript لا يتحدث
**الحل:**
```bash
# 1. حذف assets من قاعدة البيانات
venv/bin/python clear_cache_from_db.py

# 2. امسح كاش المتصفح
# 3. أعد تحميل الصفحة (Ctrl+F5)
```

### المشكلة: السجل لا يسجل
**الحل:**
```bash
# 1. تحقق من إعدادات السجل في odoo.conf
grep logfile odoo.conf

# 2. تحقق من الصلاحيات
ls -la odoo.log

# 3. أعد تشغيل Odoo
```

## أوامر مفيدة

```bash
# متابعة السجل في الوقت الفعلي
tail -f odoo.log

# البحث عن أخطاء
grep ERROR odoo.log | tail -20

# البحث عن أخطاء SAP
grep -i "sap.*error\|error.*sap" odoo.log | tail -20

# التحقق من حالة Odoo
ps aux | grep odoo-bin

# إيقاف Odoo
pkill -f odoo-bin

# عرض آخر 50 سطر من السجل
tail -n 50 odoo.log
```

