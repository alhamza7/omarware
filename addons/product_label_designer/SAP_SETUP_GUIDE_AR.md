# دليل إعداد طباعة الليبلات من SAP
## نظام طباعة ليبلات المنتجات المتكامل مع SAP Business One

---

## نظرة عامة

يستخدم هذا النظام مودل **SAP Integration** الموجود مسبقاً في النظام للاتصال بـ SAP Business One والحصول على بيانات المنتجات عن طريق الباركود.

### الميزات الرئيسية:
✅ استخدام نظام الاتصال الموجود بـ SAP  
✅ البحث عن المنتجات في SAP عن طريق Barcode أو ItemCode  
✅ عرض اسم المنتج ووحدة القياس من SAP مباشرة  
✅ إنشاء أو تحديث المنتج في Odoo تلقائياً  
✅ طباعة فورية عند مسح الباركود  
✅ تصميم مخصص للليبل مع إمكانية وضع عناصر SAP في أي مكان  

---

## خطوات الإعداد

### 1. التأكد من تفعيل مودل SAP Integration

تأكد من أن مودل `sap_integration` مثبت ومُفعّل في نظامك:

```
الإعدادات > Apps > ابحث عن "SAP Integration"
```

### 2. إعداد SAP Backend

انتقل إلى:
```
SAP Integration > Configuration > SAP Backends
```

أنشئ أو تحقق من وجود **SAP Backend** نشط مع المعلومات التالية:

- **Name**: اسم للاتصال (مثل: "SAP Production Server")
- **Service Layer URL**: رابط SAP Service Layer API  
  مثال: `https://your-sap-server.com:50000/b1s/v1`
- **Username**: اسم المستخدم في SAP
- **Password**: كلمة المرور
- **Company Database**: اسم قاعدة بيانات الشركة في SAP
- **Active**: ✅ مُفعّل

اضغط **Test Connection** للتأكد من نجاح الاتصال.

### 3. إعداد قالب الليبل (Label Template)

انتقل إلى:
```
Inventory > Product Labels > Label Templates
```

1. **أنشئ قالباً جديداً** أو **عدّل قالباً موجوداً**
2. انتقل إلى تبويب **"SAP Integration"**
3. فعّل **"Enable SAP Mode"**
4. اختر **SAP Backend** من القائمة المنسدلة
5. حدد ما إذا كنت تريد عرض **وحدة القياس من SAP** (Show SAP Unit of Measure)
6. إذا فعلت عرض وحدة القياس، اختر **تنسيق العرض**:
   - **Full Name**: الاسم الكامل لوحدة القياس
   - **Code Only**: الكود فقط
   - **Abbreviation**: الاختصار

### 4. تصميم موضع العناصر على الليبل

في نفس الصفحة، قسم **"SAP Element Positions & Styling"**:

#### لاسم المنتج من SAP:
- **SAP Name X Position**: الموضع الأفقي (mm)
- **SAP Name Y Position**: الموضع العمودي (mm)
- **SAP Name Width**: العرض (mm)
- **SAP Name Height**: الارتفاع (mm)
- **SAP Name Font Size**: حجم الخط
- **SAP Name Alignment**: محاذاة النص (يمين/وسط/يسار)
- **SAP Name Bold**: غامق
- **SAP Name Italic**: مائل

#### لوحدة القياس من SAP (إذا كانت مفعلة):
- **SAP UoM X Position**: الموضع الأفقي (mm)
- **SAP UoM Y Position**: الموضع العمودي (mm)
- **SAP UoM Width**: العرض (mm)
- **SAP UoM Height**: الارتفاع (mm)
- **SAP UoM Font Size**: حجم الخط
- **SAP UoM Alignment**: محاذاة النص
- **SAP UoM Bold**: غامق
- **SAP UoM Italic**: مائل

---

## استخدام النظام

### طريقة 1: الطباعة المستمرة (Continuous Printing)

1. انتقل إلى:
   ```
   Inventory > Product Labels > SAP Label Printer (Barcode Scan)
   ```

2. اختر **Label Template** المُعد للـ SAP

3. حدد **عدد النسخ** (Number of Copies)

4. اضغط في حقل **"Scan Barcode"** وامسح الباركود بقارئ الباركود

5. سيقوم النظام تلقائياً بـ:
   - البحث عن المنتج في SAP عن طريق الباركود
   - جلب اسم المنتج ووحدة القياس
   - إنشاء أو تحديث المنتج في Odoo
   - طباعة الليبل مباشرة

6. يمكنك الاستمرار في المسح والطباعة بدون توقف

### طريقة 2: الطباعة من Odoo

إذا كان المنتج موجوداً بالفعل في Odoo:

1. افتح المنتج من `Inventory > Products`
2. اضغط **"Print Label"**
3. اختر القالب المُعد للـ SAP
4. سيتم جلب أحدث البيانات من SAP وطباعة الليبل

---

## كيف يعمل النظام؟

### 1. عند مسح الباركود:

```
Barcode Scanner → Odoo Web Interface
   ↓
Odoo Template.get_sap_product_info(barcode)
   ↓
SAP Backend Connection (من مودل sap_integration)
   ↓
SAP Service Layer API: GET /Items?$filter=BarCode eq '{barcode}' or ItemCode eq '{barcode}'
   ↓
SAP Response: ItemCode, ItemName, SalesUnit, SalesUnitMeasure, Price, etc.
   ↓
Odoo: إنشاء أو تحديث product.product
   ↓
Odoo: طباعة الليبل PDF
```

### 2. البيانات المحفوظة في Odoo:

عند جلب المنتج من SAP، يتم حفظ:
- `name`: اسم المنتج
- `default_code`: ItemCode من SAP
- `barcode`: الباركود الممسوح
- `list_price`: السعر من SAP
- `sap_product_name`: اسم المنتج من SAP (للاحتفاظ به)
- `sap_uom`: وحدة القياس من SAP
- `last_sap_sync`: تاريخ آخر تحديث من SAP

---

## استكشاف الأخطاء

### ❌ "No SAP backend configured"
**الحل**: تأكد من:
1. اختيار SAP Backend في إعدادات القالب
2. أن الـ Backend نشط (Active)

### ❌ "Backend is not connected"
**الحل**: 
1. افتح SAP Backend من `SAP Integration > Configuration > SAP Backends`
2. اضغط **Test Connection**
3. تحقق من صحة:
   - Service Layer URL
   - Username & Password
   - Company Database

### ❌ "Product not found in SAP"
**الحل**:
- تأكد من أن الباركود موجود في SAP في حقل `BarCode` أو `ItemCode`
- تحقق من أن المنتج نشط (Valid = 'Y') في SAP

### ❌ "Error connecting to SAP"
**الحل**:
1. تحقق من اتصال الشبكة بين Odoo Server و SAP Server
2. تحقق من أن SAP Service Layer يعمل
3. راجع السجلات (Logs) في Odoo للمزيد من التفاصيل

---

## الفرق بين النظام القديم والنظام الحالي

### ❌ النظام القديم (تم إزالته):
- كان يستخدم حقول `sap_api_url` و `sap_api_key` مباشرة
- يتطلب إعداد API منفصل
- لا يستفيد من مودل SAP Integration الموجود

### ✅ النظام الحالي (محدث):
- يستخدم `sap_backend_id` من مودل `sap_integration`
- يستفيد من نظام الاتصال الموجود مع SAP
- إدارة موحدة لجميع اتصالات SAP في النظام
- Connection pooling وإعادة استخدام الجلسات
- دعم أفضل للأخطاء وإعادة المحاولة

---

## ملاحظات مهمة

1. **الأمان**: تأكد من أن مستخدمي Odoo لديهم الصلاحيات المناسبة للوصول إلى SAP Integration
2. **الأداء**: نظام الاتصال يستخدم Connection Pool لتحسين الأداء وتقليل زمن الاستجابة
3. **التزامن**: يتم تحديث بيانات المنتج في Odoo في كل مرة يتم فيها مسح الباركود
4. **الباركود**: يمكن للنظام البحث في SAP عن طريق حقل `BarCode` أو `ItemCode`

---

## الدعم الفني

إذا واجهت أي مشاكل:

1. راجع السجلات (Logs) في Odoo:
   ```
   Settings > Technical > Logging
   ```
   ابحث عن رسائل تحتوي على `SAP` أو `label`

2. تحقق من حالة SAP Backend:
   ```
   SAP Integration > Configuration > SAP Backends
   ```

3. تأكد من أن مودل `sap_integration` مُحدث ويعمل بشكل صحيح

---

**تم التحديث**: ديسمبر 2024  
**الإصدار**: 2.0 - متكامل مع sap_integration module  
**المطور**: Lugal AI

