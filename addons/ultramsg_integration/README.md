# ULTRAMSG WhatsApp Integration

مودل مستقل لإرسال رسائل واتساب عبر ULTRAMSG API.

## الميزات

✅ إرسال رسائل نصية  
✅ إرسال مستندات (PDF)  
✅ إرسال صور  
✅ تتبع حالة الرسائل  
✅ لوج كامل للرسائل  
✅ تحويل أرقام الهاتف تلقائياً  
✅ دعم كامل للعربية  

## التثبيت

1. انسخ المودل إلى مجلد `addons`
2. قم بتثبيت المودل من Odoo
3. اذهب إلى **WhatsApp Integration > Configuration**
4. أدخل Instance ID و API Token من حساب ULTRAMSG

## الاستخدام

### إرسال رسالة برمجياً:

```python
# Get config
config = self.env['ultramsg.config'].search([('active', '=', True)], limit=1)

# Send document
result = config.send_message(
    phone='07800114976',
    message_type='document',
    message_body='رسالتك هنا',
    document_url='https://example.com/file.pdf',
    document_name='invoice.pdf'
)

# Send text
result = config.send_message(
    phone='07800114976',
    message_type='text',
    message_body='مرحباً!'
)
```

### إنشاء وتتبع رسالة:

```python
# Create message
message = self.env['ultramsg.message'].create({
    'phone': '07800114976',
    'message_type': 'document',
    'message_body': 'رسالتك',
    'document_url': 'https://example.com/file.pdf',
    'res_model': 'sale.order',  # اختياري - ربط مع سجل آخر
    'res_id': order_id,
})

# Send message
message.action_send_message()
```

## الربط مع مودلات أخرى

يمكن ربط الرسائل مع أي مودل باستخدام:
- `res_model` - اسم المودل
- `res_id` - ID السجل

مثال: ربط مع `sale.order`, `pos.perfume.order`, `account.move`, إلخ.

## تنسيق الأرقام

الأرقام يتم تحويلها تلقائياً:
- **الإدخال:** `07800114976`
- **الإخراج:** `9647800114976`

## القوائم

- **WhatsApp Integration** - القائمة الرئيسية
  - **Messages Log** - جميع الرسائل المرسلة
  - **Configuration** - إعدادات ULTRAMSG

## API Reference

### ultramsg.config

**Methods:**
- `format_phone_number(phone)` - تحويل رقم الهاتف
- `send_message(...)` - إرسال رسالة
- `action_test_connection()` - اختبار الاتصال

### ultramsg.message

**Methods:**
- `action_send_message()` - إرسال الرسالة
- `action_retry_send()` - إعادة إرسال الرسائل الفاشلة

## المتطلبات

- Python package: `requests`

```bash
pip install requests
```

## الدعم

للدعم أو الأسئلة، راجع [ULTRAMSG Documentation](https://docs.ultramsg.com/)



