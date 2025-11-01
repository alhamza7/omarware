# 🔄 إعادة تشغيل Odoo - حل مشكلة صفحة اختيار قاعدة البيانات

## 🎯 **المشكلة:**
- يظهر `http://localhost:8069/web/database/selector`
- يطلب اختيار قاعدة بيانات

## ✅ **تم الحل:**
- تم تحديث `odoo.conf`
- قاعدة البيانات: `lugal`
- تم تثبيت SAP Integration على `lugal`

---

## 🚀 **الخطوات الآن:**

### **1. أوقف Odoo الحالي:**

إذا كان يعمل، اضغط:
```
Ctrl + C
```

أو أغلق نافذة Terminal التي تشغل Odoo.

---

### **2. أعد تشغيل Odoo:**

في Terminal، نفذ:

```bash
cd L:\Lugal-ai
python odoo-bin -c odoo.conf
```

---

### **3. افتح المتصفح:**

```
http://localhost:8069
```

أو:
```
http://192.168.116.211:8069
```

يجب أن يفتح **مباشرة** على قاعدة بيانات `lugal` بدون صفحة اختيار! ✅

---

## 📋 **إذا لم ينجح:**

### **الحل البديل:**

أضف `-d lugal` عند التشغيل:

```bash
python odoo-bin -c odoo.conf -d lugal
```

هذا يجبر Odoo على استخدام قاعدة بيانات `lugal` مباشرة.

---

## ✅ **بعد التشغيل:**

### **اختبر SAP Integration:**

1. اذهب إلى: `Settings > SAP Integration > Backends`

2. أو من Python Code:
   ```
   Settings > Technical > Python Code
   ```

3. جرب:
   ```python
   # التحقق من الموديل
   module = env['ir.module.module'].search([('name', '=', 'sap_integration')])
   print(f"Module State: {module.state}")
   
   # إنشاء Backend
   backend = env['sap.backend'].search([], limit=1)
   if not backend:
       backend = env['sap.backend'].create({
           'name': 'SAP Production',
           'base_url': 'https://your-server:50000/b1s/v1',
           'username': 'your_user',
           'password': 'your_pass',
           'company_db': 'YOUR_DB',
           'active': False,  # غير نشط للاختبار
       })
       print(f"✅ Created backend: {backend.name}")
   else:
       print(f"✅ Found backend: {backend.name}")
   ```

---

## 🔧 **الإعدادات الحالية في odoo.conf:**

```ini
[options]
db_host = localhost
db_port = 5432
db_user = odoo_user
db_password = root
dbfilter = ^lugal.*$
```

هذا يعني:
- سيبحث عن قاعدة بيانات تبدأ بـ `lugal`
- قاعدة البيانات الموجودة: `lugal` ✅

---

## 📊 **قواعد البيانات الموجودة:**

1. ✅ **lugal** - قاعدة البيانات الرئيسية (بها SAP Integration)
2. odoo - قاعدة اختبار
3. test_db - قاعدة اختبار

---

## 🎯 **الخلاصة:**

### **افعل هذا الآن:**

1. **أوقف Odoo** (Ctrl+C)
2. **أعد التشغيل**: `python odoo-bin -c odoo.conf`
3. **افتح المتصفح**: `http://localhost:8069`

يجب أن يعمل مباشرة! ✅

---

## 💡 **نصيحة:**

إذا استمرت المشكلة، احذف ملفات الـ cache:

```bash
# في Terminal
Remove-Item -Recurse -Force odoo/__pycache__
Remove-Item -Recurse -Force addons/__pycache__
```

ثم أعد التشغيل.

---

**🚀 الآن أعد تشغيل Odoo!**

