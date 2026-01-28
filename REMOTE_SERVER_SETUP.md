# إعداد السيرفر البعيد بعد Pull

## بعد سحب التغييرات من GitHub

### الخطوة 1: تطبيق حل مشكلة AssetsLoadingError

إذا كنت تواجه مشكلة `AssetsLoadingError` مع `web_tour.interactive.min.js`:

#### الطريقة السريعة (موصى به):
```bash
cd ~/Lugal-ai  # أو مسار المشروع على السيرفر
./fix_assets_loading_error.sh
```

#### أو استخدام Python:
```bash
python3 fix_assets_error.py
# أو
venv/bin/python fix_assets_error.py
```

#### أو خطوات يدوية:
```bash
# 1. إيقاف Odoo
pkill -f "odoo-bin.*lugal"

# 2. مسح الكاش من قاعدة البيانات
python3 clear_cache_from_db.py

# 3. تحديث وحدة web_tour
python3 odoo-bin -c odoo.conf -d lugal -u web_tour --stop-after-init

# 4. إعادة بناء Assets
python3 odoo-bin -c odoo.conf -d lugal -u web --stop-after-init

# 5. إعادة تشغيل Odoo
python3 odoo-bin -c odoo.conf -d lugal --http-port=8069
```

### الخطوة 2: التحقق من الملفات الجديدة

تأكد من أن الملفات التالية موجودة وقابلة للتنفيذ:

```bash
# جعل السكريبتات قابلة للتنفيذ
chmod +x fix_assets_loading_error.sh
chmod +x fix_assets_error.py
chmod +x setup_github_auth.sh
chmod +x setup_github_auth.py
```

### الخطوة 3: التحقق من التحديثات

```bash
# عرض آخر commits
git log --oneline -5

# التحقق من حالة Git
git status
```

### الخطوة 4: إعادة تشغيل Odoo (إذا كان يعمل)

```bash
# إيقاف Odoo
pkill -f "odoo-bin.*lugal"

# انتظار قليل
sleep 3

# إعادة التشغيل
cd ~/Lugal-ai
python3 odoo-bin -c odoo.conf -d lugal --http-port=8069

# أو في الخلفية:
nohup python3 odoo-bin -c odoo.conf -d lugal --http-port=8069 > odoo.log 2>&1 &
```

### الخطوة 5: مسح كاش المتصفح

بعد إعادة تشغيل Odoo:
1. افتح المتصفح
2. اضغط `Ctrl+Shift+Delete` لمسح الكاش
3. أو اضغط `Ctrl+F5` لإعادة تحميل الصفحة بدون كاش

## الملفات الجديدة المتاحة

### سكريبتات حل مشكلة Assets:
- `fix_assets_loading_error.sh` - سكريبت شامل لحل مشكلة Assets
- `fix_assets_error.py` - سكريبت Python لحل المشكلة
- `clear_cache_from_db.py` - محدث لمسح جميع Assets

### سكريبتات GitHub:
- `setup_github_auth.sh` - إعداد المصادقة مع GitHub (Bash)
- `setup_github_auth.py` - إعداد المصادقة مع GitHub (Python)
- `quick_push.sh` - رفع سريع للتغييرات

### التوثيق:
- `FIX_ASSETS_LOADING_ERROR.md` - دليل حل مشكلة Assets
- `GITHUB_PUSH_GUIDE.md` - دليل رفع التغييرات إلى GitHub

## ملاحظات مهمة

1. **Assets سيتم إعادة بنائها تلقائياً** عند أول طلب بعد الحذف
2. **قد يستغرق إعادة بناء Assets بعض الوقت** في المرة الأولى
3. **تأكد من أن وحدة `web_tour` مثبتة** ومحدثة
4. **إذا استمرت المشكلة**، جرب إعادة تثبيت وحدة `web_tour`:
   ```bash
   python3 odoo-bin -c odoo.conf -d lugal -i web_tour --stop-after-init
   ```

## التحقق من نجاح الحل

بعد تطبيق الحل:
1. افتح Odoo في المتصفح
2. افتح Developer Tools (F12)
3. تحقق من Console - يجب ألا يكون هناك خطأ `AssetsLoadingError`
4. تحقق من Network tab - يجب أن يتم تحميل `web_tour.interactive.min.js` بنجاح
