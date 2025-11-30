# فاتورة NBS - دليل الاستخدام

## نظرة عامة

تم إنشاء تقرير فاتورة NBS بتصميم مطابق 100% للتصميم الأصلي في HTML. التقرير يحتوي على:

- **هيدر**: شعار NBS والاسم بالعربي والإنجليزي
- **معلومات الفاتورة**: رقم الفاتورة، التاريخ، الوقت، نوع الفاتورة
- **معلومات العميل**: الاسم، العنوان، الهاتف
- **جدول المنتجات**: مع الكمية، السعر، الخصم، المجموع، المنشأ
- **الإجماليات**: المبلغ الإجمالي بالدولار والدينار العراقي
- **الملاحظات**: ملاحظات الطلب و Reference للـ Sale Order
- **فوتر**: شعار الشركة

## المتطلبات

### 1. الصور المطلوبة

يجب أن تكون الصور التالية موجودة في:
```
addons/pos_perfume_custom/static/src/img/
```

- **nbs_header.png**: صورة الهيدر (777×160px)
- **nbs_footer.png**: صورة الفوتر (778×46px)

✅ تم نسخ الصور تلقائياً من مجلد HTML

### 2. الحقول المطلوبة في النموذج

التقرير يستخدم الحقول التالية من `pos.perfume.order`:

```python
- name               # رقم الفاتورة
- date               # تاريخ ووقت الفاتورة
- partner_id         # معلومات العميل
- invoice_type       # نوع الفاتورة (1-8)
- exchange_rate      # سعر الصرف للدينار
- amount_total       # المجموع بالدولار
- amount_discount    # الخصم الكلي
- note               # الملاحظات
- order_line_ids     # سطور الطلب
- sale_order_id      # مرجع Sale Order
```

### 3. الحقول المطلوبة في سطور الطلب

```python
- custom_product_name    # اسم المنتج المخصص
- product_id.name        # اسم المنتج (احتياطي)
- quantity               # الكمية
- product_uom_id.name    # وحدة القياس
- unit_price             # سعر الوحدة
- discount_percent       # نسبة الخصم
- line_total             # المجموع الكلي للسطر
- product_id.country_id  # بلد المنشأ
```

## كيفية الاستخدام

### 1. تحديث الوحدة

```bash
cd L:\Lugal-ai
venv\Scripts\python.exe odoo-bin -c odoo.conf -d lugal --http-port=8070 -u pos_perfume_custom
```

### 2. طباعة الفاتورة

من داخل Odoo:

1. افتح **POS → Perfume Orders**
2. اختر طلب معين
3. اضغط على **Print**
4. اختر **"فاتورة NBS - طلب العطور"**

### 3. عرض الفاتورة

يمكنك عرض الفاتورة بصيغة:
- **PDF**: للطباعة والأرشفة
- **HTML**: للعرض السريع في المتصفح

## التخصيصات المتاحة

### 1. تغيير الألوان

في ملف `pos_perfume_order_report_nbs.xml`:

```xml
<!-- Yellow Header Bar -->
.yellow-header-bar {
    background-color: #fcefb4;  /* اللون الأصفر */
    border: 1px solid #0080ff;  /* البوردر الأزرق */
}
```

### 2. تغيير الخطوط

```xml
font-family: 'MCS Taybah S_U normal.', 'Arial', 'Tahoma', sans-serif;
```

### 3. تغيير أبعاد الصفحة

في `pos_perfume_report_action.xml`:

```xml
<field name="margin_top">10</field>
<field name="margin_bottom">10</field>
<field name="margin_left">7</field>
<field name="margin_right">7</field>
```

## أنواع الفواتير المدعومة

```
1 = زبون محل
2 = شركات توصيل
3 = نقليات
4 = ديلفري
5 = NBS
6 = شورجة
7 = NA
8 = مكاتب الشورجة
```

نوع الفاتورة يظهر في:
- أعلى جدول معلومات الفاتورة
- أسفل جدول الإجماليات

## سعر الصرف

يتم استخدام `exchange_rate` من الطلب لتحويل المبالغ من الدولار إلى الدينار العراقي:

```python
amount_iqd = amount_usd * exchange_rate
```

القيمة الافتراضية: **1300 IQD/USD**

## التنسيق الرقمي

### الأرقام بالدولار
```python
${:,.2f}  # مثال: $216.50
```

### الأرقام بالدينار
```python
{:,.0f}  # مثال: 281,450
```

## استكشاف الأخطاء

### الصور لا تظهر

**الحل:**
1. تأكد من وجود الصور في المسار الصحيح
2. تحقق من صلاحيات القراءة للملفات
3. امسح الكاش وأعد تحميل الصفحة
4. تأكد من تحديث الوحدة

```bash
venv\Scripts\python.exe odoo-bin -c odoo.conf -d lugal --http-port=8070 -u pos_perfume_custom
```

### الخطوط غير صحيحة

**الحل:**
تأكد من تثبيت الخط العربي على السيرفر أو استخدم بديل:

```css
font-family: 'Arial', 'Tahoma', sans-serif;
```

### معلومات العميل ناقصة

**الحل:**
تأكد من استكمال بيانات العميل في:
- الاسم
- العنوان (street)
- الهاتف (phone/mobile)
- رقم العميل (ref)

### نوع الفاتورة فارغ

**الحل:**
تأكد من اختيار `invoice_type` عند إنشاء الطلب. إذا لم يتم اختياره، لن يظهر في الفاتورة.

## التقارير المتاحة

يوجد الآن **3 تقارير** مختلفة:

1. **التقرير الأساسي** - `action_report_pos_perfume_order`
2. **التقرير الذهبي** - `action_report_pos_perfume_order_gold`
3. **تقرير NBS** - `action_report_pos_perfume_order_nbs` ⭐ جديد

يمكنك الوصول إلى جميع التقارير من زر **Print** في الطلب.

## الملفات ذات الصلة

```
addons/pos_perfume_custom/
├── reports/
│   ├── pos_perfume_order_report_nbs.xml    # التصميم الرئيسي
│   ├── pos_perfume_report_action.xml       # تعريف التقرير
│   └── ...
├── static/src/img/
│   ├── nbs_header.png                       # صورة الهيدر
│   ├── nbs_footer.png                       # صورة الفوتر
│   └── README.md                            # دليل الصور
└── __manifest__.py                          # ملف التكوين
```

## التكامل مع SAP

التقرير متوافق مع حقول SAP:
- `invoice_type` → `U_InvType` في SAP
- يعرض نفس المعلومات المرسلة إلى SAP
- يدعم جميع أنواع الفواتير

## الدعم الفني

للمساعدة أو الإبلاغ عن مشاكل:
- راجع ملفات LOG في Odoo
- تحقق من الـ Browser Console للأخطاء
- تأكد من تحديث الوحدة بعد أي تعديلات

---

**تم التطوير بواسطة**: Lugal-AI  
**الإصدار**: 19.0.1.0.0  
**التاريخ**: November 2025



