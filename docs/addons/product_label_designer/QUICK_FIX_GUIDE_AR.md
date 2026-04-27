# دليل الإصلاح السريع ⚡

## 🔧 لحل مشكلة QR والصور

### الخطوة 1: Upgrade الموديول (مهم جداً!)

```
1. التطبيقات → ابحث "Product Label"
2. اضغط "Upgrade" ⬆️ (وليس Install)
3. انتظر حتى ينتهي
```

---

### الخطوة 2: تفعيل QR Code

```
1. المخزون → Product Labels → Label Templates
2. افتح القالب (أو أنشئ واحد جديد)
3. تبويب "Display Options"
4. فعّل ☑️ "Show QR Code"
5. احفظ (Save)
```

---

### الخطوة 3: افتح المصمم المرئي

```
1. نفس القالب
2. تبويب "Visual Designer"
3. اضغط "Open Visual Designer"
4. شاشة جديدة ستفتح
```

---

### الخطوة 4: تحقق من Console

```
في المصمم المرئي:
1. اضغط F12
2. تبويب "Console"
3. يجب أن ترى:

=== Template Data Loaded ===
Template ID: 1
Show QR: true           ← يجب أن تكون true
Show Logo: true
Has Background: false
Has Logo Image: false
===========================

ثم:

Template Data: {...}
Show QR: true           ← مرة أخرى true
Total elements to create: X
Creating element: qr-code QR Code  ← يجب أن ترى هذا!
```

**إذا كان Show QR: false:**
- ارجع للقالب
- فعّل Show QR Code
- احفظ
- Upgrade الموديول مرة أخرى

---

### الخطوة 5: رفع الصور

في Sidebar (الشريط الجانبي):

#### 🖼️ Background:
```
1. اضغط "Upload Background"
2. اختر صورة (PNG/JPG، أقل من 5MB)
3. انتظر قليلاً
4. يجب أن ترى alert: "Background uploaded successfully!"
5. الصورة تظهر في معاينة
6. الخلفية تتغير في Canvas مباشرة
```

#### 🏷️ Logo:
```
1. تأكد من تفعيل "Show Logo" في القالب
2. اضغط "Upload Logo"
3. اختر صورة
4. alert: "Logo uploaded successfully!"
5. يظهر في Canvas
6. يمكنك سحبه وتغيير حجمه
```

---

## ✅ قائمة التحقق:

قبل فتح المصمم، تأكد:

- [ ] **Upgrade** الموديول (مهم!)
- [ ] القالب **محفوظ** بعد التعديل
- [ ] **Show QR** مفعّل (إذا أردت QR)
- [ ] **Show Logo** مفعّل (إذا أردت شعار)
- [ ] الصورة **أقل من 5MB**
- [ ] الصيغة: **PNG أو JPG**

---

## 🐛 Debug:

### افتح Console (F12) وشغّل:

```javascript
// 1. تحقق من البيانات
console.log(window.templateData);

// 2. تحقق من المصمم
console.log(window.labelDesigner);

// 3. تحقق من العناصر
window.labelDesigner.canvas.querySelectorAll('.draggable-element').forEach(el => {
    console.log(el.dataset.id, el.dataset.label);
});

// يجب أن ترى:
// product-name Product Name
// qr-code QR Code  ← إذا كان مفعّل
// barcode Barcode
// ...إلخ
```

---

## 🔄 إذا ما زالت المشكلة:

### الحل النهائي:

```bash
# 1. أوقف Odoo تماماً
Ctrl+C

# 2. احذف كل الـ cache
rm -rf addons/product_label_designer/__pycache__
rm -rf addons/product_label_designer/models/__pycache__
rm -rf addons/product_label_designer/wizard/__pycache__
rm -rf addons/product_label_designer/controllers/__pycache__

# 3. Uninstall الموديول من الواجهة
التطبيقات → Product Label Designer → Uninstall

# 4. شغّل Odoo
./odoo-bin -c odoo.conf

# 5. Install من جديد
التطبيقات → Update Apps List → Install

# 6. في المتصفح
Ctrl+Shift+Delete → Clear cache → Reload
```

---

## 📸 أرسل لي لقطة شاشة من:

1. **F12 → Console** (في المصمم)
2. **القالب** (تبويب Display Options)
3. **المصمم** (الشاشة الكاملة)

وسأساعدك فوراً! 🚀

---

## ⚡ اختصار سريع:

```
1. Upgrade الموديول
2. فعّل Show QR في القالب
3. احفظ
4. افتح المصمم
5. F12 → شاهد Console
6. يجب أن ترى QR في القائمة!
```

---

**الكود تم تحديثه الآن وجاهز!** ✅



