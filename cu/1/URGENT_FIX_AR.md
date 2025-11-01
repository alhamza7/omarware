# 🚨 إصلاح عاجل - خطأ Sale Order
## Urgent Fix - Sale Order Error

⏰ **عاجل**: يجب تطبيقه فوراً  
🐛 **الخطأ**: RPC_ERROR عند فتح Sales Order

---

## ❌ الخطأ الذي تراه

```
ValueError: Wrong @depends on '_compute_price_unit'
Dependency field 'product_uom' not found in model sale.order.line.
```

---

## ✅ الإصلاح (دقيقة واحدة!)

### الطريقة السريعة:

```bash
# شغّل هذا الملف
quick_fix_and_restart.bat
```

سيقوم تلقائياً بـ:
1. ترقية الموديول
2. إعادة تشغيل Odoo

---

## 🔧 ما تم إصلاحه؟

### المشكلة
كان هناك **تعارض** بين ملفين:
- `sale_order_line.py` (القديم)
- `sale_order_line_smart.py` (الجديد)

كلاهما يعيد تعريف نفس المنهج!

### الحل
✅ تم تعطيل `sale_order_line.py` القديم  
✅ الاحتفاظ بـ `sale_order_line_smart.py` فقط (النظام الذكي)  
✅ إصلاح اسم الحقل: `product_uom` → `product_uom_id`

---

## 🚀 الخطوات (إذا لم تستخدم .bat)

### 1. أوقف Odoo
```
اضغط Ctrl+C في terminal
```

### 2. ترقية الموديول
```bash
python odoo-bin -c odoo.conf -u uom_in_pricelist -d lugal --stop-after-init
```

### 3. أعد تشغيل Odoo
```bash
python odoo-bin -c odoo.conf
```

### 4. اختبر
```
1. افتح المتصفح
2. Ctrl+F5 (تحديث قوي)
3. Sales → Orders → Create
4. ✅ يجب أن يعمل الآن!
```

---

## ✅ التحقق من الإصلاح

### علامات النجاح:

```
✅ لا خطأ RPC_ERROR
✅ يمكن فتح Sales Order بدون مشاكل
✅ يمكن اختيار منتج
✅ يمكن تغيير UoM
✅ السعر يتغير تلقائياً
```

### إذا ما زال الخطأ موجود:

```
1. تأكد من إيقاف Odoo تماماً
2. احذف __pycache__:
   rm -rf addons/uom_in_pricelist/models/__pycache__
3. أعد الترقية
4. أعد التشغيل
```

---

## 🎯 ما الجديد الآن؟

### النظام الذكي يعمل!

```python
# عند اختيار منتج في Sales Order:

1. يبحث عن سعر محدد للـ UoM
   → موجود؟ ✅ يستخدمه مباشرة

2. غير موجود؟
   → 🧮 يحسب من السعر الأساسي × factor

3. النتيجة:
   → ✅ دائماً هناك سعر صحيح!
```

---

## 📋 الخلاصة

```
المشكلة: ❌ تعارض في الملفات + حقل خاطئ
الإصلاح: ✅ تعطيل الملف القديم + تصحيح الحقل
الوقت: ⏱️ دقيقة واحدة
الحالة: ✅ جاهز للاستخدام
```

---

## 🚀 ابدأ الآن

```bash
# أسرع طريقة:
quick_fix_and_restart.bat

# أو يدوياً:
# 1. Ctrl+C (إيقاف)
# 2. python odoo-bin -c odoo.conf -u uom_in_pricelist -d lugal --stop-after-init
# 3. python odoo-bin -c odoo.conf
```

---

**الحالة**: 🔥 **عاجل - نفّذ الآن!**  
**الوقت**: ⏱️ **1 دقيقة فقط**  
**النتيجة**: ✅ **نظام تسعير ذكي يعمل بكفاءة**



