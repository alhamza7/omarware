# 🖨️ دمج زر الطباعة مع Invoice Designer

## تم التحديث! ✅

الآن زر **Print** 🖨️ في واجهة POS Perfume يستخدم **Invoice Designer** لطباعة الفواتير المخصصة!

---

## كيف يعمل؟

### 1. عند الضغط على زر Print

```javascript
// في واجهة POS
زر Print → يحفظ الطلب أولاً → يستدعي action_print_with_designer
```

### 2. في الخلفية (Backend)

```python
# في pos_perfume_order.py
action_print_with_designer():
  1. يبحث عن القالب المحدد للطلب (invoice_template_id)
  2. إذا لم يجد، يبحث عن القالب الافتراضي (is_default=True)
  3. إذا لم يجد، يأخذ أول قالب متاح
  4. يولد PDF باستخدام القالب
  5. يفتح PDF في نافذة جديدة
```

### 3. النتيجة

- ✅ PDF جاهز مع التصميم المحدد
- ✅ يفتح في نافذة جديدة
- ✅ جاهز للطباعة

---

## التخصيص

### اختيار قالب محدد لكل طلب

```
1. في نموذج POS Perfume Order
2. حقل "Invoice Template"
3. اختر القالب المطلوب
4. احفظ
5. الآن زر Print سيستخدم هذا القالب!
```

### تعيين قالب افتراضي

```
1. Invoice Designer → Templates
2. افتح القالب المطلوب
3. ضع علامة ✓ على "Default Template"
4. احفظ
5. سيُستخدم تلقائياً لجميع الطلبات!
```

---

## الكود المُحدث

### JavaScript (pos_perfume_screen.js)

```javascript
async printOrder() {
    // حفظ الطلب أولاً
    if (!this.state.currentOrder.order_id) {
        await this.saveOrder('draft');
    }
    
    // طباعة باستخدام Invoice Designer
    const result = await this.orm.call(
        'pos.perfume.order',
        'action_print_with_designer',
        [[orderId]]
    );
    
    // فتح PDF
    if (result.type === 'ir.actions.act_url') {
        window.open(result.url, '_blank');
    }
}
```

### Python (pos_perfume_order.py)

```python
def action_print_with_designer(self):
    # البحث عن القالب
    template = self.invoice_template_id
    if not template:
        template = self.env['invoice.template.designer'].search([
            ('template_type', '=', 'pos_receipt'),
            ('is_default', '=', True),
        ], limit=1)
    
    # توليد PDF
    pdf_data = template.generate_invoice_pdf(self.id, model_name='pos.perfume.order')
    
    # إرجاع URL
    return {
        'type': 'ir.actions.act_url',
        'url': f'/web/content/.../{self.name}.pdf',
        'target': 'new',
    }
```

---

## التجربة

### الطريقة 1: من واجهة POS

```
1. افتح POS Perfume
2. أدخل منتجات
3. احفظ الطلب
4. اضغط 🖨️ Print
5. ستفتح نافذة PDF جديدة!
```

### الطريقة 2: من نموذج الطلب

```
1. POS Perfume → Orders
2. افتح طلب
3. اضغط "طباعة مع المصمم"
4. ستفتح نافذة PDF!
```

---

## المميزات

✅ **تلقائي**: يستخدم القالب المحدد أو الافتراضي
✅ **مرن**: يمكن تغيير القالب لكل طلب
✅ **سريع**: PDF فوري
✅ **احترافي**: تصميم مخصص بالكامل
✅ **سهل**: زر واحد فقط!

---

## استكشاف الأخطاء

### ❌ خطأ: "No invoice template found"

**الحل:**
```
1. انتقل إلى: Invoice Designer → Templates
2. تأكد من وجود قالب واحد على الأقل
3. أو أنشئ قالب جديد
```

### ❌ خطأ: "Failed to generate PDF"

**الحل:**
```
1. تحقق من أن القالب يحتوي على عناصر
2. تحقق من الحقول الديناميكية
3. جرّب قالب آخر
```

### ❌ PDF فارغ

**الحل:**
```
1. تحقق من أن الطلب يحتوي على سطور
2. تحقق من أن القالب يحتوي على جدول المنتجات
3. راجع إعدادات القالب
```

---

## ملاحظات مهمة

⚠️ **يجب حفظ الطلب أولاً** قبل الطباعة
⚠️ **يحتاج قالب واحد على الأقل** في النظام
⚠️ **امسح الـ cache** إذا لم تظهر التغييرات (Ctrl+Shift+R)

---

## القوالب المتاحة

عند التثبيت، تحصل على قالبين جاهزين:

### 1. فاتورة كلاسيكية (افتراضي)
- تصميم مهني
- جميع التفاصيل
- جاهز للاستخدام

### 2. فاتورة عصرية
- تدرجات لونية
- QR Code
- تصميم حديث

---

<div align="center">

# ✅ جاهز للاستخدام!

**اضغط Print واحصل على فاتورة احترافية!**

</div>


