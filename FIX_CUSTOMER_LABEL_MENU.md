# حل مشكلة عدم ظهور قائمة Customer Label Templates

## المشكلة
قائمة "Customer Label Templates" لا تظهر في قائمة "Product Labels" لأن النموذج `customer.label.template` غير محمّل في الـ registry.

## الحل الشامل

### الطريقة 1: إعادة تثبيت الموديول من واجهة Odoo (موصى به)

1. **افتح Odoo في المتصفح**
2. **اذهب إلى: Apps**
3. **ابحث عن: Product Label Designer**
4. **اضغط: Uninstall** (إذا كان مثبتاً)
5. **انتظر حتى يكتمل الإلغاء**
6. **اضغط: Install**
7. **انتظر حتى يكتمل التثبيت**
8. **أعد تشغيل Odoo:**
   ```powershell
   cd L:\Lugal-ai
   venv\Scripts\python.exe odoo-bin -c odoo.conf -d lugal --http-port=8070
   ```
9. **حدّث الصفحة:** اضغط `Ctrl + F5` في المتصفح

### الطريقة 2: إعادة تحديث الموديول من Terminal

1. **أوقف Odoo** (إذا كان يعمل)
2. **شغّل الأمر:**
   ```powershell
   cd L:\Lugal-ai
   venv\Scripts\python.exe odoo-bin -c odoo.conf -d lugal --http-port=8070 -u product_label_designer --stop-after-init
   ```
3. **أعد تشغيل Odoo:**
   ```powershell
   venv\Scripts\python.exe odoo-bin -c odoo.conf -d lugal --http-port=8070
   ```
4. **حدّث الصفحة:** اضغط `Ctrl + F5`

### الطريقة 3: التحقق من الموديول في قاعدة البيانات

إذا استمرت المشكلة، تحقق من:
1. الموديول مثبت في قاعدة البيانات
2. النموذج `customer.label.template` موجود في `ir_model`
3. القائمة موجودة في `ir_ui_menu`

## التحقق من الحل

بعد إعادة التثبيت، تحقق من:
1. اذهب إلى: `Inventory` → `Product Labels`
2. يجب أن ترى:
   - Quick Print
   - Label Templates
   - Select Products
   - **Customer Label Templates** (جديد)

## ملاحظات مهمة

- بعد أي تحديث للموديول، يجب **إعادة تشغيل Odoo بشكل كامل**
- يجب **تحديث الصفحة** في المتصفح (`Ctrl + F5`)
- إذا لم تظهر القائمة، جرب **إعادة تثبيت الموديول** من واجهة Odoo






