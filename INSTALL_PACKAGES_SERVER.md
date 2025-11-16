# تثبيت المكتبات المفقودة على الخادم

## المشكلة:
النظام يستخدم Python 3.12 مع بيئة محمية (externally-managed-environment)

## الحلول:

### الحل 1: استخدام --break-system-packages (الأسرع)

```bash
cd ~/Lugal-ai

# تثبيت passlib
pip3 install --break-system-packages passlib==1.7.4

# تثبيت pdfminer.six (اختياري)
pip3 install --break-system-packages pdfminer.six
```

### الحل 2: استخدام apt (إذا كانت المكتبات متوفرة)

```bash
sudo apt update
sudo apt install python3-passlib python3-pdfminer
```

### الحل 3: إنشاء virtual environment (الأفضل)

```bash
cd ~/Lugal-ai

# إنشاء virtual environment
python3 -m venv venv

# تفعيل virtual environment
source venv/bin/activate

# تثبيت المكتبات
pip install passlib==1.7.4
pip install pdfminer.six

# تثبيت جميع المكتبات من requirements.txt
pip install -r requirements.txt

# إلغاء تفعيل virtual environment
deactivate
```

**ملاحظة مهمة**: إذا استخدمت virtual environment، يجب تشغيل Odoo من داخل virtual environment:

```bash
cd ~/Lugal-ai
source venv/bin/activate
python3 odoo-bin -c odoo.conf -d lugal --http-port=8069
```

### الحل 4: استخدام السكريبت المحدث

```bash
cd ~/Lugal-ai
git pull origin main
chmod +x fix_server.sh
./fix_server.sh
```

## بعد التثبيت:

1. **التحقق من التثبيت:**
```bash
python3 -c "import passlib; print('passlib installed successfully')"
```

2. **إعادة تشغيل Odoo:**
```bash
# إيقاف Odoo الحالي
pkill -f odoo-bin

# إعادة التشغيل
cd ~/Lugal-ai
python3 odoo-bin -c odoo.conf -d lugal --http-port=8069
```

3. **مراقبة السجل:**
```bash
tail -f ~/Lugal-ai/odoo.log
```

## التوصية:

استخدم **الحل 1** (--break-system-packages) إذا كنت تريد حل سريع، أو **الحل 3** (virtual environment) للحل الأفضل والأكثر أماناً.

