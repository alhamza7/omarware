# 🔧 حل مشكلة عدم ظهور التغييرات في POS
# Troubleshooting: Changes Not Showing in POS

## ❌ المشكلة / Problem

فتحت POS ولم تظهر أي تغييرات (لا أسعار بالدينار ولا أسماء عربية)

---

## ✅ الحل الكامل / Complete Solution

### الخطوة 1: تأكد أن Odoo يعمل

```bash
cd L:\Lugal-ai
python odoo-bin -c odoo.conf
```

انتظر حتى ترى:
```
INFO lugal odoo.service.server: HTTP service (werkzeug) running on ...
```

---

### الخطوة 2: افتح المتصفح بوضع التصفح الخفي (Incognito)

**مهم جداً!** افتح نافذة جديدة incognito/private:

- **Chrome:** Ctrl+Shift+N
- **Edge:** Ctrl+Shift+P  
- **Firefox:** Ctrl+Shift+P

ثم اذهب إلى:
```
http://localhost:8069
```

---

### الخطوة 3: سجّل دخول وافتح POS

1. سجّل دخول بحسابك
2. اذهب: `Point of Sale`
3. افتح جلسة جديدة: `New Session`

---

### الخطوة 4: أضف منتج بالاسم العربي أولاً

**مهم:** الميزات تظهر فقط للمنتجات التي لها اسم عربي!

1. اذهب: `Inventory → Products → Create`
2. املأ:
   ```
   Product Name: Test Perfume
   Arabic Name: عطر تجريبي
   Sales Price: 100.00
   Available in POS: ✓ (checked)
   ```
3. احفظ

---

### الخطوة 5: ارجع لـ POS وحدّث

1. في POS، اضغط **F5** أو **Ctrl+Shift+R**
2. ابحث عن المنتج "Test Perfume"
3. أضفه للطلب

**يجب أن ترى:**
```
Test Perfume
عطر تجريبي      ← الاسم العربي
$100.00
130,000 IQD     ← السعر بالدينار
```

---

## 🔍 إذا لم تظهر بعد / If Still Not Showing

### الحل 1: تحديث الوحدة يدوياً

```bash
cd L:\Lugal-ai
python odoo-bin -c odoo.conf -d lugal -u pos_perfume_custom --stop-after-init
```

ثم شغّل Odoo من جديد

---

### الحل 2: تفعيل Developer Mode

1. اذهب: `Settings → General Settings → Developer Tools`
2. فعّل: `Activate the developer mode`
3. ثم: `Regenerate Assets Bundles`
4. أعد فتح POS

---

### الحل 3: فحص Console للأخطاء

في المتصفح:
1. اضغط `F12` لفتح Developer Tools
2. اذهب لتبويب `Console`
3. ابحث عن أخطاء (Errors) باللون الأحمر
4. يجب أن ترى:
   ```
   POS Perfume Custom: Module loaded successfully! IQD support enabled.
   ```

إذا رأيت هذه الرسالة = الوحدة تعمل! ✅

---

### الحل 4: تحقق من تفعيل المنتج في POS

المنتج يجب أن يكون:
- ✅ `Available in POS` مُفعّل
- ✅ له `Arabic Name`
- ✅ له سعر (`Sales Price`)

---

## 📋 قائمة تحقق سريعة / Quick Checklist

- [ ] Odoo يعمل على localhost:8069
- [ ] الوحدة مثبتة (pos_perfume_custom)
- [ ] فتحت المتصفح في وضع incognito
- [ ] أنشأت منتج جديد بـ Arabic Name
- [ ] فعّلت "Available in POS" للمنتج
- [ ] ضغطت F5 في POS بعد إضافة المنتج
- [ ] فحصت Console ورأيت رسالة النجاح

---

## 🎯 اختبار سريع / Quick Test

قم بإنشاء منتج تجريبي:

```python
# في Odoo shell أو من Products UI:
Product Name: Test
Arabic Name: تجربة  
Sales Price: 10.00
Available in POS: True
```

افتح POS → أضف المنتج → يجب أن ترى:
```
Test
تجربة
$10.00
13,000 IQD
```

---

## 💡 ملاحظات مهمة / Important Notes

1. **الأسماء العربية اختيارية** - إذا لم تضف اسم عربي، لن يظهر شيء إضافي (وهذا طبيعي)

2. **السعر بالدينار يظهر دائماً** - حتى بدون اسم عربي

3. **التحويل تلقائي** - 1 USD = 1,300 IQD

4. **التغييرات تظهر في:**
   - سطور الطلب (Orderlines)
   - المجموع الكلي (Total)

---

## 🆘 إذا استمرت المشكلة

شغّل هذا السكريبت للتشخيص الكامل:

```bash
cd L:\Lugal-ai
python verify_pos_installation.py
```

يجب أن ترى:
```
State: installed ✓
Version: 19.0.1.0.0 ✓
```

---

## 📞 تواصل للدعم

إذا جربت كل الحلول ولم تنجح:

1. افحص ملف السجل:
   ```bash
   Get-Content L:\Lugal-ai\odoo.log -Tail 100
   ```

2. ابحث عن أخطاء تحتوي على "perfume" أو "assets"

---

**آخر تحديث:** 23 أكتوبر 2025

