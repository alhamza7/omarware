# تثبيت نظيف - Clean Installation

## ⚠️ لحل جميع المشاكل

اتبع هذه الخطوات **بالترتيب**:

---

## 🔴 الخطوة 1: إلغاء التثبيت الكامل

```
1. التطبيقات → ابحث "Product Label"
2. إذا كان مثبتاً: اضغط "Uninstall"
3. تأكد من الحذف
4. انتظر حتى ينتهي
```

---

## 🔴 الخطوة 2: إعادة تشغيل Odoo

```bash
# أوقف Odoo تماماً
Ctrl+C

# احذف كل الـ cache
Remove-Item -Path "addons\product_label_designer\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "addons\product_label_designer\*\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue

# شغّل Odoo من جديد
./odoo-bin -c odoo.conf
```

---

## 🔴 الخطوة 3: مسح Cache المتصفح

```
في المتصفح:
1. Ctrl+Shift+Delete
2. اختر "Cached images and files"
3. Clear
4. أغلق المتصفح تماماً
5. افتحه مرة أخرى
```

---

## 🔴 الخطوة 4: تثبيت نظيف

```
1. سجل دخول إلى Odoo
2. التطبيقات → Update Apps List
3. انتظر حتى ينتهي
4. ابحث "Product Label Designer"
5. اضغط "Install" (وليس Upgrade)
6. انتظر حتى ينتهي التثبيت
```

---

## ✅ الخطوة 5: التحقق

بعد التثبيت، تحقق من:

```
1. المخزون → Product Labels
   يجب أن ترى:
   ✅ Quick Print
   ✅ Label Templates
   ✅ Select Products

2. افتح أي منتج
   يجب أن ترى:
   ✅ زر "Print Label"
   ✅ حقل "Foreign Name"

3. Label Templates → Create
   يجب أن ترى كل التبويبات:
   ✅ Display Options
   ✅ A4 Layout
   ✅ Visual Designer
   ✅ Images
```

---

## 🎯 الخطوة 6: اختبار سريع

```
1. Label Templates → Create
   Name: Test Template
   Width: 80
   Height: 60
   
2. Display Options:
   ☑️ Show Name
   ☑️ Show Code
   ☑️ Show QR
   
3. Save

4. Quick Print → اختر Test Template
   Add All Products
   Print Mode: Single
   Print Now

5. يجب أن يفتح PDF! ✅
```

---

## 🐛 إذا ما زالت المشكلة:

### Debug في المتصفح:

```
1. افتح Quick Print
2. F12 → Console
3. ابحث عن أخطاء حمراء
4. أرسل لي لقطة شاشة
```

### تحقق من Log:

```bash
# في terminal حيث يعمل Odoo
# شاهد آخر الأخطاء
tail -f odoo.log
```

---

## 🔄 البديل: تثبيت من سطر الأوامر

```bash
# 1. أوقف Odoo
Ctrl+C

# 2. احذف من قاعدة البيانات
psql your_database -c "DELETE FROM ir_module_module WHERE name='product_label_designer';"

# 3. شغّل مع install
./odoo-bin -c odoo.conf -i product_label_designer -d your_database --stop-after-init

# 4. شغّل Odoo عادي
./odoo-bin -c odoo.conf

# 5. F5 في المتصفح
```

---

## ✅ قائمة التحقق:

- [ ] Uninstall الموديول القديم
- [ ] إعادة تشغيل Odoo
- [ ] حذف __pycache__
- [ ] مسح cache المتصفح
- [ ] Update Apps List
- [ ] Install من جديد
- [ ] تحقق من القوائم
- [ ] اختبار طباعة

---

**اتبع الخطوات بالترتيب وأخبرني النتيجة!** 🚀



