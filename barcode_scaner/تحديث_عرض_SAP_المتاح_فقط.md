# تحديث عرض كمية SAP - إظهار المتاح فقط

## 📝 الوصف
تم تعديل النظام لإظهار **الكمية المتاحة (Available)** فقط من SAP، بدلاً من عرض:
- الكمية الموجودة (InStock)
- الكمية المحجوزة (Committed)
- الكمية المتاحة (Available)

## 🎯 الكمية المتاحة
الكمية المتاحة = الكمية الموجودة - الكمية المحجوزة

`Available = InStock - Committed`

## ✅ الملفات المعدّلة

### 1. تطبيق الموبايل (Flutter)
**الملف:** `mobile_app_runner/lib/screens/inventory_screen.dart`

#### التعديلات:
- **دايلوج "تم الجرد مسبقاً"** (السطر 198-235): تم إزالة عرض الكمية الموجودة والمحجوزة، والإبقاء على المتاح فقط
- **دايلوج "إضافة كمية"** (السطر 376-410): تم تبسيط العرض لإظهار المتاح فقط

### 2. واجهة الويب (JavaScript)
**الملف:** `public/app.js`

#### التعديلات:
- **دالة openCountDialog** (السطر 148-208): تم تحديث صندوق SAP لإظهار المتاح فقط
- **دالة showAlreadyCountedDialog** (السطر 210-337): تم تحديث دايلوج "تم الجرد مسبقاً" لإظهار المتاح فقط

### 3. ملف الاختبار الرئيسي
**الملف:** `test_sap_web.html`

#### التعديلات:
- **عرض النتائج** (السطر 130-142): تم تحديث عرض كمية SAP لإظهار المتاح فقط بخط أكبر وأوضح

### 4. ملف اختبار التصحيح
**الملف:** `public/test_debug.html`

#### التعديلات:
- **محاكاة Dialog** (السطر 225-233): تم تبسيط العرض لإظهار المتاح فقط

## 🎨 التصميم الجديد

### تطبيق الموبايل
```dart
// صندوق SAP مبسط
Container(
  padding: const EdgeInsets.all(12),
  decoration: BoxDecoration(
    color: Colors.blue.shade50,
    borderRadius: BorderRadius.circular(8),
  ),
  child: Column(
    children: [
      Row(
        children: [
          Icon(Icons.cloud_sync, color: Colors.blue.shade700),
          Text('كمية SAP:'),
        ],
      ),
      Text('المتاح: ${available}', 
        style: TextStyle(
          color: Colors.green.shade700,
          fontWeight: FontWeight.bold,
          fontSize: 15,
        )),
    ],
  ),
)
```

### واجهة الويب
```html
<div style="background: #E3F2FD; border: 1px solid #2196F3; border-radius: 8px; padding: 12px;">
  <div style="display: flex; align-items: center;">
    <span>☁️</span>
    <strong style="color: #1976D2;">كمية SAP:</strong>
  </div>
  <div style="display: flex; justify-content: space-between;">
    <span>✅ الكمية المتاحة:</span>
    <strong style="color: #4CAF50; font-size: 18px;">${available}</strong>
  </div>
</div>
```

## 🔍 كيفية الاختبار

### 1. اختبار تطبيق الموبايل
```bash
cd mobile_app_runner
flutter run
```
- امسح أي صنف بالباركود
- تحقق من ظهور "الكمية المتاحة" فقط في صندوق SAP

### 2. اختبار واجهة الويب
```bash
# تأكد من أن السيرفر يعمل
node src/server.js

# افتح المتصفح على:
http://localhost:3000
```
- ابحث عن أي صنف
- تحقق من ظهور "الكمية المتاحة" فقط

### 3. اختبار صفحة SAP المخصصة
افتح في المتصفح:
```
http://localhost:3000/test_sap_web.html
```
- اضغط على "جلب الكمية من SAP"
- تحقق من ظهور المتاح فقط بخط كبير واضح

## 📊 مثال على النتيجة

**قبل التعديل:**
```
☁️ كمية SAP:
الكمية الموجودة: 100
الكمية المحجوزة: 20
✅ الكمية المتاحة: 80
```

**بعد التعديل:**
```
☁️ كمية SAP:
✅ الكمية المتاحة: 80
```

## 💡 ملاحظات مهمة

1. **البيانات من الباك إند لم تتغير**: السيرفر لا زال يرسل جميع القيم (quantity, committed, available) ولكن الواجهات تعرض المتاح فقط

2. **الكمية المتاحة محسوبة في الباك إند**: في ملف `src/sap_client.js` الكمية المتاحة محسوبة تلقائياً:
   ```javascript
   available: (InStock || 0) - (Committed || 0)
   ```

3. **سهولة الرجوع**: إذا أردت الرجوع لعرض جميع القيم، يمكنك استعادة الكود السابق من Git

## 🚀 الخطوة التالية

إذا أردت تحديث تطبيق الموبايل:
```bash
cd mobile_app_runner
flutter build apk --release
```
سيتم إنشاء ملف APK جديد في:
```
mobile_app_runner/build/app/outputs/flutter-apk/app-release.apk
```

## 📝 التاريخ
- **تاريخ التعديل:** 22 ديسمبر 2025
- **الغرض:** تبسيط واجهة المستخدم وإظهار المعلومات الأهم فقط (الكمية المتاحة)





