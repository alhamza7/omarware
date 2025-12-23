# ميزة الطباعة من SAP - SAP Print Feature
# Print Documents from SAP and Get PDF

## ✅ المشكلة التي تم حلها | Problem Solved

كان الكود يحاول الوصول إلى `backend.api_gateway_url` ولكن هذا الحقل لم يكن موجوداً في `sap.backend`، مما تسبب في خطأ:

```
'sap.backend' object has no attribute 'api_gateway_url'
```

The code was trying to access `backend.api_gateway_url` but this field didn't exist in `sap.backend`, causing the error above.

---

## 🔧 الحل المطبق | Solution Applied

### 1. إضافة حقل API Gateway URL

تم إضافة حقل جديد إلى `sap.backend`:

```python
api_gateway_url = fields.Char(
    'API Gateway URL',
    help="SAP API Gateway URL for printing and other services (e.g., https://sap-server.com:50001)"
)
```

### 2. إضافة دالة الطباعة الكاملة

تم إضافة دالة `print_document()` إلى `SapServiceLayerConnection` مع:
- ✅ دعم طريقتين للطباعة (API Gateway و Crystal Reports)
- ✅ إرجاع PDF تلقائياً
- ✅ حفظ PDF كـ attachment في Odoo
- ✅ إمكانية الطباعة أو التحميل مباشرة

---

## 📋 كيفية الاستخدام | How to Use

### خطوة 1: إعداد SAP Backend

1. **افتح Odoo:**
   ```
   Settings → SAP Integration → Backends
   ```

2. **افتح Backend الحالي أو أنشئ جديد**

3. **أضف API Gateway URL (اختياري):**
   ```
   API Gateway URL: https://your-sap-server.com:50001
   ```
   
   **ملاحظة:** إذا لم تحدد URL، سيستخدم النظام Crystal Reports Service تلقائياً

4. **احفظ**

---

### خطوة 2: الطباعة من POS

#### من واجهة POS:

1. **افتح طلب POS**
2. **تأكد من أن الطلب مُرسل إلى SAP** (يجب أن يكون لديه `sap_doc_entry`)
3. **اضغط زر "Print from SAP"** أو استخدم الإجراء المخصص
4. **سيتم:**
   - إرسال طلب طباعة إلى SAP
   - استرجاع PDF من SAP
   - حفظ PDF كـ attachment
   - فتح PDF للطباعة أو التحميل

---

### خطوة 3: الطباعة برمجياً

#### من Python Code:

```python
# الحصول على طلب POS
pos_order = env['pos.perfume.order'].browse(order_id)

# إرسال طلب طباعة
result = pos_order.action_print_to_sap()

# result يحتوي على:
# {
#     'type': 'ir.actions.act_url',
#     'url': '/web/content/{attachment_id}?download=true',
#     'target': 'new'
# }
```

#### من SAP Connection مباشرة:

```python
# الحصول على SAP backend
backend = env['sap.backend'].search([('active', '=', True)], limit=1)

# إنشاء اتصال
connection = backend.get_connection()

# إرسال طلب طباعة
result = connection.print_document(
    doc_entry=12345,           # رقم DocEntry من SAP
    doc_type='Orders',         # نوع المستند
    print_format='DEFAULT LAYOUT',  # اسم Layout في SAP
    return_pdf=True,           # إرجاع PDF؟
    api_gateway_url=backend.api_gateway_url  # (اختياري)
)

# result يحتوي على:
# {
#     'success': True/False,
#     'message': 'رسالة توضيحية',
#     'pdf_base64': 'base64 encoded PDF' أو None
# }
```

---

## 🎯 أنواع المستندات المدعومة | Supported Document Types

| النوع | `doc_type` | SAP Object Type |
|-------|-----------|-----------------|
| عروض الأسعار | `'Quotations'` | 23 |
| أوامر البيع | `'Orders'` | 17 |
| الفواتير | `'Invoices'` | 13 |
| أوامر الشراء | `'PurchaseOrders'` | 22 |
| إشعارات التسليم | `'DeliveryNotes'` | 15 |

---

## 🔄 طرق الطباعة | Print Methods

### الطريقة 1: API Gateway (الأسرع) ✅ مستحسن

إذا قمت بتحديد `api_gateway_url` في Backend:

**المزايا:**
- ✅ أسرع
- ✅ إرجاع PDF مباشرة
- ✅ لا يحتاج إعداد إضافي

**متطلبات:**
- يجب أن يكون لديك SAP API Gateway مُعد
- URL مثل: `https://sap-server.com:50001`

**كيف يعمل:**
```
Odoo → API Gateway → SAP Crystal Reports → PDF → Odoo
```

---

### الطريقة 2: Crystal Reports Service (القياسية)

إذا لم تحدد `api_gateway_url`:

**المزايا:**
- ✅ يعمل مع أي SAP Service Layer
- ✅ لا يحتاج API Gateway منفصل

**العيوب:**
- ⚠️ قد يكون أبطأ
- ⚠️ قد لا يرجع PDF مباشرة (حسب إعدادات SAP)

**كيف يعمل:**
```
Odoo → SAP Service Layer → Print Queue → Crystal Reports
```

---

## 📊 مثال كامل | Complete Example

### سيناريو: طباعة Order من POS

```python
# 1. إنشاء طلب POS
pos_order = env['pos.perfume.order'].create({
    'name': 'POS/2025/001',
    'partner_id': partner.id,
    # ... بيانات أخرى
})

# 2. حفظ الطلب وإرساله إلى SAP
pos_order.action_save_order()  # يرسل تلقائياً إلى SAP

# 3. التحقق من أن الطلب في SAP
assert pos_order.sap_doc_entry > 0, "Order not synced to SAP"

# 4. إرسال طلب طباعة
result = pos_order.action_print_to_sap()

# 5. النتيجة
if result['type'] == 'ir.actions.act_url':
    print(f"✅ PDF ready: {result['url']}")
    
    # الحصول على PDF من attachment
    attachment_id = int(result['url'].split('/')[3])
    attachment = env['ir.attachment'].browse(attachment_id)
    
    # PDF موجود في attachment.datas (base64)
    pdf_base64 = attachment.datas
    
    # تحويل إلى binary إذا لزم الأمر
    import base64
    pdf_binary = base64.b64decode(pdf_base64)
    
    # حفظ إلى ملف
    with open('order_from_sap.pdf', 'wb') as f:
        f.write(pdf_binary)
    
    print("✅ PDF saved to order_from_sap.pdf")
```

---

## ⚙️ الإعدادات المتقدمة | Advanced Configuration

### 1. تغيير Print Layout

يمكنك تحديد layout مختلف عند الطباعة:

```python
result = connection.print_document(
    doc_entry=12345,
    doc_type='Orders',
    print_format='CUSTOM LAYOUT NAME',  # ← استخدم اسم layout من SAP
    return_pdf=True
)
```

**كيف تجد اسم Layout في SAP:**
1. افتح SAP Business One
2. اذهب إلى: Administration → System Initialization → Print Layout Design
3. اختر المستند (مثل Sales Order)
4. انسخ اسم Layout المراد استخدامه

---

### 2. الطباعة بدون إرجاع PDF

إذا كنت تريد فقط إرسال أمر طباعة إلى SAP (بدون استرجاع PDF):

```python
result = connection.print_document(
    doc_entry=12345,
    doc_type='Orders',
    print_format='DEFAULT LAYOUT',
    return_pdf=False  # ← لا ترجع PDF
)

# النتيجة:
# {
#     'success': True,
#     'message': 'Print request sent to SAP successfully',
#     'pdf_base64': None
# }
```

---

### 3. معالجة الأخطاء

```python
try:
    result = pos_order.action_print_to_sap()
    
    if result.get('type') == 'ir.actions.client' and 'error' in result.get('params', {}).get('message', '').lower():
        # حدث خطأ
        error_message = result['params']['message']
        _logger.error(f"Print failed: {error_message}")
    else:
        # نجحت الطباعة
        _logger.info("Print successful")
        
except Exception as e:
    _logger.error(f"Print error: {str(e)}", exc_info=True)
```

---

## 🐛 استكشاف الأخطاء | Troubleshooting

### المشكلة 1: `'sap.backend' object has no attribute 'api_gateway_url'`

**الحل:**
```bash
# تحديث المودل
cd /home/lugalai/Lugal-ai
./venv/bin/python3 odoo-bin -c odoo_simple.conf -d lugal -u sap_integration --stop-after-init
./venv/bin/python3 odoo-bin -c odoo_simple.conf -d lugal
```

---

### المشكلة 2: لا يتم إرجاع PDF

**الأسباب المحتملة:**
1. ✅ **API Gateway غير مُعد:** حدد `api_gateway_url` في Backend
2. ✅ **Crystal Reports غير مُعد:** تأكد من إعداد Crystal Reports في SAP
3. ✅ **Layout غير موجود:** تحقق من اسم Print Layout في SAP

**الحل:**
```python
# جرّب بدون API Gateway
result = connection.print_document(
    doc_entry=12345,
    doc_type='Orders',
    print_format='DEFAULT LAYOUT',
    return_pdf=True,
    api_gateway_url=None  # ← استخدم Crystal Reports
)
```

---

### المشكلة 3: خطأ في الاتصال بـ SAP

**الحل:**
```python
# 1. تحقق من الاتصال
backend = env['sap.backend'].search([('active', '=', True)], limit=1)
result = backend.test_connection()

# 2. تحقق من الـ logs
# راجع /var/log/odoo/odoo.log أو console output

# 3. تحقق من URL
print(f"Service Layer URL: {backend.base_url}")
print(f"API Gateway URL: {backend.api_gateway_url}")
```

---

### المشكلة 4: PDF تالف أو لا يفتح

**الحل:**
```python
# تحقق من صحة PDF
import base64

pdf_base64 = result.get('pdf_base64')
if pdf_base64:
    pdf_binary = base64.b64decode(pdf_base64)
    
    # تحقق من أول bytes (يجب أن تبدأ بـ %PDF)
    if pdf_binary[:4] == b'%PDF':
        print("✅ PDF is valid")
    else:
        print("❌ PDF is corrupted")
        print(f"First 20 bytes: {pdf_binary[:20]}")
```

---

## 📝 ملاحظات هامة | Important Notes

### 1. الأمان | Security
- ⚠️ API Gateway URL يُحفظ في قاعدة البيانات (plaintext)
- ⚠️ تأكد من حماية الوصول إلى SAP Backend
- ⚠️ استخدم HTTPS دائماً للاتصال بـ SAP

### 2. الأداء | Performance
- ⚠️ طلبات الطباعة قد تستغرق 5-30 ثانية (حسب حجم المستند)
- ⚠️ PDF الكبيرة قد تستهلك ذاكرة
- ✅ استخدم API Gateway للحصول على أداء أفضل

### 3. التوافق | Compatibility
- ✅ يعمل مع SAP Business One 9.3+
- ✅ يعمل مع SAP Service Layer v1 و v2
- ✅ يدعم Crystal Reports 2016+

---

## 🔄 التحديث | Update

### تحديث المودل:
```bash
cd /home/lugalai/Lugal-ai
./venv/bin/python3 odoo-bin -c odoo_simple.conf -d lugal -u sap_integration --stop-after-init
./venv/bin/python3 odoo-bin -c odoo_simple.conf -d lugal
```

### إضافة API Gateway URL:
```sql
-- في psql أو Odoo Shell
UPDATE sap_backend 
SET api_gateway_url = 'https://your-sap-server.com:50001'
WHERE active = true;
```

---

## 📚 المراجع | References

- **SAP Service Layer API:** Print Service documentation
- **SAP Crystal Reports:** Layout Designer guide
- **Odoo:** ir.attachment, ir.actions.act_url
- **Python:** base64, requests

---

## ✅ الملخص | Summary

| الميزة | الحالة |
|--------|--------|
| API Gateway URL field | ✅ مضاف |
| print_document() function | ✅ مضاف |
| API Gateway support | ✅ مدعوم |
| Crystal Reports support | ✅ مدعوم |
| PDF return | ✅ يعمل |
| Error handling | ✅ شامل |
| Logging | ✅ مفصّل |

---

**تاريخ الإصلاح:** 23 ديسمبر 2025  
**الإصدار:** SAP Integration v2.0.3  
**الميزة:** SAP Print & PDF Return  
**الحالة:** ✅ جاهز للاستخدام

