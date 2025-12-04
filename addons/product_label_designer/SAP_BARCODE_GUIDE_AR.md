# دليل نظام طباعة الليبلات مع SAP - استخدام الباركودات الفرعية

## 📋 المحتويات

1. [نظرة عامة](#نظرة-عامة)
2. [مزامنة البيانات من SAP](#مزامنة-البيانات-من-sap)
3. [استخدام الباركودات الفرعية](#استخدام-الباركودات-الفرعية)
4. [طباعة الليبلات](#طباعة-الليبلات)

---

## 🎯 نظرة عامة

### المشكلة التي تم حلها

في **SAP Business One 10**، لا يمكن البحث عن الباركودات الفرعية (Sub-unit barcodes) مباشرة عبر الـ OData API لأن:
- `ItemBarCodeCollection` ليس navigation property
- لا يمكن استخدام `$expand` معه
- جدول `OBCD` غير متاح عبر `/SQLQuery`

### الحل المطبق ✅

**نظام مزامنة وتخزين محلي (Sync & Cache)**:

1. ✅ مزامنة دورية لجميع المنتجات من SAP
2. ✅ تخزين الباركودات الفرعية في Odoo
3. ✅ بحث سريع محلي عند مسح الباركود
4. ✅ تحديث تلقائي من SAP

---

## 🔄 مزامنة البيانات من SAP

### الخطوة 1: تشغيل المزامنة الكاملة

```
Inventory → Configuration → SAP Product Migration
```

1. افتح المعالج (Wizard)
2. حدد الخيارات:
   - ✅ **Stage 1: Import UoM Groups**
   - ✅ **Stage 2: Import Products**
   - ✅ **Stage 3: Import Pricelists** (اختياري)
   - ✅ **Stage 4: Import Warehouse Info** (اختياري)

3. اضغط **Run Complete Migration**

### الخطوة 2: مراقبة التقدم

- المعالج سيعرض:
  - نسبة الإنجاز (%)
  - عدد المنتجات المستوردة
  - أي أخطاء

### الخطوة 3: التحقق من الباركودات البديلة

```
Inventory → Products → [اختر منتج] → Alternative Barcodes
```

---

## 📦 استخدام الباركودات الفرعية

### عرض الباركودات البديلة لمنتج

1. افتح المنتج
2. انتقل إلى تبويب **Alternative Barcodes**
3. ستشاهد:
   - الباركود
   - وحدة القياس (UoM)
   - تاريخ آخر مزامنة

### إضافة باركود بديل يدوياً

```xml
Product → Alternative Barcodes → Add a line
```

أدخل:
- **Barcode**: الباركود الفرعي
- **UoM Name**: اسم وحدة القياس (مثل: "كارتون")
- **Active**: ✅

---

## 🖨️ طباعة الليبلات

### طريقة 1: من واجهة SAP Printer

```
Inventory → Product Labels → SAP Label Printer (Barcode Scan)
```

1. افتح الواجهة
2. امسح الباركود (رئيسي أو فرعي)
3. النظام سيبحث:
   - أولاً في Odoo Cache (خلال آخر ساعة)
   - ثانياً في SAP مباشرة
4. سيتم طباعة الليبل تلقائياً

### طريقة 2: من قائمة المنتجات

```
Inventory → Products → [اختر منتج] → Print → Product Label
```

---

## ⚙️ الإعدادات المتقدمة

### تكرار المزامنة التلقائية

```
Settings → Technical → Scheduled Actions → SAP Product Sync
```

يمكنك ضبط:
- **Execute Every**: كل كم من الوقت (مثل: يومياً)
- **Next Execution Date**: متى سيتم التشغيل القادم

### إعدادات الـ Template

```
Inventory → Configuration → Product Label Templates
```

في تبويب **SAP Integration**:
- ✅ **Enable SAP Mode**
- **SAP Backend**: اختر الـ backend المطلوب
- **Show SAP UoM**: عرض وحدة القياس من SAP

---

## 🔍 استكشاف الأخطاء

### المنتج غير موجود

**المشكلة**: `Product with barcode X not found`

**الحل**:
1. تأكد من وجود المنتج في SAP
2. شغل المزامنة من جديد
3. تحقق من أن الباركود صحيح

### الباركود الفرعي لا يعمل

**المشكلة**: لا يجد الباركود الفرعي

**الحل**:
1. تحقق من `Alternative Barcodes` للمنتج
2. تأكد من أن `Active = ✅`
3. إذا لم يكن موجوداً، شغل المزامنة
4. أو أضفه يدوياً

### بطء البحث

**الحل**:
- المزامنة الدورية تحفظ البيانات محلياً
- البحث الأول قد يكون بطيئاً (يتصل بـ SAP)
- البحث الثاني سيكون سريعاً (من Cache)
- Cache صالح لمدة ساعة

---

## 📊 معلومات تقنية

### نموذج البيانات

```
product.product (المنتج الرئيسي)
  ├─ barcode (الباركود الرئيسي)
  ├─ alternative_barcode_ids (الباركودات البديلة)
  │   └─ product.barcode.alternative
  │       ├─ barcode (الباركود)
  │       ├─ uom_name (وحدة القياس)
  │       ├─ sap_uom_entry (رقم UoM في SAP)
  │       └─ last_sync (آخر مزامنة)
  └─ sap_product_name, sap_uom (بيانات SAP)
```

### API البحث

```python
# البحث بالباركود
product = env['product.barcode.alternative'].find_product_by_barcode('20493')

# أو
template = env['product.label.template'].browse(1)
result = template.get_sap_product_info('20493')
```

---

## ✅ الخلاصة

- ✅ **البحث**: يدعم الباركود الرئيسي والفرعي
- ✅ **السرعة**: Cache محلي لمدة ساعة
- ✅ **التحديث**: مزامنة دورية تلقائية
- ✅ **المرونة**: إضافة يدوية للباركودات
- ✅ **التوافق**: يعمل مع SAP B1 10

---

## 🆘 الدعم

للحصول على الدعم:
1. راجع الـ logs: `odoo.log`
2. تحقق من الاتصال بـ SAP
3. تأكد من صلاحيات المستخدم

---

**تم إنشاؤه بواسطة**: Lugal AI  
**التاريخ**: 2025-12-04  
**الإصدار**: 1.0

