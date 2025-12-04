# إصلاح مشكلة العناوين والملاحظات

## المشكلة
1. الملاحظات لا تظهر في المصمم المرئي
2. العناوين ما زالت تظهر (هاتف:، موبايل:، نوع الفاتورة:)

## الحل

### 1. تحديث القيم الافتراضية في قاعدة البيانات

افتح Odoo Shell وقم بتشغيل:

```python
templates = env['customer.label.template'].search([])
templates.write({
    'show_phone_label': False,
    'show_mobile_label': False,
    'show_invoice_type_label': False,
    'show_note_label': False,
})
print(f"تم تحديث {len(templates)} قالب")
```

### 2. التأكد من تفعيل الملاحظات

افتح القالب وتأكد من:
- تبويب "Display Options" → ✅ Show Notes مفعل
- تبويب "Visual Designer" → Note X Position و Note Y Position موجودة

### 3. تحديث الموديول

```bash
venv\Scripts\python.exe odoo-bin -c odoo.conf -d lugal --http-port=8070 -u product_label_designer --stop-after-init
```

## التحقق

1. افتح المصمم المرئي
2. يجب أن ترى عنصر "Notes" في قائمة العناصر
3. عند الطباعة، يجب أن تظهر القيم بدون عناوين:
   - `123456789` (بدون "هاتف:")
   - `987654321` (بدون "موبايل:")
   - `زبون محل` (بدون "نوع الفاتورة:")




