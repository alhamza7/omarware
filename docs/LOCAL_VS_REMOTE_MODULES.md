# إدارة الوحدات المختلفة بين البيئة المحلية والسيرفر البعيد

## المشكلة

بعض الوحدات مثل `sap_integration` تعمل على السيرفر البعيد لكن تحتاج مكتبات غير متوفرة محلياً (مثل `connector`, `queue_job`).

## ❌ الحل الخاطئ

**لا تغير `__manifest__.py` إلى `installable: False`**

لماذا؟ لأن هذا التغيير سيؤثر على السيرفر البعيد عند عمل `git push`.

## ✅ الحل الصحيح

### الطريقة 1: عدم تثبيت الوحدة محلياً

ببساطة لا تثبت الوحدة محلياً:

```bash
# عند تهيئة Odoo محلياً، لا تضع sap_integration في قائمة الوحدات
./venv/bin/python odoo-bin -c odoo_local.conf \
  -i base,web,sale,purchase,stock,account,hr,nbs_archive,pos_perfume_custom \
  --stop-after-init

# لاحظ: sap_integration غير موجود في القائمة
```

### الطريقة 2: حذف الوحدة من قاعدة البيانات المحلية

إذا كانت الوحدة مثبتة بالفعل:

```bash
psql lugal_local -c "DELETE FROM ir_module_module WHERE name = 'sap_integration';"
```

### الطريقة 3: تحديد الوحدات المسموحة في odoo_local.conf

في ملف التكوين المحلي فقط (`odoo_local.conf`):

```ini
[options]
# ... باقي الإعدادات ...

# تحديد الوحدات الأساسية فقط
server_wide_modules = base,web
```

هذا الملف خاص بالبيئة المحلية فقط ولن يؤثر على السيرفر.

---

## 📋 قائمة الوحدات

### ✅ تعمل محلياً وعلى السيرفر

```
- base, web (الأساس)
- sale, purchase, stock (الأعمال)
- account (المحاسبة)
- hr (الموارد البشرية)
- nbs_archive (الأرشفة - مخصص)
- pos_perfume_custom (POS - مخصص)
```

### ⚠️ تعمل على السيرفر فقط

```
- sap_integration (يحتاج: connector, queue_job)
```

**الحل:** لا تثبتها محلياً، الملفات موجودة في المجلد لكن غير مفعلة.

---

## 📁 الملفات

### ملفات التكوين المختلفة

```bash
# السيرفر البعيد
odoo.conf                    # يحتوي على جميع الوحدات

# البيئة المحلية
odoo_local.conf             # يحتوي على الوحدات المتوفرة محلياً فقط
```

### قائمة الاستثناءات

```bash
# .odoo_exclude_modules
# وحدات لا تُثبت محلياً (مرجع فقط)
sap_integration  # Requires: connector, queue_job
```

---

## 🔄 سير العمل

### عند التطوير محلياً:

1. **تثبيت الوحدات المتوفرة فقط:**
   ```bash
   ./venv/bin/python odoo-bin -c odoo_local.conf \
     -i base,web,sale,purchase,stock,account,hr,nbs_archive,pos_perfume_custom \
     --stop-after-init
   ```

2. **تشغيل النظام:**
   ```bash
   ./start_local.sh
   ```

3. **الوحدات غير المثبتة لن تسبب مشاكل** - الملفات موجودة لكن غير مفعلة.

### عند النشر على السيرفر:

1. **عمل push للتغييرات:**
   ```bash
   git add .
   git commit -m "تحديثات"
   git push origin main
   ```

2. **على السيرفر:**
   ```bash
   # جميع الوحدات تعمل بما فيها sap_integration
   # لأن السيرفر لديه المكتبات المطلوبة
   ```

---

## ✅ التحقق من الحل

```bash
# 1. تأكد أن Odoo يعمل محلياً
curl -s -o /dev/null -w "%{http_code}" http://localhost:8070
# يجب أن يعيد: 200

# 2. تأكد أن sap_integration غير مثبتة محلياً
psql lugal_local -c "SELECT name, state FROM ir_module_module WHERE name = 'sap_integration';"
# يجب أن تكون النتيجة فارغة أو state = 'uninstalled'

# 3. تأكد أن الملف الأصلي لم يتغير
git status addons/sap_integration/__manifest__.py
# يجب ألا يظهر في قائمة التغييرات
```

---

## 🎯 الملخص

| الأمر | محلي | سيرفر |
|-------|------|-------|
| تغيير `__manifest__.py` | ❌ لا (يؤثر على الجميع) | ❌ لا |
| عدم تثبيت الوحدة | ✅ نعم | - |
| استخدام `odoo_local.conf` | ✅ نعم | - |
| حذف من قاعدة البيانات المحلية | ✅ نعم | - |

---

## 🚀 النتيجة

- ✅ **محلياً:** النظام يعمل بدون `sap_integration`
- ✅ **على السيرفر:** جميع الوحدات تعمل بما فيها `sap_integration`
- ✅ **لا تعارض:** كل بيئة لها تكوينها الخاص
- ✅ **التطوير سلس:** يمكن العمل على باقي الوحدات بدون مشاكل

---

## 📝 ملاحظات إضافية

### لماذا هذا الحل أفضل؟

1. **لا يؤثر على السيرفر** - كل بيئة مستقلة
2. **سهل الصيانة** - تغيير بسيط في التكوين المحلي
3. **واضح** - من السهل معرفة ما يعمل أين
4. **مرن** - يمكن إضافة/إزالة وحدات بسهولة

### إضافة وحدات جديدة للاستثناء:

إذا كان لديك وحدات أخرى تحتاج مكتبات خاصة:

```bash
# 1. أضفها إلى .odoo_exclude_modules (توثيق فقط)
echo "module_name  # Requires: some_dependency" >> .odoo_exclude_modules

# 2. لا تثبتها محلياً
# (لا تضعها في قائمة -i عند التهيئة)

# 3. احذفها من القاعدة المحلية إذا كانت مثبتة
psql lugal_local -c "DELETE FROM ir_module_module WHERE name = 'module_name';"
```

---

**الخلاصة:** الوحدات موجودة في الكود، لكن غير مفعلة محلياً. السيرفر يستخدمها بشكل طبيعي. ✅
