# إعداد ULTRAMSG - دليل سريع

## 1. إنشاء حساب ULTRAMSG

1. اذهب إلى https://ultramsg.com
2. سجل حساب جديد
3. اربط رقم واتساب
4. احصل على:
   - Instance ID
   - API Token

## 2. تفعيل في Odoo

1. **WhatsApp Integration > Configuration**
2. انقر **New**
3. أدخل:
   - Instance ID: `instance12345`
   - API Token: `your_token`
   - Phone Prefix: `964`
4. احفظ

## 3. اختبار

1. افتح Configuration
2. انقر **Test Connection**
3. تحقق من استلام الرسالة

## 4. الاستخدام

```python
# في أي مودل
config = self.env['ultramsg.config'].search([('active', '=', True)], limit=1)
result = config.send_message(
    phone='07800114976',
    message_type='text',
    message_body='مرحباً!'
)
```

## تنسيق الأرقام

- `07800114976` → `9647800114976` ✅
- `7800114976` → `9647800114976` ✅
- `9647800114976` → `9647800114976` ✅

تم! 🎉





