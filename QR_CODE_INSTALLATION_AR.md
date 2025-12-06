# دليل تثبيت QR Code للملصقات

## المشكلة

عند محاولة طباعة QR codes على الملصقات، يظهر الخطأ التالي:

```
ModuleNotFoundError: No module named 'rlPyCairo'
reportlab.graphics.utils.RenderPMError: cannot import desired renderPM backend rlPyCairo
```

## السبب

مكتبة `reportlab` التي يستخدمها Odoo لتوليد QR codes تحتاج إلى مكتبات إضافية (`pycairo` و `pillow`) لتوليد صور PNG.

## الحل

### الطريقة الأولى: استخدام السكريبت التلقائي (موصى به)

1. انسخ ملف `install_qr_dependencies.sh` إلى السيرفر:
   ```bash
   scp install_qr_dependencies.sh lugalai@192.168.116.211:/home/lugalai/
   ```

2. اتصل بالسيرفر عبر SSH:
   ```bash
   ssh lugalai@192.168.116.211
   ```

3. شغل السكريبت:
   ```bash
   cd /home/lugalai
   chmod +x install_qr_dependencies.sh
   bash install_qr_dependencies.sh
   ```

4. أعد تشغيل Odoo:
   ```bash
   sudo systemctl restart odoo
   ```
   أو:
   ```bash
   ps aux | grep odoo-bin
   kill -9 <PID>
   cd /home/lugalai/Lugal-ai
   source venv/bin/activate
   python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069
   ```

---

### الطريقة الثانية: التثبيت اليدوي

إذا لم يعمل السكريبت، اتبع هذه الخطوات:

#### 1. تثبيت مكتبات النظام

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    libjpeg-dev \
    libfreetype6-dev \
    zlib1g-dev \
    libcairo2-dev \
    pkg-config \
    build-essential
```

#### 2. تفعيل virtual environment

```bash
cd /home/lugalai/Lugal-ai
source venv/bin/activate
```

#### 3. تثبيت مكتبات Python

```bash
pip install --upgrade pip
pip install --upgrade pillow pycairo
```

#### 4. اختبار التثبيت

```bash
python3 -c "from reportlab.graphics.barcode import createBarcodeDrawing; barcode = createBarcodeDrawing('QR', value='TEST', format='png', width=300, height=300); print('✓ QR Code works!')"
```

إذا ظهرت الرسالة `✓ QR Code works!` فالتثبيت ناجح.

#### 5. إعادة تشغيل Odoo

```bash
sudo systemctl restart odoo
```

---

## التحقق من نجاح التثبيت

1. افتح Odoo في المتصفح
2. اذهب إلى **SAP Label Printer** أو **Print Label Wizard**
3. امسح باركود منتج
4. يجب أن يظهر QR code على الملصق بدون أخطاء

---

## استكشاف الأخطاء

### إذا استمر الخطأ بعد التثبيت:

1. **تحقق من أن virtual environment مفعل:**
   ```bash
   which python
   # يجب أن يكون: /home/lugalai/Lugal-ai/venv/bin/python
   ```

2. **تحقق من تثبيت المكتبات:**
   ```bash
   pip list | grep -i cairo
   pip list | grep -i pillow
   ```

3. **جرب إعادة تثبيت reportlab:**
   ```bash
   pip uninstall reportlab
   pip install reportlab
   ```

4. **تحقق من logs الخطأ:**
   ```bash
   tail -f /var/log/odoo/odoo.log
   # أو
   journalctl -u odoo -f
   ```

---

## ملاحظات مهمة

- ✅ الكود في `label_templates_simple.xml` صحيح ولا يحتاج أي تعديل
- ✅ المشكلة فقط في المكتبات المفقودة على السيرفر
- ✅ بعد التثبيت، QR codes ستعمل تلقائياً
- ⚠️ يجب إعادة تشغيل Odoo بعد التثبيت

---

## معلومات إضافية

### محتوى QR Code:
```
<product_code>|<barcode>
مثال: R00072|20493
```

### المكتبات المطلوبة:
- `pycairo`: لرسم الرسومات (Cairo graphics)
- `pillow`: لمعالجة الصور
- System libs: `libcairo2-dev`, `libjpeg-dev`, إلخ

---

## الدعم

إذا واجهت أي مشاكل، تحقق من:
1. أن المكتبات مثبتة بشكل صحيح
2. أن virtual environment مفعل عند تشغيل Odoo
3. أن Odoo تم إعادة تشغيله بعد التثبيت

---

**تاريخ الإنشاء:** 2025-12-06  
**الإصدار:** 1.0

