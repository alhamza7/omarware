# حل المشاكل - Troubleshooting

## ❌ المشكلة: QR Code لا يظهر في عناصر التصميم

### ✅ الحلول:

#### 1. تأكد من تفعيل QR في القالب:
```
1. افتح القالب
2. تبويب "Display Options"
3. فعّل ☑️ "Show QR Code"
4. احفظ
5. أعد فتح Visual Designer
```

#### 2. تحقق من Console:
```
في المصمم المرئي:
1. اضغط F12 (Developer Tools)
2. تبويب "Console"
3. ابحث عن:
   - "Show QR: true"
   - "Adding QR Code element"
   
إذا رأيت "Show QR: false":
   → القالب لم يُحفظ بشكل صحيح
   → أعد تفعيل "Show QR" واحفظ
```

#### 3. Upgrade الموديول:
```
التطبيقات → Product Label Designer → Upgrade
```

#### 4. امسح الـ Cache:
```bash
# احذف __pycache__
rm -rf addons/product_label_designer/__pycache__
rm -rf addons/product_label_designer/*/__pycache__

# أعد تشغيل Odoo
```

---

## ❌ المشكلة: الصور المرفوعة لا تظهر

### ✅ الحلول:

#### 1. تحقق من حجم الصورة:
```
الحد الأقصى: 5MB
إذا كانت أكبر:
- قلل الدقة
- استخدم ضغط PNG/JPG
```

#### 2. تحقق من الصيغة:
```
الصيغ المدعومة:
✅ PNG
✅ JPG/JPEG
✅ GIF
❌ SVG (غير مدعوم)
❌ BMP (غير مدعوم)
```

#### 3. تحقق من رسائل الخطأ:
```
F12 → Console → ابحث عن أخطاء حمراء

إذا رأيت "Failed to upload":
- تحقق من حجم الملف
- تحقق من الصيغة
- جرب صورة أخرى
```

#### 4. جرب من النموذج العادي:
```
بدلاً من المصمم، جرب من:
1. Label Templates → افتح القالب
2. تبويب "Images"
3. ارفع Background/Logo هنا
4. احفظ
5. أعد فتح المصمم
```

#### 5. تحقق من الصلاحيات:
```
تأكد من:
- أنت مسجل دخول كمستخدم لديه صلاحيات
- المجموعة: Stock User أو Stock Manager
```

---

## ❌ المشكلة: المصمم المرئي لا يفتح

### ✅ الحلول:

#### 1. تحقق من URL:
```
يجب أن يكون:
http://localhost:8069/label_designer/[template_id]

مثال:
http://localhost:8069/label_designer/1
```

#### 2. تحقق من Controller:
```python
# في controllers/label_designer.py
# تأكد من وجود route:

@http.route('/label_designer/<int:template_id>', type='http', auth='user', website=True)
def label_designer(self, template_id, **kwargs):
    ...
```

#### 3. أعد تشغيل Odoo:
```bash
# أوقف Odoo
Ctrl+C

# شغّل مرة أخرى
./odoo-bin -c odoo.conf
```

---

## ❌ المشكلة: العناصر لا تتحرك

### ✅ الحلول:

#### 1. تحقق من Console:
```
F12 → Console
ابحث عن:
- أخطاء JavaScript حمراء
- "labelDesigner is not defined"
```

#### 2. تأكد من تحميل JavaScript:
```
F12 → Network → Reload (F5)
ابحث عن:
- label_designer.js (يجب أن يكون 200 OK)
```

#### 3. امسح Cache المتصفح:
```
Ctrl+Shift+Delete → Clear Cache → Reload
```

---

## ❌ المشكلة: الحفظ لا يعمل

### ✅ الحلول:

#### 1. تحقق من Network:
```
F12 → Network → حرك عنصر
ابحث عن:
- Request إلى /label_designer/save_positions
- الحالة يجب أن تكون 200 OK
```

#### 2. تحقق من Console:
```
ابحث عن:
- "Positions saved successfully" ✅
- أو أخطاء حمراء ❌
```

#### 3. تحقق من الصلاحيات:
```
الـ Controller يحتاج:
auth='user' ✅
المستخدم مسجل دخول ✅
```

---

## ❌ المشكلة: الطباعة لا تعمل

### ✅ الحلول:

#### 1. تحقق من وجود بيانات المنتج:
```
المنتج يجب أن يحتوي:
- اسم ✅
- كود (اختياري)
- سعر ✅
- باركود (للباركود)
- foreign_name (للاسم الأجنبي)
```

#### 2. تحقق من القالب:
```
القالب يجب أن:
- يكون نشطاً (Active = True)
- له عرض وارتفاع صحيح
- العناصر المطلوبة مفعّلة
```

#### 3. تحقق من نوع الطباعة:
```
Single Labels:
- يحتاج paper format 80x60mm

A4 Sheet:
- يحتاج paper format A4
```

---

## ❌ المشكلة: A4 Sheet - الملصقات متداخلة

### ✅ الحلول:

#### 1. تحقق من الإعدادات:
```
في القالب → A4 Layout:

للملصق 80×60mm:
Labels per Row: 2
Labels per Column: 4
Margin: 2mm

للملصق 50×30mm:
Labels per Row: 4
Labels per Column: 9
Margin: 2mm
```

#### 2. احسب المساحة:
```
عرض ورقة A4 = 210mm
عرض ملصق واحد = 80mm
Margin = 2mm

(80mm × 2) + (2mm × 3) = 166mm ✅ (يناسب A4)

إذا كان أكبر من 210mm:
- قلل عدد الأعمدة
- أو قلل حجم الملصق
```

---

## 🔍 Debug Mode

### تفعيل وضع التصحيح:

```javascript
// في Console (F12)
window.labelDesigner.templateData
// سيعرض جميع البيانات

window.labelDesigner.canvas
// سيعرض الـ Canvas

window.labelDesigner.savePositions()
// حفظ يدوي
```

### اختبار رفع صورة:

```javascript
// في Console
const input = document.getElementById('background-upload');
input.click();
// يجب أن يفتح نافذة اختيار ملف

// بعد اختيار صورة، راقب:
// "background uploaded successfully" ✅
```

---

## ✅ قائمة التحقق الكاملة:

قبل استخدام المصمم، تأكد من:

- [ ] الموديول مثبت ومحدّث (Upgrade)
- [ ] القالب محفوظ بشكل صحيح
- [ ] "Show QR Code" مفعّل إذا أردت QR
- [ ] "Show Logo" مفعّل إذا أردت شعار
- [ ] صورة الخلفية/الشعار أقل من 5MB
- [ ] الصيغة: PNG أو JPG
- [ ] Cache المتصفح تم مسحه (Ctrl+Shift+Delete)
- [ ] F12 Console لا يعرض أخطاء

---

## 🆘 حل سريع شامل:

إذا لم يعمل شيء:

```bash
# 1. أوقف Odoo
Ctrl+C

# 2. احذف Cache
rm -rf addons/product_label_designer/__pycache__
rm -rf addons/product_label_designer/*/__pycache__

# 3. شغّل Odoo مع upgrade
./odoo-bin -c odoo.conf -u product_label_designer -d your_db

# 4. في المتصفح:
Ctrl+Shift+Delete → Clear cache
F5 → Reload

# 5. افتح المصمم مرة أخرى
```

---

## 📞 ما زالت المشكلة؟

### أرسل لي:

1. لقطة شاشة من F12 → Console
2. لقطة شاشة من المصمم
3. لقطة شاشة من القالب (تبويب Display Options)

وسأساعدك فوراً! 🚀



