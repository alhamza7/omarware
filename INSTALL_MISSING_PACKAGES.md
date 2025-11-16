# تعليمات تثبيت المكتبات المفقودة على الخادم

## المشاكل المكتشفة في السجل:

1. **مكتبة passlib مفقودة**: `ModuleNotFoundError: No module named 'passlib'`
2. **مكتبة pdfminer مفقودة**: تحذير في السجل
3. **ملف XML تالف**: تم إصلاحه محلياً - يجب رفعه للخادم

## خطوات الإصلاح على الخادم:

### 1. الاتصال بالخادم:
```bash
ssh lugalai@192.168.116.211
# كلمة المرور: Mohammed11
```

### 2. الانتقال إلى مجلد المشروع:
```bash
cd ~/Lugal-ai
```

### 3. تفعيل البيئة الافتراضية (إن وجدت):
```bash
# إذا كان هناك virtual environment
source venv/bin/activate
# أو
python3 -m venv venv
source venv/bin/activate
```

### 4. تثبيت المكتبات المفقودة:

#### أ. تثبيت passlib:
```bash
pip3 install passlib==1.7.4
```

#### ب. تثبيت pdfminer (اختياري - للفهرسة):
```bash
pip3 install pdfminer.six
```

#### ج. تثبيت جميع المكتبات من requirements.txt:
```bash
pip3 install -r requirements.txt
```

### 5. رفع الملف المُصلح إلى الخادم:

من الجهاز المحلي (Windows):
```bash
# رفع الملف المُصلح
scp addons/sap_integration/views/sap_menu_structure.xml lugalai@192.168.116.211:~/Lugal-ai/addons/sap_integration/views/
```

### 6. إعادة تشغيل Odoo:

بعد تثبيت المكتبات وإصلاح الملفات:
```bash
# إيقاف Odoo (إذا كان يعمل كخدمة)
sudo systemctl stop odoo
# أو إيقاف العملية يدوياً
pkill -f odoo-bin

# إعادة التشغيل
cd ~/Lugal-ai
python3 odoo-bin -c odoo.conf -d lugal --http-port=8069
```

### 7. التحقق من السجل:

```bash
tail -f ~/Lugal-ai/odoo.log
```

## ملاحظات:

- تأكد من استخدام Python 3.12 أو الإصدار المطلوب
- إذا كان هناك virtual environment، استخدمه دائماً
- تحقق من أن جميع المسارات صحيحة
- بعد الإصلاح، يجب أن يبدأ Odoo بدون أخطاء حرجة

