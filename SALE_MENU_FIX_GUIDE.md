# دليل إصلاح قائمة Sale

## المشكلة
قائمة Sales/المبيعات لا تظهر في القائمة الرئيسية لـ Odoo

## الأسباب المحتملة

1. **الوحدة غير مثبتة**: وحدة `sale` غير مثبتة أو معطلة
2. **القائمة الرئيسية مفقودة**: القائمة الرئيسية Sales غير موجودة في الـ Root
3. **صلاحيات المستخدم**: المستخدم ليس لديه صلاحيات الوصول لقوائم Sale
4. **الكاش قديم**: الكاش في قاعدة البيانات أو المتصفح قديم

## الحل السريع (السيرفر البعيد)

```bash
cd /home/lugalai/Lugal-ai

# سحب آخر التحديثات
git pull origin main

# تشغيل سكريبت الإصلاح
bash fix_sale_menu_remote.sh
```

## ماذا يفعل السكريبت؟

### 1. إيقاف Odoo
```bash
pkill -9 -f odoo-bin
```

### 2. تثبيت/ترقية وحدة sale
```bash
venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai -i sale --stop-after-init
```

### 3. إصلاح القوائم والصلاحيات
- ✅ إنشاء القائمة الرئيسية Sales إذا كانت مفقودة
- ✅ تفعيل القوائم المعطلة
- ✅ إضافة صلاحيات Sale Manager و Sale User للمستخدم
- ✅ مسح الكاش

### 4. إعادة تشغيل Odoo
```bash
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &
```

## بعد تشغيل السكريبت

### في المتصفح:
1. **امسح الكاش تماماً**: `Ctrl+Shift+Delete`
   - ✅ Cookies وبيانات المواقع
   - ✅ الصور والملفات المخزنة مؤقتاً
2. **سجل خروج** من Odoo
3. **أغلق المتصفح** تماماً
4. **افتحه من جديد** وسجل دخول

## التحقق من النتيجة

يجب أن تظهر قائمة **Sales** أو **المبيعات** في القائمة الرئيسية بجانب:
- Dashboard
- Contacts
- Inventory
- إلخ...

## استكشاف الأخطاء

### إذا لم تظهر القائمة:

#### 1. تحقق من سجل الأخطاء
```bash
tail -100 /home/lugalai/Lugal-ai/odoo.log
```

#### 2. تحقق من أن Odoo يعمل
```bash
ps aux | grep odoo-bin
```

#### 3. تحقق من حالة الوحدة
```bash
venv/bin/python odoo-bin shell -c odoo.conf -d nbs_lugalai
```

ثم في shell:
```python
module = env['ir.module.module'].search([('name', '=', 'sale')])
print(f"State: {module.state}")
print(f"Installed: {module.installed_version}")
```

#### 4. تحقق من القوائم
```python
menus = env['ir.ui.menu'].search([('name', '=', 'Sales')])
for menu in menus:
    print(f"ID: {menu.id}, Parent: {menu.parent_id.name}, Active: {menu.active}")
```

#### 5. تحقق من صلاحيات المستخدم
```python
user = env['res.users'].browse(env.uid)
print(f"User: {user.name}")
groups = user.group_ids.filtered(lambda g: 'sale' in g.name.lower())
for group in groups:
    print(f"  - {group.name}")
```

## الإصلاح اليدوي

إذا فشل السكريبت، يمكن الإصلاح يدوياً:

### 1. تثبيت الوحدة
من واجهة Odoo:
- اذهب إلى **Settings** → **Apps**
- ابحث عن "**Sales**"
- اضغط **Install** أو **Upgrade**

### 2. إضافة الصلاحيات
- اذهب إلى **Settings** → **Users & Companies** → **Users**
- افتح المستخدم الحالي
- في تبويب **Access Rights**، تأكد من تفعيل:
  - ✅ Sales / Manager
  - ✅ Sales / User

### 3. تفعيل القائمة
إذا كانت القائمة موجودة لكن معطلة:
```bash
venv/bin/python odoo-bin shell -c odoo.conf -d nbs_lugalai
```

```python
menu = env['ir.ui.menu'].search([('name', '=', 'Sales'), ('parent_id', '=', False)])
if menu:
    menu.active = True
    env.cr.commit()
```

## ملاحظات مهمة

1. **مسح الكاش ضروري**: لا تتخطى خطوة مسح كاش المتصفح
2. **تسجيل خروج ودخول**: بعد مسح الكاش، سجل خروج ودخول
3. **إعادة تشغيل Odoo**: يجب إعادة تشغيل Odoo بعد التغييرات
4. **الصبر**: انتظر 5-10 ثوان بعد إعادة تشغيل Odoo قبل الدخول

## الدعم

إذا استمرت المشكلة:
1. أرسل محتوى `odoo.log` (آخر 100 سطر)
2. أرسل نتيجة تشغيل `check_sale_module.py`
3. أرسل لقطة شاشة من القائمة الرئيسية
